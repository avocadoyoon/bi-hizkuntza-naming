import openpyxl, pandas as pd, numpy as np
from pathlib import Path

X=Path(__file__).resolve().parent/'MULTIMAP_CrossLanguage.xlsx'  # download from the MULTIMAP repo, see README
wb=openpyxl.load_workbook(X,data_only=True)
def sheet(n,anchor):
    rows=list(wb[n].iter_rows(values_only=True))
    h=list(rows[0]); i=h.index(anchor)
    h=[str(c).strip() if c is not None else f'x{j}' for j,c in enumerate(h)][i:]
    return pd.DataFrame([r[i:] for r in rows[1:]],columns=h).dropna(subset=[h[0]])
def lev(a,b):
    a=a.lower();b=b.lower();p=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        c=[i]
        for j,y in enumerate(b,1): c.append(min(p[j]+1,c[-1]+1,p[j-1]+(x!=y)))
        p=c
    return p[-1]
def build(kind):
    A,B=('Noun','Noun') if kind=='noun' else ('Verb','Verb')
    sp=sheet('Spanish_objects' if kind=='noun' else 'Spanish_verbs',A)
    ba=sheet('Basque_objects' if kind=='noun' else 'Basque_verbs',B)
    sp=sp[['Noun' if kind=='noun' else 'Verb','Translation','log_frq','es_num_syll','name_agree','IMG_CODE']]
    sp.columns=['english','es','es_logfreq','es_syll','es_agree','img']
    if kind=='noun':
        ba=ba[['Translation','with article','LOG10_FREQ_a','NUM_SYLL','name_agree','IMG_CODE']]
        ba.columns=['eu_bare','eu','eu_logfreq','eu_syll','eu_agree','img']
    else:
        ba=ba[['Translation','LOG10_FREQ','NUM_SYLL','name_agree','IMG_CODE']]
        ba.columns=['eu','eu_logfreq','eu_syll','eu_agree','img']
        ba['eu_bare']=ba['eu']
    d=sp.merge(ba,on='img').dropna(subset=['es','eu'])
    for c in ['es_logfreq','es_syll','es_agree','eu_logfreq','eu_syll','eu_agree']: d[c]=pd.to_numeric(d[c],errors='coerce')
    d['lev']=[lev(a,b) for a,b in zip(d.es,d.eu_bare)]
    d['lev_norm']=d.lev/d[['es','eu_bare']].apply(lambda r:max(len(r.es),len(r.eu_bare)),axis=1)
    d['kind']=kind
    return d
if __name__=='__main__':
    for k in ['noun','verb']:
        d=build(k); print(k,len(d),d.isna().sum().to_dict())
        ok=d[(d.es_agree>=80)&(d.eu_agree>=80)]
        print(' agree>=80 both:',len(ok),' noncognate (lev_norm>=.6):',(ok.lev_norm>=.6).sum())
        print(d.head(3).to_string())
