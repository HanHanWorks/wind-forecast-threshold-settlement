import os
import pandas as pd, numpy as np
D = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'daily_acc_panel.csv'), parse_dates=['date'])
POOL=['acc_S01_src1','acc_S02_src2','acc_S04_vendorF','acc_S06_scale','acc_S09_scale','acc_S11_floor05','acc_S13_blendY']
g = D.groupby('date')[POOL].mean()
R = pd.read_csv('/tmp/econ/regret_decision.csv')
wins=pd.date_range('2024-01-01','2025-03-26',freq='15D')

def C(n,k):
    return int(np.math.factorial(n)//(np.math.factorial(k)*np.math.factorial(n-k))) if hasattr(np,'math') else None
import math
def comb(n,k): return math.factorial(n)//(math.factorial(k)*math.factorial(n-k))
def mcnemar_exact(b,c):
    n=b+c
    if n==0: return 1.0
    k=min(b,c)
    p=sum(comb(n,i) for i in range(k+1))/2**n*2
    return min(1.0,p)

rules={}
rows=[]
for s in wins:
    bt=g.loc[s-pd.Timedelta(days=365): s-pd.Timedelta(days=1)]
    dp=g.loc[s:s+pd.Timedelta(days=89)]
    if len(bt)<300 or len(dp)<85: continue
    bm=bt.mean(); top2=bm.nlargest(2).index.tolist(); best=dp.mean().idxmax()
    # features computed on BACKTEST data only
    f={}
    for sysn in top2:
        x=bt[sysn]
        roll=x.rolling(30).mean().dropna()
        f[sysn]=dict(mean=x.mean(), sd30=roll.std(), worst30=roll.min(),
                     recent90=x.iloc[-90:].mean(), recent30=x.iloc[-30:].mean(),
                     cv=x.std()/x.mean(),
                     downside=x.quantile(0.1))
    a,b=top2[0],top2[1]
    picks={
      'A_backtest_top1':a,
      'B_incumbent_src2':'acc_S02_src2' if 'acc_S02_src2' in top2 else a,
      'C_lower_vol30':a if f[a]['sd30']<f[b]['sd30'] else b,
      'D_higher_recent90':a if f[a]['recent90']>f[b]['recent90'] else b,
      'E_higher_worst30':a if f[a]['worst30']>f[b]['worst30'] else b,
      'F_higher_downside':a if f[a]['downside']>f[b]['downside'] else b,
      'G_lower_cv':a if f[a]['cv']<f[b]['cv'] else b,
      'H_always_S06':'acc_S06_scale' if 'acc_S06_scale' in top2 else a,
    }
    rows.append(dict(window=s.date().isoformat(),best=best,top2='|'.join(top2),
                     gap=bm.nlargest(2).iloc[0]-bm.nlargest(2).iloc[1],
                     **{k:int(v==best) for k,v in picks.items()},
                     **{k+"_p":v for k,v in picks.items()}))
T=pd.DataFrame(rows)
print("n=",len(T))
summ=T[[c for c in T.columns if not c.endswith('_p') and c not in('window','best','top2','gap')]].sum()
print(summ.sort_values(ascending=False).to_string())
print("\nvs A (McNemar exact, discordant b/c):")
a=T['A_backtest_top1'].values
for c in summ.index:
    if c=='A_backtest_top1': continue
    x=T[c].values; b=int(((a==1)&(x==0)).sum()); cc=int(((a==0)&(x==1)).sum())
    print(f"  {c:22s} hits={x.sum():2d} ({100*x.mean():4.1f}%)  vs A: +{cc}/-{b}  p={mcnemar_exact(b,cc):.3f}")
print("\ntop2 composition:", dict(T.top2.value_counts()))
T.to_csv('/tmp/econ/tiebreak.csv',index=False)
