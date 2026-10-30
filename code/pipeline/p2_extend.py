#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把面板从 2025-06-24 延到 2025-09-01（用 新能源数据20250901 这个较新的导出）
做法：只算 2025-06-01..2025-09-01 的增量，口径与 p2_v5_pipeline 完全一致，
      再与既有 daily 面板合并（重叠期以新导出为准）。
输出：v5/daily_acc_v1_v2_ext.csv, v5/farmmonth_v2_ext.csv, v5/summary_ext.json
"""
import os, json
import numpy as np
import pandas as pd

R = os.environ['P2_RAW']
NEW = R + '/2原始数据/新能源数据20250901'
V = R + '/2原始数据/5风电光伏分开的预测值2022-2025'
OUT = os.environ.get('P2_OUT', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'v5'))
THETA, K = 60.0, 0.2
CAPTBL = os.environ.get('P2_CAPTBL', os.path.join(R, 'monthly_capacity.csv'))


def cap_static():
    c = pd.read_csv(R + '/4处理后数据/filtered_56_farm.csv')
    c.columns = [x.strip().lstrip('\ufeff') for x in c.columns]
    c['farm_id'] = c['farm_id'].astype(str).str.strip()
    c['Cap'] = pd.to_numeric(c['capability'].astype(str).str.strip(" '"), errors='coerce')
    c['kind'] = c['farm_no'].astype(str).str.strip(" '").str[:2]
    return c[(c.Cap > 10) & (c.kind == 'EE')][['farm_id', 'Cap']].reset_index(drop=True)


def acc_of(PM, PP, Cap):
    PM = np.asarray(PM, float); PP = np.asarray(PP, float)
    d = np.where(PM >= 0.2 * Cap, PM, 0.2 * Cap)
    d = np.where(d == 0, np.nan, d)
    e = (PM - PP) / d
    e = e[~np.isnan(e)]
    if len(e) < 90:
        return np.nan
    return (1 - np.sqrt((e ** 2).mean())) * 100.0


def main():
    cap = cap_static()
    real = pd.read_csv(f'{NEW}/bs_data_real_fifteen_2025.csv',
                       usecols=['farm_id', 'data_time', 'real_power'],
                       dtype={'farm_id': str}, parse_dates=['data_time'])
    real['farm_id'] = real.farm_id.str.strip()
    real['PM'] = pd.to_numeric(real.real_power, errors='coerce')
    real = real.drop_duplicates(['farm_id', 'data_time'])

    sp = pd.read_csv(f'{NEW}/bs_data_short_power_2025.csv',
                     usecols=['farm_id', 'data_time', 'predict_power', 'data_source',
                              'predict_limit_power'],
                     dtype={'farm_id': str, 'data_source': str}, parse_dates=['data_time'])
    sp['farm_id'] = sp.farm_id.str.strip()
    sp['ds'] = sp.data_source.astype(str).str.strip()
    for c in ['predict_power', 'predict_limit_power']:
        sp[c] = pd.to_numeric(sp[c], errors='coerce')
    sp = sp.drop_duplicates(['farm_id', 'data_time', 'ds'])

    s1 = sp[sp.ds == '1'][['farm_id', 'data_time', 'predict_power', 'predict_limit_power']] \
        .rename(columns={'predict_power': 'src1', 'predict_limit_power': 'limit'})
    s2 = sp[sp.ds == '2'][['farm_id', 'data_time', 'predict_power']].rename(columns={'predict_power': 'src2'})

    vf = None
    p = f'{V}/bs_data_short_power_2025F.csv'
    if os.path.exists(p):
        d = pd.read_csv(p, usecols=['farm_id', 'data_time', 'predict_power', 'data_source'],
                        dtype={'farm_id': str, 'data_source': str}, parse_dates=['data_time'])
        d['farm_id'] = d.farm_id.str.strip()
        if d.data_source.notna().any():
            ds = d.data_source.astype(str).str.strip()
            d = d[ds == ds.value_counts().index[0]]
        d['predict_power'] = pd.to_numeric(d.predict_power, errors='coerce')
        vf = d.drop_duplicates(['farm_id', 'data_time'])[['farm_id', 'data_time', 'predict_power']] \
            .rename(columns={'predict_power': 'vendorF'})

    m = real.merge(s1, on=['farm_id', 'data_time'], how='inner')
    m = m.merge(s2, on=['farm_id', 'data_time'], how='left')
    m = m.merge(vf, on=['farm_id', 'data_time'], how='left') if vf is not None else m.assign(vendorF=np.nan)
    m = m.merge(cap, on='farm_id', how='inner')
    m = m[m.PM >= 0].sort_values(['farm_id', 'data_time'])
    print(f'增量原始点 {len(m):,}，时间 {m.data_time.min()} .. {m.data_time.max()}，站 {m.farm_id.nunique()}')

    m['restr'] = ((m.limit.notna()) & (m.limit < m.src1 - 1e-6)).astype(float)
    g = m.groupby('farm_id')['restr']
    m['restr_flag'] = (g.transform(lambda s: s.rolling(4, min_periods=1).max()) > 0)
    m['day'] = m.data_time.dt.normalize()

    rows = []
    for (fid, day), grp in m.groupby(['farm_id', 'day'], sort=False):
        if len(grp) < 90:
            continue
        C = float(grp.Cap.iloc[0])
        rec = {'date': day, 'farm_id': fid, 'n_pts': len(grp),
               'restr_share': float(grp.restr_flag.mean())}
        keep = grp[~grp.restr_flag]
        for c in ['src1', 'src2', 'vendorF']:
            rec[f'v1_{c}'] = acc_of(grp.PM, grp[c], C)
            rec[f'v2_{c}'] = acc_of(keep.PM, keep[c], C)
        rows.append(rec)
    inc = pd.DataFrame(rows)
    print(f'增量日级行 {len(inc):,}（{inc.date.min().date()} .. {inc.date.max().date()}）')

    old = pd.read_csv(f'{OUT}/daily_acc_v1_v2.csv', parse_dates=['date'])
    old['farm_id'] = old.farm_id.astype(str).str.strip()
    inc['farm_id'] = inc.farm_id.astype(str).str.strip()
    for c in ['v1_src1', 'v1_src2', 'v1_vendorF', 'v2_src1', 'v2_src2', 'v2_vendorF']:
        if c in old.columns:
            old[c] = pd.to_numeric(old[c], errors='coerce')
        if c in inc.columns:
            inc[c] = pd.to_numeric(inc[c], errors='coerce')
    old = old[old.date < inc.date.min()]
    ext = pd.concat([old, inc], ignore_index=True).drop_duplicates(['date', 'farm_id'], keep='last')
    ext.to_csv(f'{OUT}/daily_acc_v1_v2_ext.csv', index=False)
    print(f'合并后日级 {len(ext):,} 行（{ext.date.min().date()} .. {ext.date.max().date()}）')

    # 场站月
    mc = pd.read_csv(CAPTBL)
    mc['farm_id'] = mc.farm_id.astype(str).str.strip()
    mc['ym'] = mc.month.astype(str)
    mc = mc[['farm_id', 'ym', 'Cap_MW']]
    stat = cap.rename(columns={'Cap': 'Cap_stat_global'})

    d = ext.copy()
    d['ym'] = d.date.dt.to_period('M').astype(str)
    fm = d.groupby(['ym', 'farm_id'])[['v2_src1', 'v2_src2', 'v2_vendorF']].mean().reset_index()
    fm.columns = ['ym', 'farm_id', 'src1', 'src2', 'vendorF']
    fm = fm.dropna(subset=['src1', 'src2'])
    fm = fm.merge(mc, on=['farm_id', 'ym'], how='left').merge(stat, on='farm_id', how='left')
    print(f'  分组后 {len(fm)} 行，ym 范围 {fm.ym.min()} .. {fm.ym.max()}')
    fm['Cap'] = fm.Cap_MW.fillna(fm.Cap_stat_global)
    fm['days'] = fm.ym.map(lambda s: pd.Period(s).days_in_month)
    fm['cap_src'] = np.where(fm.Cap_MW.notna(), 'monthly', 'static_fallback')
    fm = fm.dropna(subset=['Cap'])
    fm['best'] = fm[['src1', 'src2', 'vendorF']].max(axis=1)
    fm['n_pass'] = (fm[['src1', 'src2', 'vendorF']] >= THETA).sum(axis=1)
    for c in ['src1', 'src2', 'vendorF']:
        fm[f'def_{c}'] = np.maximum(0, THETA - fm[c])
        fm[f'E_{c}'] = fm.Cap * fm[f'def_{c}'] * K
    fm.to_csv(f'{OUT}/farmmonth_v2_ext.csv', index=False)

    full = fm.dropna(subset=['vendorF'])
    print(f'\n场站月 {len(fm)}（三源齐全 {len(full)}），{fm.ym.nunique()} 个月，{fm.farm_id.nunique()} 站')
    for tag, x in [('全部', fm), ('三源齐全', full)]:
        print(f'  [{tag}] src2达标 {100*(x.src2>=THETA).mean():5.1f}%  三源全达标 {100*(x.n_pass==3).mean():5.1f}%  '
              f'有价格 {100*((x.best>=THETA)&(x.src2<THETA)).mean():5.1f}%  全不达标 {100*(x.n_pass==0).mean():5.1f}%')

    s = {
        'n_farmmonth': int(len(fm)), 'n_farmmonth_full3': int(len(full)),
        'months': int(fm.ym.nunique()), 'farms': int(fm.farm_id.nunique()),
        'period': [str(fm.ym.min()), str(fm.ym.max())],
        'shares_full3': {
            'src2_pass': float((full.src2 >= THETA).mean()),
            'all_pass': float((full.n_pass == 3).mean()),
            'live_cell': float(((full.best >= THETA) & (full.src2 < THETA)).mean()),
            'all_fail': float((full.n_pass == 0).mean()),
        },
        'assessed_GWh_total': {c: float(fm['E_' + c].sum() / 1e3) for c in ['src1', 'src2', 'vendorF']},
        'switch_GWh_per_year': float((full.E_src1.sum() - full.E_src2.sum()) / full.ym.nunique() * 12 / 1e3),
    }
    json.dump(s, open(f'{OUT}/summary_ext.json', 'w'), ensure_ascii=False, indent=2)
    print(json.dumps(s, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
