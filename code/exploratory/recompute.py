import os
import pandas as pd, numpy as np, itertools, json
from scipy.stats import kendalltau

D = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'daily_acc_panel.csv'), parse_dates=['date'])
POOL7 = ['acc_S01_src1','acc_S02_src2','acc_S04_vendorF','acc_S06_scale','acc_S09_scale','acc_S11_floor05','acc_S13_blendY']
POOL3 = ['acc_S01_src1','acc_S02_src2','acc_S04_vendorF']

# farm-averaged daily panel
g = D.groupby('date')[POOL7].mean()

wins = pd.date_range('2024-01-01','2025-03-26',freq='15D')
rows=[]
for s in wins:
    bt = g.loc[s-pd.Timedelta(days=365): s-pd.Timedelta(days=1)]
    dp = g.loc[s: s+pd.Timedelta(days=89)]
    if len(bt)<300 or len(dp)<85: continue
    bm = bt.mean(); dm = dp.mean()
    pick = bm.idxmax()
    best_fixed = dm.idxmax()
    # daily oracle
    orac = dp.max(axis=1)
    chosen_daily = dp[pick]
    regret_daily = float((orac - chosen_daily).mean())
    regret_fixed = float(dm[best_fixed] - dm[pick])
    # "excess over best-fixed-if-oracle": i.e. regret of fixed choice vs daily oracle
    rows.append(dict(window=s.date().isoformat(), pick=pick, best=best_fixed,
                     hit=int(pick==best_fixed), regret_daily=regret_daily, regret_fixed=regret_fixed,
                     gap12=float(bm.nlargest(2).iloc[0]-bm.nlargest(2).iloc[1]),
                     bm_pick=float(bm[pick]), bm_best=float(bm[best_fixed]),
                     dm_pick=float(dm[pick]), dm_best=float(dm[best_fixed])))

R=pd.DataFrame(rows)
print("n windows", len(R))
print(R.head(3).to_string())
print("\n=== ORACLE vs FIXED ===")
for c in ['regret_daily','regret_fixed']:
    print(f"{c}: mean={R[c].mean():.4f} med={R[c].median():.4f} p90={R[c].quantile(.9):.4f} max={R[c].max():.4f} sum={R[c].sum():.2f}")
print("\nratio daily/fixed (median):", (R.regret_daily/R.regret_fixed.replace(0,np.nan)).median())
print("windows with regret_fixed>0:", int((R.regret_fixed>0).sum()), "/", len(R))
print("\n=== hit ===")
print("hits", R.hit.sum(), "=", round(100*R.hit.mean(),1),"%")
print("pick counts\n", R.pick.value_counts().to_string())
print("best counts\n", R.best.value_counts().to_string())
print("\ngap12: med=%.3f mean=%.3f"%(R.gap12.median(), R.gap12.mean()))
print("corr(gap12,hit) pearson=%.3f  spearman=%.3f"%(R.gap12.corr(R.hit), R.gap12.corr(R.hit,method='spearman')))
print("\n=== conversion sanity (B11) ===")
print("B11: 5.2174 GWh / 2.6351 pt =", round(5.2174476895807755/2.635074590697361,4), "GWh/pt")
print("B11: 286.07 wan / 5.21745 GWh =", round(286.07204154300064/5.2174476895807755,3), "wan/GWh")
R.to_csv('/tmp/econ/regret_decision.csv',index=False)
