#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
场站月统计量的抽样噪声有多大？

背景：机制回归显示，场站月层面的系统差距 sd≈12 点，而其均值只有 3 点。
问题是：这 12 点里有多少是「不同系统真的不同」，有多少只是「一个月只有 30 天、
统计量本身就不稳」？

方法：面板里的场站月 ACC 是月内日 ACC 的均值（见 p2_v5_pipeline.py），因此
场站月差距 = 日差距序列的均值。对每个场站月，用日序列估计该均值的标准误：
    SE = sd(d) / sqrt(n) * sqrt((1+rho)/(1-rho))      rho = 日序列一阶自相关
然后把横截面方差拆成「真差异」与「抽样噪声」：
    sd_true^2 = max(0, sd_obs^2 - mean(SE^2))

输出：v5/gap_noise.json
"""
import os, json
import numpy as np
import pandas as pd

OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'v5'))
D = pd.read_csv(os.path.join(os.path.dirname(OUT), 'daily_acc_panel.csv'), dtype={'farm_id': str}, parse_dates=['date'])
D['farm_id'] = D.farm_id.str.strip()
D['ym'] = D.date.dt.to_period('M').astype(str)
D = D.rename(columns={'acc_S01_src1': 'v2_src1', 'acc_S02_src2': 'v2_src2',
                      'acc_S04_vendorF': 'v2_vendorF'})
for c in ['v2_src1', 'v2_src2', 'v2_vendorF']:
    D[c] = pd.to_numeric(D[c], errors='coerce')
D['gap'] = D.v2_src2 - D.v2_src1


def se_of_mean(x):
    x = np.asarray([v for v in x if np.isfinite(v)], float)
    n = len(x)
    if n < 20:
        return np.nan, n
    sd = x.std(ddof=1)
    if sd == 0:
        return np.nan, n
    rho = np.corrcoef(x[:-1], x[1:])[0, 1]
    rho = min(max(rho, -0.9), 0.95)
    return sd / np.sqrt(n) * np.sqrt((1 + rho) / (1 - rho)), n


rows = []
for (f, ym), g in D.groupby(['farm_id', 'ym']):
    se_g, n = se_of_mean(g.gap.values)
    se_a, _ = se_of_mean(g.v2_src2.values)
    rows.append({'farm_id': f, 'ym': ym, 'n_days': n,
                 'gap': g.gap.mean(), 'acc': g.v2_src2.mean(),
                 'se_gap': se_g, 'se_acc': se_a})
P = pd.DataFrame(rows).dropna(subset=['se_gap'])
P.to_csv(f'{OUT}/farmmonth_se.csv', index=False)

out = {'n_farm_month': int(len(P))}


def decomp(col, se_col):
    obs = P[col].dropna()
    se = P[se_col].dropna()
    sd_obs = float(obs.std(ddof=1))
    mse2 = float((se ** 2).mean())
    sd_true = float(np.sqrt(max(sd_obs ** 2 - mse2, 0)))
    return {'sd_observed': sd_obs,
            'median_se': float(se.median()),
            'mean_se': float(se.mean()),
            'sd_true_implied': sd_true,
            'noise_share_of_variance': float(min(mse2 / sd_obs ** 2, 1.0))}


out['gap'] = decomp('gap', 'se_gap')
out['acc'] = decomp('acc', 'se_acc')

# 场站月层面：|gap| 小于自身 1.96SE 的比例（即无法与零区分）
sig = (P.gap.abs() > 1.96 * P.se_gap)
out['share_gap_indistinguishable_from_zero'] = float(1 - sig.mean())
out['share_farmmonth_src1_better'] = float((P.gap < 0).mean())

# 车队月层面：把 25 站平均后，噪声是否小到可分辨 3 点
F = P.groupby('ym').agg(gap=('gap', 'mean'), se=('se_gap', 'mean'), n=('gap', 'size'))
F['se_fleet'] = F.se / np.sqrt(F.n)
out['fleet_month'] = {'sd_gap': float(F.gap.std(ddof=1)),
                      'median_se': float(F.se_fleet.median()),
                      'n_month': int(len(F)),
                      'share_positive': float((F.gap > 0).mean())}

json.dump(out, open(f'{OUT}/gap_noise.json', 'w'), ensure_ascii=False, indent=2)

print(f"场站月 {out['n_farm_month']} 个")
for k in ('gap', 'acc'):
    d = out[k]
    print(f"{k}: 观测 sd={d['sd_observed']:.2f}  中位 SE={d['median_se']:.2f}  "
          f"噪声占方差 {d['noise_share_of_variance']*100:.0f}%  隐含真 sd={d['sd_true_implied']:.2f}")
print(f"|gap| 与 0 无法区分（<1.96SE）的场站月: {out['share_gap_indistinguishable_from_zero']*100:.1f}%")
print(f"src1 更好的场站月: {out['share_farmmonth_src1_better']*100:.1f}%")
fm = out['fleet_month']
print(f"车队月: sd(gap)={fm['sd_gap']:.2f}  中位 SE={fm['median_se']:.2f}  "
      f"gap>0 的月份 {fm['share_positive']*100:.0f}% (n={fm['n_month']})")
