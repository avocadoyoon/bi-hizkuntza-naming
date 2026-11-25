# Picture naming task (Spanish). Run with PsychoPy (Coder: press Run).
#
# The participant sees one picture at a time and says what it is. 
# THE VOICE IS RECORDED; nothing is scored during the session. 
# The RA presses SPACE when the participant has finished, and the responses
# are coded afterwards from the recordings. 
#
# Nouns and verbs are shown in SEPARATE BLOCKS, never intermixed. The order
# within a block is shuffled fresh on every run. Which block comes first is
# counterbalanced across participants, from the digits in their code, and is
# the same for that person in both languages and at every time point.
#
# Nothing needs to know the order in advance: it is written to the log and
# into each .wav filename, and the responses are coded afterwards.
#
# A short "beep" sound is played AT picture onset and recorded with the response, so
# every .wav carries an acoustic mark of the moment the picture appeared.
# Voice onset measured from that beep is a real naming latency.
# It is not a "go" signal; the picture is the cue, and it is only 80 ms 
# so it cannot mask an early answer.
#
# ESC aborts; everything up to the last finished trial is kept.
import csv, os, random, re, sys, time, unicodedata
from psychopy import visual, core, event, gui
from PIL import Image

BUILD = '2026-11-22e  streams open all session; picture lookup ignores accents, extension, underscores'
print('naming task build: ' + BUILD)

LANGUAGE = 'Spanish'
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
FIX_DUR, PIC_HEIGHT = 0.5, 0.7          # fixation seconds; picture height
MAX_RECORD_S = 15                       
SAMPLE_RATE = 44100
ADVANCE = ['space', 'return', 'num_enter', 'right']

# Colours. Black screen.
BG, FG = 'black', 'white'

INSTRUCTIONS = ('Verás una imagen en la pantalla.\n\n'
                'Di en voz alta la palabra que corresponde a la imagen (una cosa o una acción), '
                'lo más rápido que puedas.\n\n'
                'Si no estás seguro/a, di la primera palabra que se te ocurra.\n\n\n'
                'Pulsa la barra espaciadora para empezar.')
BLOCK_BREAK = 'Pulsa la barra espaciadora para continuar.'
END_TEXT = 'Gracias.'

# Examples. This list can be edited/extended/shortened.
ERROR_TYPES = ['correct', 'semantic', 'phonological', 'mixed', 'unrelated',
               'neologism', 'circumlocution', 'perseveration', 'no response',
               'self-corrected', 'other']

import numpy as np
import sounddevice as sd
import soundfile as sf

# Kept short (80 ms) so it cannot mask an early response. These numbers
# can change based on your computer. They behave differently in Mac and 
# Windows.
BEEP_HZ, BEEP_MS, BEEP_LEVEL, BEEP_TAIL_MS = 1000, 80, 0.25, 60


def beep_sound():
    n = int(SAMPLE_RATE * BEEP_MS / 1000)
    t = np.arange(n) / SAMPLE_RATE
    x = np.sin(2 * np.pi * BEEP_HZ * t) * BEEP_LEVEL
    fade = max(1, int(SAMPLE_RATE * 0.005))
    x[:fade] *= np.linspace(0, 1, fade)
    x[-fade:] *= np.linspace(1, 0, fade)
    tail = np.zeros(int(SAMPLE_RATE * BEEP_TAIL_MS / 1000))
    return np.concatenate([x, tail]).astype('float32')


BEEP = beep_sound()


info = {'participant': ''}
if not gui.DlgFromDict(info, title='Naming task - ' + LANGUAGE).OK or not info['participant']:
    core.quit()
pid = info['participant']


