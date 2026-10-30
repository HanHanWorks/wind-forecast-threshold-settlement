import os
import pandas as pd, numpy as np
D = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'daily_acc_panel.csv'), parse_dates=['date'])
POOL=['acc_S01_src1','acc_S02_src2','acc_S04_vendorF','acc_S06_scale','acc_S09_scale','acc_S11_floor05','acc_S13_blendY']
g = D.groupby('date')[POOL].mean()
R = pd.read_csv('/tmp/econ/regret_decision.csv')
wins=pd.date_range('2024-01-01','2025-03-26',freq='15D')
dep={}
for s in wins:
    dp=g.loc[s:s+pd.Timedelta(days=89)]
    if len(dp)>=85: dep[s.date().isoformat()]=dp
sp={w:d.mean().rank(ascending=False) for w,d in dep.items()}
rk=np.array([sp[w][p] for w,p in zip(R.window,R.pick)])
print("pick deploy-rank (1=best):",dict(pd.Series(rk).value_counts().sort_index()))

print("\n=== finalist duel: src2 vs S06, 90-day mean difference ===")
rng=np.random.default_rng(11)
rows=[]
for w,d in dep.items():
    diff=(d['acc_S02_src2']-d['acc_S06_scale']).dropna().values
    n=len(diff); m=diff.mean(); sd=diff.std(ddof=1); se=sd/np.sqrt(n)
    # circular block bootstrap on the mean
    L=7; nb=int(np.ceil(n/L)); bs=np.empty(4000)
    for b in range(4000):
        st=rng.integers(0,n,nb)
        idx=np.concatenate([(np.arange(s,s+L)%n) for s in st])[:n]
        bs[b]=diff[idx].mean()
    lo,hi=np.percentile(bs,[2.5,97.5])
    rows.append(dict(window=w,n=n,mean=m,se_naive=se,lo=lo,hi=hi,
                     sig=int(lo>0 or hi<0),t=m/se,
                     winner='src2' if m>0 else 'S06'))
F=pd.DataFrame(rows)
print("mean gap=%.3f pt ; median |gap|=%.3f"%(F['mean'].mean(),F['mean'].abs().median()))
print("naive SE median=%.3f ; block-boot 95%% CI width median=%.3f"%(F.se_naive.median(),(F.hi-F.lo).median()))
print("windows where the duel is statistically resolvable (CI excludes 0): %d/%d = %.1f%%"%(F.sig.sum(),len(F),100*F.sig.mean()))
print("|gap| < 1 pt: %d/%d"%( (F['mean'].abs()<1).sum(), len(F)))
print("median 90-day paired SE (naive) = %.3f  ->  the 0.62 pt gap is %.2f SE"%(F.se_naive.median(), 0.62/F.se_naive.median()))
print("\nper-window:\n",F.round(3).to_string(index=False))
F.to_csv('/tmp/econ/duel.csv',index=False)

# noise floor vs pool granularity: distribution of pairwise gaps among top-3 in backtest
print("\n=== backtest top-1 minus top-2 gap, vs 90-day paired SE ===")
print("gap median=%.2f ; SE median=%.2f ; ratio=%.2f"%(R.gap12.median(),F.se_naive.median(),R.gap12.median()/F.se_naive.median()))
