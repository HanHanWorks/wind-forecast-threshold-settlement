#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P2 v5 流水线：G1（官方口径 ACC）+ G3（铰链考核电量）+ G4（分解与分诊）+ G5（合同价值）

在服务器上运行：
    ~/anaconda3/bin/python p2_v5_pipeline.py

产出（写到 $P2_OUT，默认仓库 data/v5/）：
  daily_acc_v1_v2.csv   日级 ACC，两种口径（v1=现行；v2=排除受限时段及后 1h）
  farmmonth.csv         场站月：ACC、月度装机、铰链考核量
  summary.json          份额、亏欠、集中度、合同价值

口径说明：
- ACC 公式沿用现行实现：d = max(PM, 0.2*Cap_static)，ACC = (1 - RMSE((PM-PP)/d)) * 100
- 受限代理：源1 的 predict_limit_power < predict_power（限电修正下调的时刻）
  G0 已证：limit 与 predict 在 86% 的点上完全相同，12.2% 为下调，1.8% 为上抬
  → limit < predict 可作"预期受限"的代理标记
- v2 在 v1 基础上排除：受限点 + 其后 1 小时（4 个 15min 步长），对所有系统同时排除
- 考核量两种约定（绝对量级待定，份额与形状不受影响）：
     A（按月一次性）  MWh = Cap_MW * deficit_points * k
     B（按日累加）    MWh = Cap_MW * deficit_points * k * 天数
  k=0.2，阈值 60
