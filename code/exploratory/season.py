import os
import pandas as pd, numpy as np
D = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'daily_acc_panel.csv'), parse_dates=['date'])
A='acc_S02_src2'; B='acc_S06_scale'
g=D.groupby('date')[[A,B]].mean()
d=(g[A]-g[B]).dropna()
print("daily diff: n=%d mean=%+.3f sd=%.3f  range [%.2f, %.2f]"%(len(d),d.mean(),d.std(),d.min(),d.max()))
# 30-day centred smoothing for a readable seasonal curve
sm=d.rolling(30,center=True,min_periods=20).mean()
print("\nH1 vs H2 means (daily diff):")
for y in [2023,2024,2025]:
    h1=d[(d.index.year==y)&(d.index.month<=6)]; h2=d[(d.index.year==y)&(d.index.month>6)]
    print(f"  {y}: H1 {h1.mean():+.2f} (n={len(h1)})   H2 {h2.mean():+.2f} (n={len(h2)})" if len(h2) else f"  {y}: H1 {h1.mean():+.2f} (n={len(h1)})   H2 n/a")
print("\nmonthly means:")
print(d.groupby([d.index.year,d.index.month]).mean().round(2).to_string())
# autocorrelation vs lag
print("\nautocorrelation of the DAILY diff series by lag:")
for lag in [15,30,60,90,120,180,270,365,450,540,730]:
    x=d.values[:-lag]; y=d.values[lag:]
    x=x-np.nanmean(x); y=y-np.nanmean(y)
    print(f"  lag {lag:3d}d: r={np.sum(x*y)/np.sqrt(np.sum(x*x)*np.sum(y*y)):+.3f}")
# same for the 30-day smoothed
s=sm.dropna()
print("\nautocorrelation of 30d-smoothed diff:")
for lag in [90,180,365,730]:
    x=s.values[:-lag]; y=s.values[lag:]
    x=x-x.mean(); y=y-y.mean()
    print(f"  lag {lag:3d}d: r={np.sum(x*y)/np.sqrt(np.sum(x*x)*np.sum(y*y)):+.3f}")
