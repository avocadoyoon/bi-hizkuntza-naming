import csv,os,json,urllib.parse,urllib.request
api="https://git.bcbl.eu/api/v4/projects/sgisbert%2Fmultimap2/repository/"
names={}
for sub in ['New_Objects','New_Verbs']:
    names[sub]={x['name'].lower():x['name'] for x in json.load(urllib.request.urlopen(api+f"tree?path=DATA/Stimuli/{sub}&per_page=200"))}
miss=[];n=0
for r in csv.DictReader(open('selected_items_by_language.csv')):
    sub='New_Objects' if r['category']=='noun' else 'New_Verbs'
    real=names[sub].get(r['picture_file'].lower())
    out=f"pictures/{r['language']}/{r['category']}s"; os.makedirs(out,exist_ok=True)
    dest=f"{out}/{r['word']}__{r['picture_file']}"
    old=f"previous_bare_form/{dest}"
    try:
        if os.path.exists(old): data=open(old,'rb').read()
        else: data=urllib.request.urlopen(api+"files/"+urllib.parse.quote(f"DATA/Stimuli/{sub}/{real}",safe='')+"/raw?ref=master",timeout=60).read()
        open(dest,'wb').write(data); n+=1
    except Exception as e: miss.append((r['word'],str(e)))
print(n,'ok; missing',miss)