"""
import os, glob, json
import numpy as np
import pandas as pd

R = os.environ['P2_RAW']
S = R + '/2原始数据/3Second_data'
V = R + '/2原始数据/5风电光伏分开的预测值2022-2025'
OUT = os.environ.get('P2_OUT', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'v5'))
os.makedirs(OUT, exist_ok=True)

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


def read_vendor(fn):
    if not os.path.exists(fn):
        return None
    d = pd.read_csv(fn, usecols=['farm_id', 'data_time', 'predict_power', 'data_source'],
                    dtype={'farm_id': str, 'data_source': str}, parse_dates=['data_time'])
    d['farm_id'] = d.farm_id.str.strip()
    if d.data_source.notna().any():
        ds = d.data_source.astype(str).str.strip()
        d = d[ds == ds.value_counts().index[0]]
    d = d.drop_duplicates(['farm_id', 'data_time'])
    d['predict_power'] = pd.to_numeric(d.predict_power, errors='coerce')
    return d[['farm_id', 'data_time', 'predict_power']]


def build_year(year, cap):
    real = pd.read_csv(f'{S}/75-电站实际功率{year}-bs_data_real_fifteen_{year}.csv',
                       usecols=['farm_id', 'data_time', 'real_power'],
                       dtype={'farm_id': str}, parse_dates=['data_time'])
    real['farm_id'] = real.farm_id.str.strip()
    real['PM'] = pd.to_numeric(real.real_power, errors='coerce')
    real = real.drop_duplicates(['farm_id', 'data_time'])[['farm_id', 'data_time', 'PM']]

    b = pd.read_csv(f'{S}/81-短期预测功率表{year}-bs_data_short_power_{year}.csv',
                    usecols=['farm_id', 'data_time', 'predict_power', 'data_source', 'predict_limit_power'],
                    dtype={'farm_id': str, 'data_source': str}, parse_dates=['data_time'])
    b['farm_id'] = b.farm_id.str.strip()
    b['ds'] = b.data_source.astype(str).str.strip()
    for c in ['predict_power', 'predict_limit_power']:
        b[c] = pd.to_numeric(b[c], errors='coerce')
    b = b.drop_duplicates(['farm_id', 'data_time', 'ds'])

    s1 = b[b.ds == '1'][['farm_id', 'data_time', 'predict_power', 'predict_limit_power']] \
        .rename(columns={'predict_power': 'src1', 'predict_limit_power': 'limit'})
    s2 = b[b.ds == '2'][['farm_id', 'data_time', 'predict_power']].rename(columns={'predict_power': 'src2'})
    vF = read_vendor(f'{V}/bs_data_short_power_{year}F.csv')
    vF = vF.rename(columns={'predict_power': 'vendorF'}) if vF is not None else None

    m = real.merge(s1, on=['farm_id', 'data_time'], how='inner')
    m = m.merge(s2, on=['farm_id', 'data_time'], how='left')
    if vF is not None:
        m = m.merge(vF, on=['farm_id', 'data_time'], how='left')
    else:
        m['vendorF'] = np.nan
    m = m.merge(cap, on='farm_id', how='inner')
    m = m[m.PM >= 0].sort_values(['farm_id', 'data_time'])

    # 受限代理：limit < predict（仅源1 有 limit）
    m['restr'] = (m.limit.notna()) & (m.limit < m.src1 - 1e-6)
    m['restr'] = m.restr.astype(float)
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
    return pd.DataFrame(rows)


def main():
    cap = cap_static()
    print(f'EE 场站 {len(cap)} 站，总装机 {cap.Cap.sum():.1f} MW')
    parts = []
    for y in [2023, 2024, 2025]:
        print(f'=== {y} ===', flush=True)
        d = build_year(y, cap)
        print(f'  日级行数 {len(d):,}  站 {d.farm_id.nunique()}  受限点占比 {d.restr_share.mean()*100:.2f}%', flush=True)
        parts.append(d)
    daily = pd.concat(parts, ignore_index=True)
    daily.to_csv(f'{OUT}/daily_acc_v1_v2.csv', index=False)
    print(f'\n日级面板 {len(daily):,} 行 → daily_acc_v1_v2.csv')

    for c in ['src1', 'src2', 'vendorF']:
        print(f'  {c:8s} v1 均值 {daily[f"v1_{c}"].mean():6.2f}  v2 均值 {daily[f"v2_{c}"].mean():6.2f}  '
              f'差 {(daily[f"v2_{c}"]-daily[f"v1_{c}"]).mean():+.2f}  有效 {daily[f"v2_{c}"].notna().mean()*100:.1f}%')

    # ---------- 场站月 ----------
    mc = pd.read_csv(CAPTBL)
    mc['farm_id'] = mc.farm_id.astype(str).str.strip()
    mc['ym'] = mc.month.astype(str)
    mc = mc[['farm_id', 'ym', 'Cap_MW']]
    # 全局静态装机（来自 filtered_56_farm），用于月度表未覆盖的月份（2023 全部 + 2025-10 之后）
    stat = cap.rename(columns={'Cap': 'Cap_stat_global'})

    for tag in ['v1', 'v2']:
        d = daily.copy()
        d['ym'] = d.date.dt.to_period('M').astype(str)
        cols = [f'{tag}_src1', f'{tag}_src2', f'{tag}_vendorF']
        fm = d.groupby(['ym', 'farm_id'])[cols].mean().reset_index()
        fm.columns = ['ym', 'farm_id', 'src1', 'src2', 'vendorF']
        fm = fm.dropna(subset=['src1', 'src2'])
        fm = fm.merge(mc, on=['farm_id', 'ym'], how='left')
        fm = fm.merge(stat, on='farm_id', how='left')
        fm['Cap'] = fm.Cap_MW.fillna(fm.Cap_stat_global)          # 月度优先，缺失回退全局静态
        fm['days'] = fm.ym.map(lambda s: pd.Period(s).days_in_month)
        fm['cap_src'] = np.where(fm.Cap_MW.notna(), 'monthly', 'static_fallback')
        n_missing = int(fm.Cap.isna().sum())
        if n_missing:
            print(f'  ⚠ 仍有 {n_missing} 个场站月无容量，已剔除')
            fm = fm.dropna(subset=['Cap'])

        fm['best'] = fm[['src1', 'src2', 'vendorF']].max(axis=1)
        fm['n_pass'] = (fm[['src1', 'src2', 'vendorF']] >= THETA).sum(axis=1)
        for c in ['src1', 'src2', 'vendorF']:
            fm[f'def_{c}'] = np.maximum(0, THETA - fm[c])
            fm[f'E_{c}'] = fm.Cap * fm[f'def_{c}'] * K          # MW·point·0.2  (约定A)
            fm[f'EB_{c}'] = fm[f'E_{c}'] * fm.days              # 约定B
        fm.to_csv(f'{OUT}/farmmonth_{tag}.csv', index=False)

        print(f'\n===== 场站月（{tag}）：{len(fm):,} 个，月度容量命中 {100*(fm.cap_src=="monthly").mean():.1f}% =====')
        print(f'  src2 达标            {100*(fm.src2>=THETA).mean():5.1f}%')
        print(f'  三源全部达标          {100*(fm.n_pass==3).mean():5.1f}%')
        print(f'  最优达标且 src2 未达标 {100*((fm.best>=THETA)&(fm.src2<THETA)).mean():5.1f}%')
        print(f'  三源全部未达标        {100*(fm.n_pass==0).mean():5.1f}%')
        for c in ['src1', 'src2', 'vendorF']:
            print(f'  {c:8s} 均值ACC {fm[c].mean():6.2f}  年均亏欠点·站 {fm[f"def_{c}"].mean()*12:7.2f}  '
                  f'考核量A(万MWh) {fm[f"E_{c}"].sum()/1e4:8.1f}  B {fm[f"EB_{c}"].sum()/1e4:9.1f}')

        # 集中度：src2 的考核量洛伦兹
        e = fm.E_src2.sort_values(ascending=False).values
        if e.sum() > 0:
            cum = np.cumsum(e) / e.sum()
            for q in [0.1, 0.2, 0.5]:
                k = max(1, int(len(e) * q))
                print(f'    前 {int(q*100)}% 场站月贡献 src2 考核量的 {100*cum[k-1]:5.1f}%')

    # ---------- 合同价值 ----------
    fm = pd.read_csv(f'{OUT}/farmmonth_v2.csv')
    save_A = (fm.E_src1.sum() - fm.E_src2.sum())
    save_B = (fm.EB_src1.sum() - fm.EB_src2.sum())
    months = fm.ym.nunique()
    summary = {
        'n_farmmonth': int(len(fm)), 'months': int(months),
        'shares_v1': {'src2_pass': float((pd.read_csv(f'{OUT}/farmmonth_v1.csv').src2 >= THETA).mean())},
        'shares_v2': {
            'src2_pass': float((fm.src2 >= THETA).mean()),
            'all_pass': float((fm.n_pass == 3).mean()),
            'live_cell': float(((fm.best >= THETA) & (fm.src2 < THETA)).mean()),
            'all_fail': float((fm.n_pass == 0).mean()),
        },
        'mean_acc': {c: float(fm[c].mean()) for c in ['src1', 'src2', 'vendorF']},
        'switch_src1_to_src2': {
            'GWh_per_year_A': float(save_A / months * 12 / 1e3),
            'GWh_per_year_B': float(save_B / months * 12 / 1e3),
            'total_MWh_A': float(save_A), 'total_MWh_B': float(save_B),
        },
        'per_point_month_MWh_A': float(fm.Cap.sum() / len(fm) * K),
    }
    json.dump(summary, open(f'{OUT}/summary.json', 'w'), ensure_ascii=False, indent=2)
    print('\n===== 汇总 =====')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
