#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""讨论 §5.2 用的三项事实：方差分解、月间波动、阈值附近堆积（或缺失）
输入：01_data/v5/farmmonth_v2_ext.csv（三源齐全子集）
输出：01_data/v5/var_decomp.json
"""
import os, json
import numpy as np
import pandas as pd

BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
V5 = os.path.join(BASE, 'data', 'v5')
fm = pd.read_csv(os.path.join(V5, 'farmmonth_v2_ext.csv')).dropna(subset=['src1', 'src2', 'vendorF'])
a = fm[['farm_id', 'ym', 'src2']].copy()
a['ym'] = pd.PeriodIndex(a.ym, freq='M')

gm = a.src2.mean()
farm_mean = a.groupby('farm_id').src2.transform('mean')
month_mean = a.groupby('ym').src2.transform('mean')
resid = a.src2 - farm_mean - month_mean + gm

out = {
    'n_farmmonth': int(len(a)),
    'total_var': float(a.src2.var()),
    'between_farm_share': float(((farm_mean - gm) ** 2).mean() / a.src2.var()),
    'within_farm_share': float(((a.src2 - farm_mean) ** 2).mean() / a.src2.var()),
    'resid_var_after_two_way_fe': float(resid.var()),
    'resid_share': float(resid.var() / a.src2.var()),
}
b = a.sort_values(['farm_id', 'ym'])
b['lag'] = b.groupby('farm_id').src2.shift(1)
d = b.dropna(subset=['lag'])
out['lag1_autocorr'] = float(d.src2.corr(d.lag))
out['sd_month_to_month_change'] = float((d.src2 - d.lag).std())

bins = np.arange(50, 75, 1)
h, _ = np.histogram(a.src2, bins=bins)
out['hist_50_75'] = {f'{int(x)}-{int(x)+1}': int(c) for x, c in zip(bins[:-1], h)}
out['share_within_3_of_theta'] = float(((a.src2 >= 57) & (a.src2 <= 63)).mean())
out['share_within_5_of_theta'] = float(((a.src2 >= 55) & (a.src2 <= 65)).mean())

json.dump(out, open(os.path.join(V5, 'var_decomp.json'), 'w'), indent=2)
print(json.dumps({k: v for k, v in out.items() if k != 'hist_50_75'}, indent=2))
print('\n阈值附近计数 (58-59 / 59-60 / 60-61 / 61-62):',
      [out['hist_50_75'][k] for k in ['58-59', '59-60', '60-61', '61-62']])
