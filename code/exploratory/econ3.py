import os
import pandas as pd, numpy as np
D = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'daily_acc_panel.csv'), parse_dates=['date'])
POOL=['acc_S01_src1','acc_S02_src2','acc_S04_vendorF','acc_S06_scale','acc_S09_scale','acc_S11_floor05','acc_S13_blendY']
g = D.groupby('date')[POOL].mean()
R = pd.read_csv('/tmp/econ/regret_decision.csv')
K=1.98; KW=54.83

wins = pd.date_range('2024-01-01','2025-03-26',freq='15D')
dep={}
for s in wins:
    dp = g.loc[s: s+pd.Timedelta(days=89)]
    if len(dp)<85: continue
    dep[s.date().isoformat()] = dp.mean()

reg_bt=[]; reg_rand=[]; reg_worst=[]; reg_2nd=[]
for w,p in zip(R.window,R.pick):
    dm=dep[w]; best=dm.max()
    reg_bt.append(best-dm[p])
    reg_rand.append((best-dm).mean())
    reg_worst.append(best-dm.min())
print("=== regret decomposition (deploy fixed-choice, pt) ===")
print("backtest Top-1 pick      mean=%.3f  -> %.2f GWh  %.0f wan"%(np.mean(reg_bt),np.mean(reg_bt)*K,np.mean(reg_bt)*K*KW))
print("random pick among 7      mean=%.3f  -> %.2f GWh"%(np.mean(reg_rand),np.mean(reg_rand)*K))
print("worst possible pick      mean=%.3f  -> %.2f GWh"%(np.mean(reg_worst),np.mean(reg_worst)*K))
print("value captured by backtest = %.2f of %.2f pt available = %.1f%%"%(np.mean(reg_rand)-np.mean(reg_bt),np.mean(reg_rand),100*(1-np.mean(reg_bt)/np.mean(reg_rand))))
print("residual (the 52%% metric) = %.2f pt = %.1f%% of total available value"%(np.mean(reg_bt),100*np.mean(reg_bt)/np.mean(reg_rand)))

# does the backtest ever pick a bottom-half system?
sp = pd.DataFrame(dep).T.rank(axis=1)
rank_of_pick = np.array([sp.loc[w,p] for w,p in zip(R.window,R.pick)])
print("\npick's deploy rank distribution (1=best):", dict(pd.Series(rank_of_pick).value_counts().sort_index()))
print("picks outside top-2: %d/%d"%( (rank_of_pick>2).sum(), len(rank_of_pick)))

# backtest rank of the true best  (is elimination reliable?)
btr={}
for s in wins:
    bt=g.loc[s-pd.Timedelta(days=365): s-pd.Timedelta(days=1)]
    if len(bt)<300: continue
    btr[s.date().isoformat()]=bt.mean().rank(ascending=False)
btrank_of_best=np.array([btr[w][dep[w].idxmax()] for w in R.window])
print("\nbacktest rank of the true deploy-best: ", dict(pd.Series(btrank_of_best).value_counts().sort_index()))
print("P(true best is backtest top-2) = %.1f%%"%(100*(btrank_of_best<=2).mean()))
print("P(true best is backtest bottom-2) = %.1f%%"%(100*(btrank_of_best>=6).mean()))

# long-run (pooled over all deploy days) top-2 gap
alldeploy = pd.concat([g.loc[s: s+pd.Timedelta(days=89)] for s in wins])
mm = alldeploy.mean()
print("\n=== pooled deploy mean over all 31x90 days ===")
print((mm.sort_values(ascending=False)-mm.max()).round(2).to_string())
