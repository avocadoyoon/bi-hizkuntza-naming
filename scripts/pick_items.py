import sys; sys.path.insert(0,'/private/tmp/claude-501/-Users-lilavocado--claude-spares-spare-qtprbx/715200af-7595-41c2-b3cb-b754d5412e97/scratchpad')
import numpy as np, pandas as pd
from scipy import stats
from load import build
from syll import eu_syll

EXCL={'egg','road','bucket','glass','arm'}
rng=np.random.default_rng(1)
def cand(k):
    d=build(k); d=d[~d.english.isin(EXCL)&~d.eu.str.contains(' ')&~d.es.str.contains(' ')].copy(); d['eu_syll']=[eu_syll(w) if k=='noun' or x!=x else x for w,x in zip(d.eu,d.eu_syll)]; d=d[(d.es_agree>=80)&(d.eu_agree>=80)&(d.lev_norm>=.6)].dropna().reset_index(drop=True)
    return d
N,V=cand('noun'),cand('verb')
print(len(N),len(V))
def pmin(n,v):
    ps=[]
    for m in ['logfreq','syll']:
        g={('es','n'):n['es_'+m],('eu','n'):n['eu_'+m],('es','v'):v['es_'+m],('eu','v'):v['eu_'+m]}
        for a,b in [(('es','n'),('eu','n')),(('es','v'),('eu','v')),(('es','n'),('es','v')),(('eu','n'),('eu','v'))]:
            ps.append(stats.ttest_ind(g[a],g[b],equal_var=False).pvalue)
    return min(ps)
def dedupe(d): return d.sort_values(['english','es_agree','eu_agree']).drop_duplicates('english',keep='last').reset_index(drop=True)
N,V=dedupe(N),dedupe(V)
best=(0,None)
for restart in range(40):
    ni=list(rng.choice(len(N),20,replace=False)); vi=list(rng.choice(len(V),20,replace=False))
    cur=pmin(N.iloc[ni],V.iloc[vi])
    for it in range(250):
        which=rng.integers(2); idx,pool=(ni,N) if which==0 else (vi,V)
        pos=rng.integers(20); new=rng.integers(len(pool))
        if new in idx: continue
        old=idx[pos]; idx[pos]=new
        p=pmin(N.iloc[ni],V.iloc[vi])
        if p>=cur: cur=p
        else: idx[pos]=old
    if cur>best[0]: best=(cur,(N.iloc[ni],V.iloc[vi]))
print('best min p',best[0])
n,v=best[1]
out=pd.concat([n,v]).sort_values(['kind','english'])
out.to_csv('/Users/lilavocado/PhD/multimap_selection/selected_items.csv',index=False)
cols=['english','es','eu','es_agree','eu_agree','es_logfreq','eu_logfreq','es_syll','eu_syll','lev','img']
pd.set_option('display.width',250)
print(out[cols].to_string(index=False))
for m in ['logfreq','syll']:
    for k,d in [('noun',n),('verb',v)]:
        print(m,k,'ES %.2f (%.2f)  EU %.2f (%.2f)'%(d['es_'+m].mean(),d['es_'+m].std(),d['eu_'+m].mean(),d['eu_'+m].std()))
    print(m,'es noun vs verb p=%.2f ; eu noun vs verb p=%.2f ; es vs eu noun p=%.2f ; es vs eu verb p=%.2f'%(
      stats.ttest_ind(n['es_'+m],v['es_'+m]).pvalue,stats.ttest_ind(n['eu_'+m],v['eu_'+m]).pvalue,
      stats.ttest_ind(n['es_'+m],n['eu_'+m]).pvalue,stats.ttest_ind(v['es_'+m],v['eu_'+m]).pvalue))
