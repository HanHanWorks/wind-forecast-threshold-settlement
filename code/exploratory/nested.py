import os
import pandas as pd, numpy as np, math, itertools
D = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'daily_acc_panel.csv'), parse_dates=['date'])
CORE=['acc_S01_src1','acc_S02_src2','acc_S04_vendorF']            # 3 independent sources
POST=['acc_S06_scale','acc_S09_scale','acc_S11_floor05','acc_S13_blendY']  # 4 post-processing variants
g=D.groupby('date')[CORE+POST].mean()
wins=pd.date_range('2024-01-01','2025-03-26',freq='15D')
WIN=[]
for s in wins:
    bt=g.loc[s-pd.Timedelta(days=365): s-pd.Timedelta(days=1)]
    dp=g.loc[s:s+pd.Timedelta(days=89)]
    if len(bt)<300 or len(dp)<85: continue
    WIN.append((s,bt,dp))
print("windows:",len(WIN))
print("\n=== nested ladder: add post-processing variants one at a time (avg over all 5 subsets of size k) ===")
print("k  pools_tested  mean_hit      min_hit   max_hit   mean_median_gap")
for k in range(3,8):
    hits=[];gaps=[]
    n=1 if k==3 else (4 if k==7 else math.factorial(4)//(math.factorial(k-3)*math.factorial(7-k)))
    for extra in itertools.combinations(POST,k-3):
        pool=CORE+list(extra)
        h=0;gg=[]
        for s,bt,dp in WIN:
            bm=bt[pool].mean(); dm=dp[pool].mean()
            h+=int(bm.idxmax()==dm.idxmax()); gg.append(bm.nlargest(2).iloc[0]-bm.nlargest(2).iloc[1])
        hits.append(h); gaps.append(np.median(gg))
    print(f"{k}  {len(hits):11d}  {100*np.mean(hits)/len(WIN):6.1f}% ({np.mean(hits):.1f})  {100*min(hits)/len(WIN):6.1f}%  {100*max(hits)/len(WIN):6.1f}%  {np.mean(gaps):.2f}")
print("\n=== which single variant wrecks it? (3 core + 1 variant) ===")
for extra in POST:
    pool=CORE+[extra]; h=0;gg=[]
    for s,bt,dp in WIN:
        bm=bt[pool].mean(); dm=dp[pool].mean()
        h+=int(bm.idxmax()==dm.idxmax()); gg.append(bm.nlargest(2).iloc[0]-bm.nlargest(2).iloc[1])
    print(f"  +{extra:20s} hit={h}/31 ({100*h/31:5.1f}%)  median gap={np.median(gg):.2f}")
