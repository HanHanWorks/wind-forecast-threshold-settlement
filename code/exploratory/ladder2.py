import os
import pandas as pd, numpy as np, math
D = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'daily_acc_panel.csv'), parse_dates=['date'])
P7=['acc_S01_src1','acc_S02_src2','acc_S04_vendorF','acc_S06_scale','acc_S09_scale','acc_S11_floor05','acc_S13_blendY']
g=D.groupby('date')[P7].mean()
wins=pd.date_range('2024-01-01','2025-03-26',freq='15D')
def comb(n,k): return math.factorial(n)//(math.factorial(k)*math.factorial(n-k))
def mcn(b,c):
    n=b+c
    if n==0: return 1.0
    return min(1.0,2*sum(comb(n,i) for i in range(min(b,c)+1))/2**n)
def run(fn,minlen=30):
    hits=[];gaps=[];ws=[];sign=[]
    for s in wins:
        seg=fn(s); dp=g.loc[s:s+pd.Timedelta(days=89)]
        if seg is None or len(seg)<minlen or len(dp)<85: continue
        bm=seg.mean(); pick=bm.idxmax(); best=dp.mean().idxmax()
        hits.append(int(pick==best)); gaps.append(bm.nlargest(2).iloc[0]-bm.nlargest(2).iloc[1]); ws.append(s.date().isoformat())
    return np.array(hits),np.array(gaps),ws
def trail(L):
    def f(s):
        b=s-pd.Timedelta(days=L); e=s-pd.Timedelta(days=1)
        if b<pd.Timestamp('2023-01-01'): return None
        return g.loc[b:e]
    return f
def season(lag):
    def f(s):
        b=s-pd.Timedelta(days=lag); e=b+pd.Timedelta(days=89)
        if b<pd.Timestamp('2023-01-01'): return None
        return g.loc[b:e]
    return f
schemes=[('T365 trailing 365d',trail(365)),('T270 trailing 270d',trail(270)),('T180 trailing 180d',trail(180)),('T120 trailing 120d',trail(120)),('T90  trailing 90d',trail(90)),('S365 season-match 1y lag',season(365)),('S450 season-match 15m lag',season(450)),('S540 season-match 18m lag',season(540))]
out={}
for nm,f in schemes:
    h,gp,ws=run(f)
    out[nm]=(h,gp)
    print(f"{nm:26s} n={len(h):2d}  hit={h.sum():2d} ({100*h.mean():5.1f}%)  median bt-gap={np.median(gp):.2f}")
base_h,_=out['T365 trailing 365d']
base_w=set(run(trail(365))[2])
print("\npaired comparisons on the SAME windows as T365:")
for nm,(h,gp) in out.items():
    if nm=='T365 trailing 365d': continue
    _,_,w2=run(dict(schemes)[nm])
    common=[w for w in base_w if w in set(w2)]
    bi=[i for i,w in enumerate(base_w) if w in common]
    ai=[w2.index(w) for w in common]
    b=int(((base_h[bi]==1)&(h[ai]==0)).sum()); c=int(((base_h[bi]==0)&(h[ai]==1)).sum())
    print(f"  {nm:26s} n_common={len(common):2d}  hit {base_h[bi].sum()}/{len(common)} -> {h[ai].sum()}/{len(common)}   +{c}/-{b}  p={mcn(b,c):.3f}")
