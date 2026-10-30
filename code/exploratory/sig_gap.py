import os
import pandas as pd, numpy as np
from scipy import stats
D = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'daily_acc_panel.csv'), parse_dates=['date'])
P7=['acc_S01_src1','acc_S02_src2','acc_S04_vendorF','acc_S06_scale','acc_S09_scale','acc_S11_floor05','acc_S13_blendY']
A='acc_S02_src2'; B='acc_S06_scale'
g=D.groupby('date')[P7].mean()
wins=pd.date_range('2024-01-01','2025-03-26',freq='15D')
bt_s=[];dp_s=[];bt_g=[];dp_g=[];hits=[]
for s in wins:
    bt=g.loc[s-pd.Timedelta(days=365): s-pd.Timedelta(days=1)]
    dp=g.loc[s:s+pd.Timedelta(days=89)]
    if len(bt)<300 or len(dp)<85: continue
    bm=bt.mean(); dm=dp.mean()
    bt_s.append(bm[A]-bm[B]); dp_s.append(dm[A]-dm[B])
    bt_g.append(bm.nlargest(2).iloc[0]-bm.nlargest(2).iloc[1])
    dp_g.append(dm.nlargest(2).iloc[0]-dm.nlargest(2).iloc[1])
    hits.append(int(bm.idxmax()==dm.idxmax()))
bt_s=np.array(bt_s);dp_s=np.array(dp_s);bt_g=np.array(bt_g);dp_g=np.array(dp_g);hits=np.array(hits)
def rep(nm,x,y):
    r,p=stats.pearsonr(x,y); rs,ps=stats.spearmanr(x,y)
    print(f"{nm}: pearson r={r:+.3f} (p={p:.3f})  spearman={rs:+.3f} (p={ps:.3f})")
print("n=",len(bt_s))
rep("signed gap  bt vs deploy", bt_s, dp_s)
rep("abs gap     bt vs deploy", np.abs(bt_s), np.abs(dp_s))
rep("signed gap  bt vs hit", bt_s, hits)
rep("abs gap     bt vs hit", np.abs(bt_s), hits)
# variance decomposition of realized signed gap
print("\nrealized signed gap: mean=%+.3f sd=%.3f"%(dp_s.mean(),dp_s.std(ddof=1)))
print("bt       signed gap: mean=%+.3f sd=%.3f"%(bt_s.mean(),bt_s.std(ddof=1)))
print("=> if bt had zero info, sd(bt)=0.35 (its own SE); observed sd=%.2f"%bt_s.std(ddof=1))
# implied: corr = cov/(sd_bt sd_dp)
print("\nceiling hit rate implied by observed decomposition:")
tau2=max(dp_s.var(ddof=1)-0.713**2,0); tau=np.sqrt(tau2)
rho=tau/np.sqrt(tau2+0.713**2)
best=0.5+np.arcsin(rho)/np.pi
print("  sd(realized)=%.3f, 90d noise=%.3f, => sd(true)=%.3f"%(dp_s.std(ddof=1),0.713,tau))
print("  corr(true,realized)=%.3f  => best achievable hit = %.1f%%"%(rho,100*best))
# how often does bt correctly order the pair among windows where deploy gap is resolvable?
res=[]; 
for i,s in enumerate(wins):
    dp=g.loc[s:s+pd.Timedelta(days=89)]
    if len(dp)<85: continue
    d=(dp[A]-dp[B]).dropna()
print("\ncorr(bt signed gap, deploy hit) reported above is the key number.")
# regression
sl,ic,r,p,se=stats.linregress(bt_s,dp_s)
print("\nregress deploy_gap on bt_gap: slope=%.3f (se %.3f)  intercept=%.3f  R2=%.3f"%(sl,se,ic,r**2))
