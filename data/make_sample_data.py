#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate a synthetic, schema-compatible sample of the analysis data.

The real record behind the paper is covered by a data-sharing agreement with the
provincial dispatch centre and cannot be redistributed.  This script fabricates
data with the same files, columns and value ranges so that every script in
``code/`` runs end to end without the confidential record.  Nothing written here
resembles real plants, real forecasts or real settlements.

Files written (all git-ignored):
    data/daily_acc_panel.csv          daily accuracy of every series, per farm-day
    data/v5/farmmonth_v2_ext.csv      farm-month ledger (accuracy, capacity, assessed energy)
    data/v5/farmmonth_se.csv          per farm-month standard errors
    data/v5/realmonth_stats.csv       monthly output statistics of the fleet
    data/v5/mechanism_panel.csv       farm-month ledger plus weather-proxy variables
    data/v5/mechanism_reg2.json       regression summary stub (schema only)

Usage:
    python data/make_sample_data.py [--force]
"""
import os
import json
import calendar
import argparse
import numpy as np
import pandas as pd

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
DATA = os.path.join(ROOT, 'data')
V5 = os.path.join(DATA, 'v5')

THETA, K = 60.0, 0.2
SEED = 20261030
N_FARMS = 8
MONTHS = pd.period_range('2023-01', '2025-08', freq='M').astype(str).tolist()

# which accuracy series exist in the daily panel (column suffixes)
SERIES = ['acc_S01_src1', 'acc_S02_src2', 'acc_S03_limit', 'acc_S04_vendorF',
          'acc_S05_vendorG', 'acc_S06_scale', 'acc_S07_scale', 'acc_S08_scale',
          'acc_S09_scale', 'acc_S09_smooth4', 'acc_S10_smooth8', 'acc_S11_floor05',
          'acc_S12_clip90', 'acc_S13_blendY', 'acc_S14_med8']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--force', action='store_true', help='overwrite existing sample files')
    args = ap.parse_args()

    os.makedirs(V5, exist_ok=True)
    daily_path = os.path.join(DATA, 'daily_acc_panel.csv')
    if os.path.exists(daily_path) and not args.force:
        print('sample data already present, use --force to regenerate')
        return

    rng = np.random.default_rng(SEED)
    farms = [f'SAMPLE{i:03d}' for i in range(1, N_FARMS + 1)]
    # capacities (MW); farm 1 joins late, the rest at the start
    cap0 = dict(zip(farms, rng.uniform(45, 240, N_FARMS).round(1)))
    first_month = {f: 0 for f in farms}
    first_month['SAMPLE001'] = 10          # commissioned Nov 2023
    first_month['SAMPLE002'] = 4

    # per-farm and per-month effects
    f_eff = dict(zip(farms, rng.normal(0, 3.0, N_FARMS)))
    m_eff = {m: rng.normal(0, 2.5) for m in MONTHS}
    m_res = {m: rng.normal(0, 1.0) for m in MONTHS}   # month resource state

    # ------------------------------------------------------------- daily panel
    def month_days(m):
        y, mo = int(m[:4]), int(m[5:7])
        return pd.date_range('%04d-%02d-01' % (y, mo),
                             periods=calendar.monthrange(y, mo)[1], freq='D')

    recs = []
    for m in MONTHS:
        days = month_days(m)
        for f in farms:
            if MONTHS.index(m) < first_month[f]:
                continue
            for d in days:
                if rng.random() < 0.03:          # occasional missing day
                    continue
                base = 57.0 + f_eff[f] + m_eff[m] + rng.normal(0, 8.0)
                s2 = float(np.clip(base, -60, 100))
                s1 = float(np.clip(s2 + rng.normal(-3.0, 5.5), -70, 100))
                vf = s1 if rng.random() < 0.92 else s1 + rng.normal(0, 2.0)
                rec = {'date': str(d), 'farm_id': f,
                       'acc_S01_src1': round(s1, 4), 'acc_S02_src2': round(s2, 4),
                       'acc_S03_limit': round(float(np.clip(s2 + rng.normal(1, 4), -70, 100)), 4),
                       'acc_S04_vendorF': round(float(vf), 4),
                       'acc_S05_vendorG': round(float(np.clip(s1 + rng.normal(0, 6), -70, 100)), 4),
                       'acc_S06_scale': round(float(np.clip(s1 * 0.85 + rng.normal(0, 2), -70, 100)), 4),
                       'acc_S07_scale': round(float(np.clip(s1 * 1.15 + rng.normal(0, 2), -70, 100)), 4),
                       'acc_S08_scale': round(float(np.clip(s1 * 0.9 + rng.normal(0, 2), -70, 100)), 4),
                       'acc_S09_scale': round(float(np.clip(s1 * 1.05 + rng.normal(0, 2), -70, 100)), 4),
                       'acc_S09_smooth4': round(float(np.clip(s1 + rng.normal(0, 4), -70, 100)), 4),
                       'acc_S10_smooth8': round(float(np.clip(s1 + rng.normal(0, 3), -70, 100)), 4),
                       'acc_S11_floor05': round(float(np.clip(s1 + rng.normal(1, 4), -70, 100)), 4),
                       'acc_S12_clip90': round(float(np.clip(s1 + rng.normal(0, 5), -70, 100)), 4),
                       'acc_S13_blendY': round(float(np.clip(0.7 * s1 + 0.3 * (s1 - 2) + rng.normal(0, 4), -70, 100)), 4),
                       'acc_S14_med8': round(float(np.clip(s1 + rng.normal(0, 4), -70, 100)), 4)}
                recs.append(rec)
    day = pd.DataFrame(recs, columns=['date', 'farm_id'] + SERIES)
    day.to_csv(daily_path, index=False)

    # ------------------------------------------------------------- farm-month
    day['ym'] = day.date.str[:7]
    day['month_days'] = day.ym.map(lambda m: len(month_days(m)))
    rows = []
    for (ym, f), g in day.groupby(['ym', 'farm_id']):
        mi = MONTHS.index(ym)
        cap = cap0[f] * (1.0 + 0.002 * mi)         # slow capacity growth
        n = len(g)
        rec = {'ym': ym, 'farm_id': f}
        for key, col in (('src1', 'acc_S01_src1'), ('src2', 'acc_S02_src2'),
                         ('vendorF', 'acc_S04_vendorF')):
            acc = g[col].mean()
            rec[key] = round(float(acc), 4)
            rec['def_' + key] = round(float(max(0.0, THETA - acc)), 4)
            rec['E_' + key] = round(float(cap * K * max(0.0, THETA - acc)), 3)
        rec.update({'Cap_MW': round(float(cap), 2), 'Cap_stat_global': round(float(cap), 2),
                    'Cap': round(float(cap), 2), 'days': n, 'cap_src': 'monthly',
                    'best': round(float(max(rec['src1'], rec['src2'])), 4),
                    'n_pass': int((g[['acc_S01_src1', 'acc_S02_src2']] >= THETA).sum(axis=1).max())})
        rows.append(rec)
    fm = pd.DataFrame(rows).sort_values(['ym', 'farm_id'])
    fm.to_csv(os.path.join(V5, 'farmmonth_v2_ext.csv'), index=False)

    # ------------------------------------------------------------- farm-month SE
    se_rows = []
    for (ym, f), g in day.groupby(['ym', 'farm_id']):
        if len(g) < 20:
            continue
        d = (g.acc_S02_src2 - g.acc_S01_src1).dropna().values
        a = g.acc_S02_src2.dropna().values

        def se(x):
            n = len(x)
            sd = x.std(ddof=1)
            rho = np.corrcoef(x[:-1], x[1:])[0, 1] if n > 2 else 0.0
            rho = min(max(float(rho), -0.9), 0.95)
            return float(sd / np.sqrt(n) * np.sqrt((1 + rho) / (1 - rho)))
        se_rows.append({'farm_id': f, 'ym': ym, 'n_days': len(g),
                        'gap': round(float(d.mean()), 4), 'acc': round(float(a.mean()), 4),
                        'se_gap': round(se(d), 4), 'se_acc': round(se(a), 4)})
    pd.DataFrame(se_rows).to_csv(os.path.join(V5, 'farmmonth_se.csv'), index=False)

    # ------------------------------------------------------------- realmonth stats
    rm_rows = []
    for (ym, f), g in day.groupby(['ym', 'farm_id']):
        mi = MONTHS.index(ym)
        cap = cap0[f] * (1.0 + 0.002 * mi)
        cf = float(np.clip(0.14 + 0.05 * m_res[ym] + rng.normal(0, 0.02), 0.02, 0.45))
        rm_rows.append({'farm_id': f, 'ym': ym,
                        'pm_mean': round(cap * cf, 3), 'pm_sd': round(cap * 0.08, 3),
                        'pm_p95': round(cap * cf * 2.2, 3), 'pm_ramp': round(cap * 0.05, 3),
                        'pm_calm': round(float(rng.uniform(0.1, 0.6)), 3),
                        'n_pts': len(g) * 96, 'Cap_MW': round(float(cap), 2),
                        'Cap0': round(float(cap), 2), 'Capr': round(float(cap), 2),
                        'cf': round(cf, 4), 'cf_sd': round(cf * 0.25, 4),
                        'cf_p95': round(cf * 2.2, 4), 'ramp': round(cf * 0.2, 4),
                        'calm': round(float(rng.uniform(0.1, 0.6)), 4)})
    pd.DataFrame(rm_rows).to_csv(os.path.join(V5, 'realmonth_stats.csv'), index=False)

    # ------------------------------------------------------------- mechanism panel
    mech = fm.copy()
    cf_m = pd.DataFrame(rm_rows).groupby('ym')['cf'].mean()
    mech['W_cf'] = mech.ym.map(cf_m) + rng.normal(0, 0.01, len(mech))
    mech['W_cf_sd'] = 0.02
    mech['W_p95'] = mech.W_cf * 2.0
    mech['W_ramp'] = 0.05
    mech['W_calm'] = 0.3
    mech['n_others'] = N_FARMS - 1
    mech['gap'] = mech.src2 - mech.src1
    mech['moy'] = mech.ym.str[5:7].astype(int)
    mech.to_csv(os.path.join(V5, 'mechanism_panel.csv'), index=False)

    # ------------------------------------------------------------- regression stub
    def block():
        return {'n': int(len(mech)), 'n_farm': N_FARMS, 'n_month': len(MONTHS),
                'mean': 3.0, 'sd': 11.5, 'sd_within_farm': 10.0,
                'farm_FE': {'r2': 0.10, 'r2adj': 0.08, 'k': N_FARMS},
                'farm_month_FE': {'r2': 0.13, 'r2adj': 0.06, 'k': N_FARMS + len(MONTHS)},
                'farm_FE_weather': {'r2': 0.18, 'r2adj': 0.14, 'k': N_FARMS + 4}}
    json.dump({'acc_incumbent': block(), 'gap': block()},
              open(os.path.join(V5, 'mechanism_reg2.json'), 'w'), indent=2)

    print('sample data written to', DATA)
    print('  daily rows      :', len(day))
    print('  farm-months     :', len(fm))
    print('  farm-months (SE):', len(se_rows))


if __name__ == '__main__':
    main()