def audio_settings():
    """Set your INPUT_DEVICE and OUTPUT_DEVICE by creating a txt file named AUDIO_SETTINGS.
    This folder is probably going to be included in another repositoy related to sound checks.
    """
    folder = HERE
    for _ in range(4):
        path = os.path.join(folder, 'AUDIO_SETTINGS.txt')
        if os.path.isfile(path):
            found = {}
            with open(path, encoding='utf-8') as f:
                for line in f:
                    key, _, value = line.split('#')[0].partition('=')
                    key, value = key.strip(), value.strip()
                    if key in ('INPUT_DEVICE', 'OUTPUT_DEVICE'):
                        found[key] = None if value.lower() in ('', 'none') else int(value)
            return found.get('INPUT_DEVICE'), path
        folder = os.path.dirname(folder)
    return None, None


def use_exclusive_input(device):
    """WASAPI exclusive mode, as the rest of the battery uses.
    """
    wasapi = getattr(sd, 'WasapiSettings', None)
    if wasapi is None:
        return 'shared'
    try:
        info_d = sd.query_devices(device if device is not None else sd.default.device[0], 'input')
        api = sd.query_hostapis(info_d['hostapi'])['name']
    except Exception:
        return 'shared'
    if 'WASAPI' not in api.upper():
        return 'shared'
    try:
        extra = wasapi(exclusive=True)
        sd.check_input_settings(device=device, channels=1, dtype='int16',
                                samplerate=SAMPLE_RATE, extra_settings=extra)
    except Exception:
        return 'shared'
    sd.default.extra_settings = (extra, None)
    return 'exclusive'


IN_DEVICE, SETTINGS_PATH = audio_settings()
if IN_DEVICE is not None:
    sd.default.device = (IN_DEVICE, None)
    print('microphone: device %s (from %s)' % (IN_DEVICE, SETTINGS_PATH))
else:
    print('No AUDIO_SETTINGS.txt found above this folder; using the default input.')
    print('On the lab computer the task should sit inside PROSIA_tasks_for_lab '
          'so it picks up the same device numbers as the other tasks.')
INPUT_MODE = use_exclusive_input(IN_DEVICE)
print('capture mode: %s' % INPUT_MODE)


_IMAGE_EXTS = ('.png', '.bmp', '.jpg', '.jpeg', '.tif', '.tiff')


def _strip_exts(name):
    """'x.png.png' -> 'x'.

    Windows hides file extensions by default, so renaming a file to
    "name.png" in Explorer produces "name.png.png". That happened at the lab
    while trying to fix the accents by hand, so repeated extensions are
    peeled off rather than left to cause a second failure.
    """
    while True:
        stem, ext = os.path.splitext(name)
        if ext.lower() in _IMAGE_EXTS and stem:
            name = stem
        else:
            return name


def _fold(s):
    """A filename reduced to something that survives being moved between
    machines: no extension, composed accents, lower case, and as a last
    resort no accents at all.

    An accented name can be stored as 'o' plus a combining accent or as a
    single character. macOS matches either when you look a file up; Windows
    does not. Zipping on one and unzipping on the other can change which is
    on disk, which is how two of the accented pictures went missing at the lab while
    the other 78 pictures were fine.
    """
    s = unicodedata.normalize('NFC', _strip_exts(s)).lower()
    # Runs of underscores and spaces are collapsed. The names use a double
    # underscore between the word and the picture file, and retyping one of
    # them by hand at the lab produced a single one - invisible on screen,
    # fatal to a string comparison. 
    s = re.sub(r'[_\s]+', '_', s).strip('_')
    bare = ''.join(c for c in unicodedata.normalize('NFD', s)
                   if not unicodedata.combining(c))
    return s, bare


_PIC_INDEX = {}


def find_picture(folder, stem):
    """The picture for `stem`, whatever its extension or accent encoding."""
    if folder not in _PIC_INDEX:
        exact, bare = {}, {}
        if os.path.isdir(folder):
            for name in sorted(os.listdir(folder)):
                if name.startswith('.'):
                    continue
                a, b = _fold(name)
                exact.setdefault(a, os.path.join(folder, name))
                bare.setdefault(b, os.path.join(folder, name))
        _PIC_INDEX[folder] = (exact, bare)
    exact, bare = _PIC_INDEX[folder]
    a, b = _fold(stem)
    return exact.get(a) or bare.get(b) or ''


