#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
机制检验：结算衡量的是天气，还是系统？

设计要点
--------
天气无法直接观测到站级，而测风塔/理论功率表用的是另一套编号（与 25 站面板无交集）。
因此用「他站实测出力」作为本站天气的代理：同省同月的气象系统是共同的，别的场站
当月的出力统计量能代表本站当月的资源状态，而**完全不进入本站 ACC 的算术**，
避免了用本站 real_power 解释本站 ACC 的循环论证。

回归（均含场站固定效应，标准误按月份聚类）
  A1  acc ~ farm FE                         基准
  A2  acc ~ farm FE + month FE              共同冲击（天气）能解释多少
  A3  acc ~ farm FE + W_loo                 他站资源变量
  B1  gap ~ farm FE                         gap 是否只是场站级的常数位移
  B2  gap ~ farm FE + month FE
  B3  gap ~ farm FE + W_loo

判据：若 A3 的资源块显著、B3 的不显著，且 gap 的组内标准差远小于 acc 的组内标准差，
则「月度考核的量由资源决定，系统选择只贡献一个近乎常数的小位移」成立。

输出：v5/realmonth_stats.csv, v5/mechanism_reg2.json
"""
import os, json
import numpy as np
import pandas as pd

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
RAW = os.environ.get('P2_RAW', os.path.join(ROOT, 'data', 'raw'))
S = os.path.join(RAW, 'second')                 # raw 15-min forecast/actual series
STATIC = os.path.join(RAW, 'farm_static.csv')   # farm id -> capacity mapping
CAPTBL = os.path.join(RAW, 'monthly_capacity.csv')
OUT = os.path.join(ROOT, 'data', 'v5')
FM = f'{OUT}/farmmonth_v2_ext.csv'


def static_cap():
    c = pd.read_csv(STATIC)
    c.columns = [x.strip().lstrip('\ufeff') for x in c.columns]
    c['farm_id'] = c['farm_id'].astype(str).str.strip()
    c['Cap'] = pd.to_numeric(c['capability'].astype(str).str.strip(" '"), errors='coerce')
    c['kind'] = c['farm_no'].astype(str).str.strip(" '").str[:2]
    return c[(c.Cap > 10) & (c.kind == 'EE')][['farm_id', 'Cap']].reset_index(drop=True)


def real_month(year, farms):
    fn = f'{S}/75-电站实际功率{year}-bs_data_real_fifteen_{year}.csv'
    d = pd.read_csv(fn, usecols=['farm_id', 'data_time', 'real_power'],
                    dtype={'farm_id': str}, parse_dates=['data_time'])
    d['farm_id'] = d.farm_id.str.strip()
    d = d[d.farm_id.isin(farms)]
    d['PM'] = pd.to_numeric(d.real_power, errors='coerce')
    d = d.dropna(subset=['PM']).drop_duplicates(['farm_id', 'data_time'])
    d = d.sort_values(['farm_id', 'data_time'])
    d['dPM'] = d.groupby('farm_id')['PM'].diff().abs()
    d['ym'] = d.data_time.dt.to_period('M').astype(str)
    g = d.groupby(['farm_id', 'ym'])
    out = pd.DataFrame({
        'pm_mean': g.PM.mean(),
        'pm_sd': g.PM.std(),
        'pm_p95': g.PM.quantile(0.95),
        'pm_ramp': g.dPM.mean(),
        'pm_calm': g.PM.apply(lambda s: float((s < 3).mean())),   # <3 MW 近似静风（站均装机 120MW）
        'n_pts': g.PM.size(),
    }).reset_index()
    print(f'  {year}: {len(out)} 场站月, 站 {out.farm_id.nunique()}')
    return out


cap = static_cap()
fm = pd.read_csv(FM, dtype={'farm_id': str})
fm['farm_id'] = fm.farm_id.astype(str).str.strip()
farms = set(fm.farm_id.unique())

print('读取实测出力…')
R = pd.concat([real_month(y, farms) for y in (2023, 2024, 2025)], ignore_index=True)

# 容量：月度优先，回退静态
mc = pd.read_csv(CAPTBL, dtype={'farm_id': str})
mc['farm_id'] = mc.farm_id.astype(str).str.strip()
mc['ym'] = mc.month.astype(str)
mc = mc[['farm_id', 'ym', 'Cap_MW']]
R = R.merge(mc, on=['farm_id', 'ym'], how='left').merge(cap.rename(columns={'Cap': 'Cap0'}), on='farm_id', how='left')
R['Capr'] = R.Cap_MW.fillna(R.Cap0)
R = R.dropna(subset=['Capr'])
R = R[R.Capr > 10]

# 资源状态量（除以容量，消除规模效应）
R['cf'] = R.pm_mean / R.Capr
R['cf_sd'] = R.pm_sd / R.Capr
R['cf_p95'] = R.pm_p95 / R.Capr
R['ramp'] = R.pm_ramp / R.Capr
R['calm'] = R.pm_calm
R.to_csv(f'{OUT}/realmonth_stats.csv', index=False)
print(f'实测量 {len(R)} 场站月，站 {R.farm_id.nunique()}')

# ---------- 他站（leave-one-out）月度资源代理 ----------
rows = []
for ym, g in R.groupby('ym'):
    n = len(g)
    if n < 4:
        continue
    for _, r in g.iterrows():
        o = g[g.farm_id != r.farm_id]
        if len(o) < 3:
            continue
        rows.append({'farm_id': r.farm_id, 'ym': ym,
                     'W_cf': o.cf.mean(), 'W_cf_sd': o.cf_sd.mean(),
                     'W_p95': o.cf_p95.mean(), 'W_ramp': o.ramp.mean(),
                     'W_calm': o.calm.mean(), 'n_others': len(o)})
W = pd.DataFrame(rows)

M = fm.merge(W, on=['farm_id', 'ym'], how='inner').dropna(subset=['src1', 'src2', 'W_cf'])
M['gap'] = M.src2 - M.src1
M['moy'] = M.ym.str[-2:].astype(int)
print(f'合并后 {len(M)} 场站月，站 {M.farm_id.nunique()}，月 {M.ym.nunique()}')
M.to_csv(f'{OUT}/mechanism_panel.csv', index=False)

WCOLS = ['W_cf', 'W_cf_sd', 'W_ramp', 'W_calm']


def design(df, cols, month_fe=False):
    blocks = [pd.get_dummies(df.farm_id, prefix='f', drop_first=True).astype(float)]
    if month_fe:
        blocks.append(pd.get_dummies(df.moy, prefix='m', drop_first=True).astype(float))
    X = pd.concat(blocks, axis=1)
    for c in cols:
        X[c] = df[c].values
    X['const'] = 1.0
    return X


def fit(y, X, groups):
    Xv = X.values.astype(float)
    yv = np.asarray(y, float)
    XtX = Xv.T @ Xv
    XtXi = np.linalg.pinv(XtX)
    beta = XtXi @ (Xv.T @ yv)
    u = yv - Xv @ beta
    n, k = Xv.shape
    sse = float(u @ u)
    sst = float(((yv - yv.mean()) ** 2).sum())
    r2 = 1 - sse / sst
    # 按月份聚类的稳健标准误
    meat = np.zeros((k, k))
    G = 0
    for _, idx in pd.Series(np.arange(n)).groupby(groups.values):
        ii = idx.values
        Xg = Xv[ii]
        ug = u[ii]
        s = Xg.T @ ug
        meat += np.outer(s, s)
        G += 1
    c = G / (G - 1) * (n - 1) / (n - k)
    V = c * XtXi @ meat @ XtXi
    se = np.sqrt(np.maximum(np.diag(V), 0))
    r2adj = 1 - (1 - r2) * (n - 1) / (n - k)
    return dict(beta=beta, se=se, r2=r2, r2adj=r2adj, sse=sse, n=n, k=k, G=G)


def wald_block(fit_res, X, cols):
    names = list(X.columns)
    idx = [names.index(c) for c in cols]
    b = fit_res['beta'][idx]
    # 逐系数 t（聚类稳健）
    se = fit_res['se'][idx]
    t = b / se
    return {c: {'beta': float(bb), 'se': float(ss), 't': float(tt)}
            for c, bb, ss, tt in zip(cols, b, se, t)}


res = {}
for tag, ycol in [('acc_incumbent', 'src2'), ('gap', 'gap')]:
    y = M[ycol].values
    specs = {
        'farm_FE': design(M, []),
        'farm_month_FE': design(M, [], month_fe=True),
        'farm_FE_weather': design(M, WCOLS),
    }
    block = {'n': int(len(y)), 'mean': float(y.mean()), 'sd': float(y.std()),
             'n_farm': int(M.farm_id.nunique()), 'n_month': int(M.ym.nunique())}
    # 组内（去场站均值）标准差
    dm = y - pd.Series(y).groupby(M.farm_id.values).transform('mean').values
    block['sd_within_farm'] = float(np.std(dm, ddof=1))
    for sname, X in specs.items():
        f = fit(y, X, M.ym)
        block[sname] = {'r2': f['r2'], 'r2adj': f['r2adj'], 'k': f['k'], 'G': f['G']}
        if sname == 'farm_FE_weather':
            block['weather'] = wald_block(f, X, WCOLS)
            block['delta_r2_weather'] = float(f['r2'] - block['farm_FE']['r2'])
    block['delta_r2_monthFE'] = float(block['farm_month_FE']['r2'] - block['farm_FE']['r2'])
    res[tag] = block

# 系统位移是否恒定：把 src2 对 src1 回归（含场站 FE），斜率≈1 说明只是位移
Xg = design(M, ['src1'])
fg = fit(M.src2.values, Xg, M.ym)
slope = float(fg['beta'][list(Xg.columns).index('src1')])
res['level_shift'] = {'slope_src2_on_src1': slope,
                      'se': float(fg['se'][list(Xg.columns).index('src1')]),
                      'r2': float(fg['r2'])}

json.dump(res, open(f'{OUT}/mechanism_reg2.json', 'w'), ensure_ascii=False, indent=2)

print('\n' + '=' * 76)
for tag in ('acc_incumbent', 'gap'):
    b = res[tag]
    print(f"\n{tag}: n={b['n']}  farm={b['n_farm']}  month={b['n_month']}  "
          f"mean={b['mean']:.2f}  sd={b['sd']:.2f}  sd_within={b['sd_within_farm']:.2f}")
    for s in ('farm_FE', 'farm_month_FE', 'farm_FE_weather'):
        print(f"   {s:18s} R2={b[s]['r2']:.3f}  adjR2={b[s]['r2adj']:.3f}  k={b[s]['k']}")
    print(f"   Δ R2(month FE) = {b['delta_r2_monthFE']:+.3f}   Δ R2(weather) = {b['delta_r2_weather']:+.3f}")
    print('   weather: ' + ', '.join(f"{c} t={d['t']:+.2f} (b={d['beta']:+.3f})"
                                     for c, d in b['weather'].items()))
print(f"\nlevel shift: src2 = {res['level_shift']['slope_src2_on_src1']:.3f} * src1 "
      f"(se={res['level_shift']['se']:.3f}, R2={res['level_shift']['r2']:.3f})")
print(f"\n已写出 {OUT}/mechanism_reg2.json")
