import sys; from pathlib import Path; HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
import numpy as np, pandas as pd
from scipy import stats
from load import build
from syll import eu_syll

EXCL={'egg','road','bucket','glass','arm'}
rng=np.random.default_rng(7)
def pool(k):
    d=build(k)
    d=d[~d.english.isin(EXCL)&~d.eu_bare.str.contains(' ')&~d.es.str.contains(' ')&(d.lev_norm>=.6)].copy()
    d['eu_syll']=[eu_syll(w) if x!=x else x for w,x in zip(d.eu,d.eu_syll)]
    d=d.sort_values(['english']).reset_index(drop=True)
    d=d.dropna(subset=['eu_logfreq','es_logfreq'])
    d=d[(d.eu_logfreq>0)&~d.img.isin(['Carreta.bmp','Carretera.bmp'])]
    return d
P={k:pool(k) for k in ['noun','verb']}
def cands(k,l):
    d=P[k]; d=d[d[l+'_agree']>=80].sort_values(l+'_agree').drop_duplicates(l,keep='last'); return d.sort_values('english').reset_index(drop=True)
C={(k,l):cands(k,l) for k in ['noun','verb'] for l in ['es','eu']}
for key,v in C.items(): print(key,len(v))
keys=list(C)
def ps(sel):
    out=[]
    for m in ['logfreq','syll']:
        g={(k,l):C[(k,l)].iloc[sel[(k,l)]][l+'_'+m].values for (k,l) in keys}
        for a,b in [(('noun','es'),('noun','eu')),(('verb','es'),('verb','eu')),(('noun','es'),('verb','es')),(('noun','eu'),('verb','eu'))]:
            out.append(stats.ttest_ind(g[a],g[b],equal_var=False).pvalue)
    return out
def overlap(sel,k): return len(set(C[(k,'es')].iloc[sel[(k,'es')]].img)&set(C[(k,'eu')].iloc[sel[(k,'eu')]].img))
def score(sel): return min(ps(sel))-0.3*sum(overlap(sel,k) for k in ['noun','verb'])
best=(-9,None)
for r in range(60):
    sel={key:list(rng.choice(len(C[key]),20,replace=False)) for key in keys}
    cur=score(sel)
    for it in range(400):
        key=keys[rng.integers(4)]; pos=rng.integers(20); new=rng.integers(len(C[key]))
        if new in sel[key]: continue
        old=sel[key][pos]; sel[key][pos]=new; s=score(sel)
        if s>=cur: cur=s
        else: sel[key][pos]=old
    if cur>best[0]: best=(cur,{k:list(v) for k,v in sel.items()})
sel=best[1]; print('min p',min(ps(sel)),'overlap',[overlap(sel,k) for k in ['noun','verb']])
rows=[]
for (k,l) in keys:
    d=C[(k,l)].iloc[sel[(k,l)]]
    for _,r in d.iterrows():
        rows.append(dict(category=k,language={'es':'Spanish','eu':'Basque'}[l],word=r[l],word_bare=(r['eu_bare'] if l=='eu' else r['es']),translation_other_language=r['eu' if l=='es' else 'es'],english=r.english,picture_file=r.img,name_agreement=r[l+'_agree'],log_freq=r[l+'_logfreq'],n_syllables=r[l+'_syll'],lev_dist_es_eu=r.lev,lev_norm=round(r.lev_norm,2)))
out=pd.DataFrame(rows).sort_values(['category','language','word'])
out.to_csv(HERE/'selected_items_by_language.csv',index=False)
pd.set_option('display.width',200)
print(out.drop(columns=['english','lev_dist_es_eu']).to_string(index=False))
g=out.groupby(['category','language'])[['name_agreement','log_freq','n_syllables']].agg(['mean','std']).round(2); print(g)
names=['logfreq ES-EU nouns','logfreq ES-EU verbs','logfreq ES n-v','logfreq EU n-v','syll ES-EU nouns','syll ES-EU verbs','syll ES n-v','syll EU n-v']
for n,p in zip(names,ps(sel)): print(n,round(p,3))