items = []
with open(os.path.join(ROOT, 'selected_items_by_language.csv'), encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['language'] == LANGUAGE:
            sub = 'nouns' if r['category'] == 'noun' else 'verbs'
            stem = r['word'] + '__' + os.path.splitext(r['picture_file'])[0]
            folder = os.path.join(ROOT, 'pictures', LANGUAGE, sub)
            # Matched against what is actually in the folder, not built by
            # string concatenation: the extension differs between the working
            # copy (.bmp) and the copy sent to the lab (.png), and accented
            # names can come back from a zip in a different encoding.
            r['path'] = find_picture(folder, stem)
            r['stem'] = stem
            items.append(r)
assert len(items) == 40, 'expected 40 items, found %d' % len(items)
missing = [r for r in items if not r['path'] or not os.path.exists(r['path'])]
if missing:
    folder = os.path.join(ROOT, 'pictures', LANGUAGE,
                          'nouns' if missing[0]['category'] == 'noun' else 'verbs')
    have = sorted(os.listdir(folder))[:6] if os.path.isdir(folder) else []
    raise SystemExit(
        '%d picture(s) not found:\n  %s\n\n'
        'Looked in %s\nwhich contains, for example:\n  %s\n\n'
        'If the names look right but with odd accents, the files were '
        'renamed in transit - copy that folder across again without zipping '
        'it, or rename those few by hand.'
        % (len(missing), '\n  '.join(m['stem'] for m in missing), folder,
           '\n  '.join(have)))


def blocked_order(pid, items):
    """Nouns in one block, verbs in the other; shuffled fresh within each.
    THE ORDER WITHIN A BLOCK is a fresh shuffle every run, not seeded. The
    same participant is tested at three time points, and a seeded order would
    give them the identical sequence each visit, tying practice effects to
    one fixed order. Nothing needs to predict it: responses are coded
    afterwards from the recordings, and the exact order is written to the log
    and into every .wav filename.
    """
    nouns = [r for r in items if r['category'] == 'noun']
    verbs = [r for r in items if r['category'] != 'noun']
    random.shuffle(nouns)
    random.shuffle(verbs)
    digits = ''.join(c for c in pid if c.isdigit())
    nouns_first = (int(digits) % 2 == 1) if digits else (sum(map(ord, pid)) % 2 == 0)
    return (nouns + verbs) if nouns_first else (verbs + nouns)


items = blocked_order(pid, items)

cats = [r['category'] for r in items]
runs = [cats[0]] + [b for a, b in zip(cats, cats[1:]) if a != b]
if len(runs) != 2 or len(set(cats)) != 2:
    raise SystemExit(
        'Nouns and verbs must be in two separate blocks, but this order '
        'changes category %d time(s). This is a bug in blocked_order().'
        % (len(runs) - 1))
FIRST_BLOCK = runs[0]
BLOCK_OF = {}
for n, r in enumerate(items):
    BLOCK_OF[n] = 1 if r['category'] == FIRST_BLOCK else 2
print('Block order: %s first' % ('nouns' if FIRST_BLOCK == 'noun' else 'verbs'))

out_root = os.path.join(HERE, 'data', '%s_%s' % (LANGUAGE, pid))
if os.path.exists(out_root):
    raise SystemExit('%s already exists - use a different participant code.' % out_root)
os.makedirs(out_root)
base = os.path.join(out_root, '%s_%s' % (LANGUAGE, pid))
cols = ['participant', 'language', 'trial', 'block', 'block_type', 'trial_in_block',
        'category', 'target_word', 'picture_file', 'response_wav',
        'ra_keypress_s', 'recording_s', 'stop_reason', 'input_mode', 'build', 'timestamp']
out = open(base + '.csv', 'w', newline='', encoding='utf-8')
writer = csv.DictWriter(out, fieldnames=cols); writer.writeheader()

win = visual.Window(fullscr=True, color=BG, units='height')
fix = visual.TextStim(win, text='+', height=0.1, color=FG)
msg = visual.TextStim(win, text='', height=0.05, color=FG, wrapWidth=1.4)
clock = core.Clock()


def show_text(text, keys):
    msg.text = text; msg.draw(); win.flip()
    k = event.waitKeys(keyList=keys + ['escape'])[0]
    if k == 'escape': finish(aborted=True)


def finish(aborted=False):
    out.close()
    close_streams()
    try: sd.stop()
    except Exception: pass
    win.close()
    write_coding_sheet()
    if aborted: print('Aborted - partial data saved to', out_root)
    core.quit()


# ---------------------------------------------------------------------------
# The pip, played from a stream that is ALREADY RUNNING.
#
# First attempt used sd.play() on the flip. That has to OPEN an output stream
# at the moment it is called, and opening one takes long enough that the
# first pip of the session was lost every time - trial 1 silent, every later
# trial fine. Priming the device with silence beforehand did not help,
# because the cost is in opening the stream, not in waking the hardware.
#
# So one output stream is opened before the task and kept running until the
# end. It emits silence; firing the pip just moves a read position back to
# zero, which costs nothing and takes effect on the stream's next callback a
# few milliseconds later. No stream is opened, and nothing can be swallowed.
# ---------------------------------------------------------------------------
_pip_pos = [len(BEEP)]         
_out_stream = [None]
_in_stream = [None]
_rec_on = [False]
_rec_buf = []


def _feed_output(outdata, frames, time_info, status):
    pos = _pip_pos[0]
    n = max(0, min(frames, len(BEEP) - pos))
    if n:
        outdata[:n, 0] = BEEP[pos:pos + n]
        _pip_pos[0] = pos + n
    if n < frames:
        outdata[n:, 0] = 0.0


def _take_input(indata, frames, time_info, status):
    if _rec_on[0]:
        _rec_buf.append(indata.copy())


def open_streams():
    try:
        st = sd.OutputStream(samplerate=SAMPLE_RATE, channels=1,
                             dtype='float32', callback=_feed_output)
        st.start()
        _out_stream[0] = st
    except Exception as e:
        print('could not open the output stream (%s); no pip will be heard.'
              % type(e).__name__)
    try:
        st = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16',
                            blocksize=int(SAMPLE_RATE * 0.05),
                            callback=_take_input)
        st.start()
        _in_stream[0] = st
    except Exception as e:
        raise SystemExit('Could not open the microphone (%s).\nNothing would '
                         'be recorded, so the task stops here.' % type(e).__name__)


