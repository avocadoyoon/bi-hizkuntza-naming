# Bi-hizuntza-naming (two-languages-naming) 📑:

- Item selection and a PsychoPy picture-naming task for Spanish and Basque.

- Picks 20 nouns and 20 verbs per language from the MULTIMAP norms. Items are chosen by name agreement, non-cognate status, word frequency and syllable length. 
- The task shows the pictures in separate noun and verb blocks and records one audio file per trial.

- The pictures, the selected item list and the norms spreadsheet are not included. The items are unpublished stimuli, and the norms belong to their authors.

## Contents
- scripts/`load.py`, `pick_sep.py`, `syll.py`: item selection (needs `MULTIMAP_CrossLanguage.xlsx` in the same folder)
- scripts/`dl.py`: downloads the chosen pictures from the MULTIMAP server
- `task/`: the Spanish and Basque PsychoPy scripts and helpers

## Source of the norms
MULTIMAP cross-language norms, git.bcbl.eu/sgisbert/multimap2. Please cite the original authors.

## Licence
MIT (code only ⚠️).
