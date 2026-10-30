import os
import pandas as pd, numpy as np
D = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'daily_acc_panel.csv'), parse_dates=['date'])
P7=['acc_S01_src1','acc_S02_src2','acc_S04_vendorF','acc_S06_scale','acc_S09_scale','acc_S11_floor05','acc_S13_blendY']
g=D.groupby('date')[P7].mean()
wins=pd.date_range('2024-01-01','2025-03-26',freq='15D')
rows=[]
for s in wins:
    dp=g.loc[s:s+pd.Timedelta(days=89)]
    if len(dp)<85: continue
    best=dp.mean().idxmax()
    bt=g.loc[s-pd.Timedelta(days=365):s-pd.Timedelta(days=1)].mean()
    sg=g.loc[s-pd.Timedelta(days=365):s-pd.Timedelta(days=365)+pd.Timedelta(days=89)].mean()
    rows.append(dict(w=s.date().isoformat(), best=best.split('_')[1],
                     pick365=bt.idxmax().split('_')[1], pickS=sg.idxmax().split('_')[1],
                     h365=int(bt.idxmax()==best), hS=int(sg.idxmax()==best),
                     bt_gap=round(bt.nlargest(2).iloc[0]-bt.nlargest(2).iloc[1],2)))
T=pd.DataFrame(rows)
print(T.to_string(index=False))
print("\nwhere S365 gains over T365:", T[(T.hS==1)&(T.h365==0)].w.tolist())
print("where S365 loses:", T[(T.hS==0)&(T.h365==1)].w.tolist())
print("\npick distribution T365:",T.pick365.value_counts().to_dict())
print("pick distribution S365:",T.pickS.value_counts().to_dict())
print("best distribution:",T.best.value_counts().to_dict())
