import os
import pandas as pd, numpy as np, math
D = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'daily_acc_panel.csv'), parse_dates=['date'])
P7=['acc_S01_src1','acc_S02_src2','acc_S04_vendorF','acc_S06_scale','acc_S09_scale','acc_S11_floor05','acc_S13_blendY']
P3=['acc_S01_src1','acc_S02_src2','acc_S04_vendorF']
g=D.groupby('date')[P7].mean()
wins=pd.date_range('2024-01-01','2025-03-26',freq='15D')
def comb(n,k): return math.factorial(n)//(math.factorial(k)*math.factorial(n-k))
def mcn(b,c):
    n=b+c
    if n==0: return 1.0
    return min(1.0,2*sum(comb(n,i) for i in range(min(b,c)+1))/2**n)
out={}
for name,pool in [('7pool',P7),('3pool',P3)]:
    hit=[];gaps=[];se=[];picks=[];bests=[]
    for s in wins:
        bt=g.loc[s-pd.Timedelta(days=365): s-pd.Timedelta(days=1)][pool]
        dp=g.loc[s:s+pd.Timedelta(days=89)][pool]
        if len(bt)<300 or len(dp)<85: continue
        bm=bt.mean(); pick=bm.idxmax(); best=dp.mean().idxmax()
        hit.append(int(pick==best)); gaps.append(bm.nlargest(2).iloc[0]-bm.nlargest(2).iloc[1])
        picks.append(pick); bests.append(best)
        d=(dp[pick]-dp[best]).dropna(); 
        se.append((dp[best]-dp[pick]).std(ddof=1)/np.sqrt(len(dp)))
    out[name]=dict(hit=np.array(hit),gaps=np.array(gaps),se=np.array(se),picks=picks,bests=bests)
    print(f"{name}: hits={sum(hit)}/{len(hit)} = {100*np.mean(hit):.1f}%  median gap={np.median(gaps):.2f}  median 90d SE(diff)={np.median(se):.2f}")
    print("   picks:",pd.Series(picks).value_counts().to_dict())
    print("   bests:",pd.Series(bests).value_counts().to_dict())
a=out['7pool']['hit'];b=out['3pool']['hit']
i=int(((a==1)&(b==0)).sum());j=int(((a==0)&(b==1)).sum())
print(f"\nMcNemar 7pool vs 3pool: discordant 7pool-only={i}, 3pool-only={j}, exact p={mcn(i,j):.5f}")
print("ratio median gap / median SE:  7pool=%.2f  3pool=%.2f"%(np.median(out['7pool']['gaps'])/np.median(out['7pool']['se']),
                                                                np.median(out['3pool']['gaps'])/np.median(out['3pool']['se'])))
