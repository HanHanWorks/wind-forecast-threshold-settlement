import os
import pandas as pd, numpy as np
D = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'daily_acc_panel.csv', parse_dates=['date'])
P=['acc_S01_src1','acc_S02_src2','acc_S03_limit','acc_S04_vendorF','acc_S06_scale','acc_S07_scale','acc_S08_scale','acc_S09_scale','acc_S09_smooth4','acc_S10_smooth8','acc_S11_floor05','acc_S12_clip90','acc_S13_blendY','acc_S14_med8']
g=D.groupby('date')[P].mean()
print("coverage (% days non-null):"); print((g.notna().mean()*100).round(1).to_string())
print("\n=== correlation of daily ACC (2024+) ===")
c=g.loc['2024-01-01':].corr()
print(c.round(3).to_string())
print("\n=== mean ratio to src2 and to src1 ===")
for s in P:
    x=g[s].dropna()
    if len(x)<100: continue
    r2=(x/g['acc_S02_src2'].reindex(x.index)).median()
    r1=(x/g['acc_S01_src1'].reindex(x.index)).median()
    print(f"  {s:18s} mean={x.mean():5.2f} sd={x.std():5.2f}  x/src2={r2:.3f}  x/src1={r1:.3f}")
