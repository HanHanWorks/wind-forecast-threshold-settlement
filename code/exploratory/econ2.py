import os
import pandas as pd, numpy as np
D = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'daily_acc_panel.csv'), parse_dates=['date'])
POOL=['acc_S01_src1','acc_S02_src2','acc_S04_vendorF','acc_S06_scale','acc_S09_scale','acc_S11_floor05','acc_S13_blendY']
g = D.groupby('date')[POOL].mean()
R = pd.read_csv('/tmp/econ/regret_decision.csv')
K_GWH = 5.2174476895807755/2.635074590697361   # GWh per ACC-pt per 90-day window
K_WAN = 286.07204154300064/5.2174476895807755  # 万元 per GWh

wins = pd.date_range('2024-01-01','2025-03-26',freq='15D')
dep={}
for s in wins:
    dp = g.loc[s: s+pd.Timedelta(days=89)]
    if len(dp)<85: continue
    dep[s.date().isoformat()] = dp.mean()

# 1) deploy spread across systems
SP = pd.DataFrame(dep).T
print("=== deploy mean ACC by system (across 31 windows) ===")
print(SP.mean().round(2).sort_values(ascending=False).to_string())
print("\nspread (max-min) per window: med=%.2f mean=%.2f"%((SP.max(1)-SP.min(1)).median(),(SP.max(1)-SP.min(1)).mean()))
print("incumbent src2 deploy mean = %.2f ; best-of-7 mean = %.2f ; worst = %.2f"%(SP['acc_S02_src2'].mean(), SP.max(1).mean(), SP.min(1).mean()))

# 2) value of backtest selection vs always-incumbent
sel_dm = np.array([dep[w][p] for w,p in zip(R.window,R.pick)])
inc_dm = np.array([dep[w]['acc_S02_src2'] for w in R.window])
orc_dm = np.array([dep[w].max() for w in R.window])
print("\n=== value of selection (deploy ACC) ===")
print("backtest-selected  mean=%.3f"%sel_dm.mean())
print("always-incumbent   mean=%.3f"%inc_dm.mean())
print("best-per-window    mean=%.3f"%orc_dm.mean())
print("delta(selected-incumbent)=%+.3f pt  -> %+.2f GWh/window  %+.1f wan"%(sel_dm.mean()-inc_dm.mean(),
      (sel_dm.mean()-inc_dm.mean())*K_GWH, (sel_dm.mean()-inc_dm.mean())*K_GWH*K_WAN))
print("wins/losses vs incumbent: %d / %d / %d ties"%(int((sel_dm>inc_dm+1e-9).sum()),int((sel_dm<inc_dm-1e-9).sum()),int((abs(sel_dm-inc_dm)<1e-9).sum())))

# 3) tail structure: is daily-oracle tail the same as fixed-regret tail?
R['rank_daily']=R.regret_daily.rank(ascending=False)
w8 = R.nlargest(8,'regret_daily')
print("\n=== worst-8 by regretA(daily oracle) ===")
print(w8[['window','pick','best','hit','regret_daily','regret_fixed']].to_string(index=False))
print("worst-8 fixed regret: mean=%.3f -> %.2f GWh ; all-31 mean=%.3f -> %.2f GWh"%(
    w8.regret_fixed.mean(), w8.regret_fixed.mean()*K_GWH, R.regret_fixed.mean(), R.regret_fixed.mean()*K_GWH))
print("corr(daily,fixed) spearman=%.3f"%R.regret_daily.corr(R.regret_fixed,method='spearman'))

# 4) block bootstrap on mean fixed regret, and on mean daily regret
rng=np.random.default_rng(7)
def boot(x,B=20000,L=3):
    n=len(x); out=np.empty(B)
    nb=int(np.ceil(n/L))
    for b in range(B):
        st=rng.integers(0,n,nb)
        idx=np.concatenate([(np.arange(s,s+L)%n) for s in st])[:n]
        out[b]=x[idx].mean()
    return np.percentile(out,[2.5,50,97.5])
for nm,c in [('regret_daily','regret_daily'),('regret_fixed','regret_fixed')]:
    lo,md,hi=boot(R[c].values)
    print(f"{nm}: mean={R[c].mean():.3f} boot95=[{lo:.3f},{hi:.3f}] -> GWh [{lo*K_GWH:.2f},{hi*K_GWH:.2f}]")
# 5) among the 15 misses
mi=R[R.hit==0]
print("\nmisses n=%d: fixed regret mean=%.3f med=%.3f max=%.3f -> %.2f GWh / %.0f wan"%(
    len(mi),mi.regret_fixed.mean(),mi.regret_fixed.median(),mi.regret_fixed.max(),
    mi.regret_fixed.mean()*K_GWH, mi.regret_fixed.mean()*K_GWH*K_WAN))
print("claim-consistent 'per wrong selection' cost: %.2f GWh, %.0f wan"%(mi.regret_fixed.mean()*K_GWH, mi.regret_fixed.mean()*K_GWH*K_WAN))
print("\nK_GWH=%.4f  K_WAN=%.3f"%(K_GWH,K_WAN))