def start_trial_audio():
    """Fire the pip and begin keeping the microphone input. On the flip."""
    _pip_pos[0] = 0
    del _rec_buf[:]
    _rec_on[0] = True


def stop_trial_audio():
    _rec_on[0] = False
    return (np.concatenate(_rec_buf) if _rec_buf
            else np.zeros((0, 1), 'int16'))


def close_streams():
    for holder in (_in_stream, _out_stream):
        st = holder[0]
        if st is not None:
            try:
                st.stop(); st.close()
            except Exception:
                pass
            holder[0] = None


def check_pips(folder, rows):
    """After the session, say which trials have no pip at the start.
    """
    missing = []
    for r in rows:
        path = os.path.join(folder, r['response_wav'])
        try:
            x, rate = sf.read(path, dtype='float32', always_2d=True)
            x = x[:, 0]
        except Exception:
            continue
        head = x[:int(rate * (BEEP_MS / 1000.0))]
        if not len(head):
            missing.append(r['response_wav']); continue
        win_n = max(1, int(rate * 0.02))
        frames_ = x[:len(x) // win_n * win_n].reshape(-1, win_n)
        levels = 20 * np.log10(np.sqrt((frames_ ** 2).mean(axis=1)) + 1e-10)
        floor = float(np.percentile(levels, 10))
        head_db = 20 * np.log10(np.sqrt((head ** 2).mean()) + 1e-10)
        if head_db < floor + 10:
            missing.append(r['response_wav'])
    return missing


def write_coding_sheet():
    """The sheet the responses are coded ON, afterwards, from the recordings."""
    try:
        with open(base + '.csv', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
    except Exception:
        return
    with open(base + '_coding.csv', 'w', newline='', encoding='utf-8') as g:
        w = csv.writer(g)
        w.writerow(['trial', 'block', 'block_type', 'target_word', 'response_wav',
                    'transcription', 'score', 'error_type', 'notes'])
        for r in rows:
            w.writerow([r['trial'], r['block'], r['block_type'], r['target_word'],
                        r['response_wav'], '', '', '', ''])
        w.writerow([])
        w.writerow(['score: 1 = correct, 0 = incorrect'])
        w.writerow(['error_type (CONFIRM WITH SIMONA): ' + ', '.join(ERROR_TYPES)])


open_streams()
show_text(INSTRUCTIONS, ['space'])
prev_block = None
for n, it in enumerate(items):
    block = BLOCK_OF[n]
    if prev_block is not None and block != prev_block:
        show_text(BLOCK_BREAK, ['space'])
    prev_block = block
    trial_in_block = sum(1 for m in range(n + 1) if BLOCK_OF[m] == block)

    w, h = Image.open(it['path']).size
    pic = visual.ImageStim(win, image=it['path'], size=(PIC_HEIGHT * w / h, PIC_HEIGHT))
    fix.draw(); win.flip(); core.wait(FIX_DUR)

    # Both streams are already running; these only flip a flag and rewind
    # the pip, so they cost nothing and happen on the exact frame the
    # picture goes up.
    win.callOnFlip(clock.reset)
    win.callOnFlip(start_trial_audio)
    pic.draw(); win.flip(); event.clearEvents()
    key = event.waitKeys(maxWait=MAX_RECORD_S,
                         keyList=ADVANCE + ['escape'], timeStamped=clock)
    audio = stop_trial_audio()

    if key is None:                       # nobody pressed anything in time
        elapsed, stop_reason = MAX_RECORD_S, 'max_time'
    else:
        if key[0][0] == 'escape': finish(aborted=True)
        elapsed, stop_reason = key[0][1], 'key'

    wav_name = '%s_%s_T%02d_%s.wav' % (LANGUAGE, pid, n + 1, it['word'])
    sf.write(os.path.join(out_root, wav_name), audio, SAMPLE_RATE)

    writer.writerow(dict(participant=pid, language=LANGUAGE, trial=n + 1,
                         block=block,
                         block_type='nouns' if it['category'] == 'noun' else 'verbs',
                         trial_in_block=trial_in_block, category=it['category'],
                         target_word=it['word'], picture_file=it['picture_file'],
                         response_wav=wav_name, ra_keypress_s=round(elapsed, 3),
                         recording_s=round(len(audio) / SAMPLE_RATE, 3),
                         stop_reason=stop_reason,
                         input_mode=INPUT_MODE, build=BUILD,
                         timestamp=time.strftime('%Y-%m-%d %H:%M:%S')))
    out.flush()
    win.flip(); core.wait(0.3)

out.close()
close_streams()
write_coding_sheet()
with open(base + '.csv', encoding='utf-8') as f:
    _rows = list(csv.DictReader(f))
_missing = check_pips(out_root, _rows)
if _missing:
    print('NO PIP FOUND at the start of %d recording(s):' % len(_missing))
    for m in _missing:
        print('   ', m)
    print('Tell Nursena before running anyone else - the onset marker is') # warning for the RAs, can be omitted/edited.
    print('what makes a naming latency recoverable.')
else:
    print('Pip found at the start of all %d recordings.' % len(_rows))
show_text(END_TEXT, ['space'])
win.close(); core.quit()
