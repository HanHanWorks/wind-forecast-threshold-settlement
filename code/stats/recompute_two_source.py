#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recompute every headline number of the two-source manuscript.

Window definitions (Table 7 of the paper)
  620  farm-months : monthly ledger, Jan 2023 - Aug 2025
  570  farm-months : of those, covered by the 15-minute record (through Jun 2025)
  545  farm-months : of those, in complete months of the record (through May 2025)
  491  farm-months : of those, with >= 20 usable daily observations after the
                     exemption filter (the operator's caliber; the per-farm-month
                     series is supplied in v5/farmmonth_se.csv)

The resolution block reproduces Table 4 exactly (circular moving-block
bootstrap, 4000 replicates, seed 2024, L-grid
[30, 45, 60, 75, 90, 105, 120, 150, 180, 240, 300, 365]).

Writes 01_data/v5/two_source_numbers.json and prints a human-readable summary.
"""
import os
import json
import math
import numpy as np
import pandas as pd

BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
FM = os.path.join(BASE, '01_data', 'v5', 'farmmonth_v2_ext.csv')
DAY = os.path.join(BASE, '01_data', 'daily_acc_panel.csv')
SE = os.path.join(BASE, '01_data', 'v5', 'farmmonth_se.csv')
NOISE = os.path.join(BASE, '01_data', 'v5', 'gap_noise.json')
REAL = os.path.join(BASE, '01_data', 'v5', 'realmonth_stats.csv')
OUT = os.path.join(BASE, '01_data', 'v5', 'two_source_numbers.json')

THETA, K = 60.0, 0.2
GRID = [30, 45, 60, 75, 90, 105, 120, 150, 180, 240, 300, 365]
SEED = 2024
B = 4000

fm = pd.read_csv(FM)
fm['ym'] = fm['ym'].astype(str)
led = fm.dropna(subset=['src1', 'src2']).copy()
w545 = led[led.ym <= '2025-05'].copy()          # complete-month window
w570 = led[led.ym <= '2025-06'].copy()          # daily-record coverage window

day = pd.read_csv(DAY, parse_dates=['date'])
day['ym'] = day.date.dt.strftime('%Y-%m')

out = {}

# ---------------------------------------------------------------- 1. sample
per_month = led.groupby('ym').size()
out['sample'] = {
    'n_farmmonth': int(len(led)),
    'n_farms': int(led.farm_id.nunique()),
    'n_months': int(led.ym.nunique()),
    'first_month': led.ym.min(), 'last_month': led.ym.max(),
    'farms_first_month': int(per_month.iloc[0]),
    'farms_2023_12': int(per_month.get('2023-12', 0)),
    'farms_last_month': int(per_month.iloc[-1]),
    'n_farmmonth_daily_window': int(len(w570)),
    'n_farmmonth_complete': int(len(w545)),
    'total_capacity_MW': round(float(led.groupby('farm_id').Cap.max().sum()), 1),
}

se = pd.read_csv(SE)
out['sample']['n_farmmonth_noise'] = int(len(se))          # 491

# ---------------------------------------------------------------- 2. systems (545 window)
sysobj = {}
for c, name in (('src1', 'source1'), ('src2', 'incumbent')):
    e = w545['E_' + c]
    sysobj[name] = {
        'mean_acc': round(float(w545[c].mean()), 2),
        'share_below60': round(float((w545[c] < THETA).mean() * 100), 1),
        'GWh_29m': round(float(e.sum() / 1e3), 1),
        'GWh_per_yr': round(float(e.sum() / 1e3 * 12 / 29), 1),
    }
out['systems'] = sysobj
out['gap_farmmonth'] = round(sysobj['incumbent']['mean_acc'] - sysobj['source1']['mean_acc'], 2)
out['delta_GWh_29m'] = round(sysobj['source1']['GWh_29m'] - sysobj['incumbent']['GWh_29m'], 1)
out['delta_GWh_per_yr'] = round(sysobj['source1']['GWh_per_yr'] - sysobj['incumbent']['GWh_per_yr'], 1)

# ---------------------------------------------------------------- 3. crosstab (545)
inc = w545.src2 >= THETA
both = (w545.src1 >= THETA) & inc
auc = (w545.src1 >= THETA) & ~inc
allb = (w545.src1 < THETA) & ~inc
E = w545.E_src2
tot = E.sum()
out['crosstab'] = {
    'inc_above_pct': round(float(inc.mean() * 100), 1),
    'both_above_pct': round(float(both.mean() * 100), 1),
    'auction_bites_pct': round(float(auc.mean() * 100), 1),
    'all_below_pct': round(float(allb.mean() * 100), 1),
    'E_inc_above_pct': 0.0,
    'E_auction_bites_pct': round(float(E[auc].sum() / tot * 100), 1),
    'E_all_below_pct': round(float(E[allb].sum() / tot * 100), 1),
}

# ---------------------------------------------------------------- 4. threshold bins (545)
a = w545.src2.values
out['bins'] = {
    '58-59': int(((a >= 58) & (a < 59)).sum()),
    '59-60': int(((a >= 59) & (a < 60)).sum()),
    '60-61': int(((a >= 60) & (a < 61)).sum()),
    '61-62': int(((a >= 61) & (a < 62)).sum()),
    'within_5pts_pct': round(float((np.abs(a - THETA) <= 5).mean() * 100), 1),
    'within_3pts_pct': round(float((np.abs(a - THETA) <= 3).mean() * 100), 1),
}

# ---------------------------------------------------------------- 5. concentration (545)
e = np.sort(E.values)[::-1]
cum = np.cumsum(e) / e.sum()
out['concentration'] = {}
for k in (0.05, 0.10, 0.20, 0.50):
    i = int(round(k * len(e))) - 1
    out['concentration']['worst_%.0f_pct' % (k * 100)] = {
        'count': i + 1, 'share_pct': round(float(cum[i] * 100), 1)}

# ---------------------------------------------------------------- 6. quartiles (545)
q = w545.copy()
q['q'] = pd.qcut(q['Cap'], 4, labels=['Q1', 'Q2', 'Q3', 'Q4'])
out['quartiles'] = {}
for name, g in q.groupby('q', observed=True):
    out['quartiles'][str(name)] = {
        'n': int(len(g)),
        'MW': round(float(g.Cap.mean()), 0),
        'below60_pct': round(float((g.src2 < THETA).mean() * 100), 1),
        'E_share_pct': round(float(g.E_src2.sum() / E.sum() * 100), 1),
        'MWh_per_point': round(float(g.Cap.mean() * K), 1),
    }

# ---------------------------------------------------------------- 7. seasonality (545)
mon = w545.ym.str[5:7].astype(int)
out['seasonality'] = {
    'jan_mar_E_pct': round(float(E[mon.isin([1, 2, 3])].sum() / tot * 100), 1),
    'jul_sep_E_pct': round(float(E[mon.isin([7, 8, 9])].sum() / tot * 100), 1),
}

# ---------------------------------------------------------------- 8. noise (491, operator caliber)
noise = json.load(open(NOISE))
rms_gap = float(np.sqrt((se.se_gap ** 2).mean()))
rms_acc = float(np.sqrt((se.se_acc ** 2).mean()))
out['noise'] = {
    'n': int(len(se)),
    'level': {
        'observed_sd': round(noise['acc']['sd_observed'], 2),
        'median_se': round(noise['acc']['median_se'], 2),
        'rms_se': round(rms_acc, 2),
        'noise_share_pct': round(noise['acc']['noise_share_of_variance'] * 100),
        'implied_true_sd': round(noise['acc']['sd_true_implied'], 2),
    },
    'diff': {
        'observed_sd': round(noise['gap']['sd_observed'], 2),
        'median_se': round(noise['gap']['median_se'], 2),
        'rms_se': round(rms_gap, 2),
        'noise_share_pct': round(noise['gap']['noise_share_of_variance'] * 100),
        'implied_true_sd': round(noise['gap']['sd_true_implied'], 2),
        'indistinguishable_pct': round(noise['share_gap_indistinguishable_from_zero'] * 100),
    },
}

# ---------------------------------------------------------------- 9. resolution
dates_main = set(day.dropna(subset=['acc_S01_src1', 'acc_S02_src2']).date.unique())


def mb_se(x, L, rng, reps=B):
    n = len(x)
    k = max(1, n // L)
    starts = rng.integers(0, n, k * reps)
    idx = (starts[:, None] + np.arange(L)[None, :]) % n
    return float(x[idx].mean(axis=1).std(ddof=1))


def pair_block(ca, cb):
    sub = day.dropna(subset=[ca, cb])
    sub = sub[sub.date.isin(dates_main)]
    g = sub.groupby('date')[[ca, cb]].mean().dropna()
    x = (g[ca] - g[cb]).values
    gap = abs(float(x.mean()))
    rng = np.random.default_rng(SEED)
    res = {L: 1.96 * mb_se(x, L, rng) for L in GRID}
    cross = None
    for a2, b2 in zip(GRID, GRID[1:]):
        if (res[a2] - gap) * (res[b2] - gap) <= 0:
            t = (math.log(res[a2]) - math.log(gap)) / (math.log(res[a2]) - math.log(res[b2]))
            cross = math.exp(math.log(a2) + t * (math.log(b2) - math.log(a2)))
    extrap = (res[90] * math.sqrt(90) / gap) ** 2
    return {
        'n_days': int(len(x)),
        'gap_points': round(gap, 3),
        'min_resolvable': {str(L): round(res[L], 3) for L in GRID},
        'gap_over_resolution_90d': round(gap / res[90], 3),
        'days_needed': round(cross, 1) if cross else None,
        'days_needed_extrapolated_from_90d': round(extrap),
    }


out['resolution'] = {
    'main_src2_minus_src1': pair_block('acc_S02_src2', 'acc_S01_src1'),
    'replicate_vendorF_minus_src1': pair_block('acc_S04_vendorF', 'acc_S01_src1'),
    'variant_scale085_minus_src2': pair_block('acc_S06_scale', 'acc_S02_src2'),
    'note': ('circular moving-block bootstrap, %d replicates, seed %d, L-grid %s; '
             'days_needed by log-linear crossing of the resolution curve, '
             'days_needed_extrapolated by inverse-square scaling from the 90-day estimate'
             % (B, SEED, GRID)),
}

# ------------------------------------------------------- 10. vendor replicate check
v = fm.dropna(subset=['vendorF'])
same_m = np.isclose(v.src1, v.vendorF, atol=1e-9)
vd = day.dropna(subset=['acc_S01_src1', 'acc_S04_vendorF'])
same_d = np.isclose(vd.acc_S01_src1, vd.acc_S04_vendorF, atol=1e-9)
yr = pd.to_datetime(v.ym).dt.year
out['vendor_replicate'] = {
    'monthly': {
        'rows': int(len(v)), 'identical': int(same_m.sum()),
        'identical_2023': int(same_m[yr == 2023].sum()), 'rows_2023': int((yr == 2023).sum()),
        'identical_2024': int(same_m[yr == 2024].sum()), 'rows_2024': int((yr == 2024).sum()),
    },
    'daily': {
        'rows': int(len(vd)), 'identical': int(same_d.sum()),
        'identical_pct': round(float(same_d.mean() * 100), 1),
    },
}

# --------------------------------------------------- 10b. regret of the award (eq:delta)
oracle545 = np.minimum(w545.E_src1, w545.E_src2)
oracle620 = np.minimum(led.E_src1, led.E_src2)
out['regret_vs_oracle'] = {
    'definition': 'Delta(pi) of eq. (2): sum over farm-months of V(pi) - min_s V(s)',
    'incumbent_award_GWh_545': round(float(np.maximum(0, w545.E_src2 - oracle545).sum() / 1e3), 2),
    'incumbent_award_GWh_per_yr': round(float(np.maximum(0, w545.E_src2 - oracle545).sum() / 1e3 * 12 / 29), 2),
    'incumbent_share_of_bill_pct': round(float(np.maximum(0, w545.E_src2 - oracle545).sum() / w545.E_src2.sum() * 100), 1),
    'source1_award_GWh_545': round(float(np.maximum(0, w545.E_src1 - oracle545).sum() / 1e3), 2),
    'incumbent_award_GWh_620': round(float(np.maximum(0, led.E_src2 - oracle620).sum() / 1e3), 2),
}

# ---------------------------------------------------------------- 11. generation
r = pd.read_csv(REAL)
r['ym'] = r.ym.astype(str)
r['yr'] = r.ym.str[:4]
r['E'] = r.pm_mean * r.n_pts * 0.25
gen24 = float(r[r.yr == '2024'].E.sum() / 1e6)
inc_bill = sysobj['incumbent']['GWh_per_yr']
out['generation'] = {
    'TWh_2024': round(gen24, 2),
    'cap_factor_2024': 0.153,
    'incumbent_bill_share_of_generation_pct': round(inc_bill / (gen24 * 1e3) * 100, 2),
}

# ---------------------------------------------------------------- 12. regime split
split = {}
for lab, sub in (('2023-01_to_2024-12', w545[w545.ym <= '2024-12']),
                 ('2025-01_to_2025-05', w545[w545.ym >= '2025-01'])):
    i2 = sub.src2 >= THETA
    split[lab] = {
        'n': int(len(sub)),
        'inc_above_pct': round(float(i2.mean() * 100), 1),
        'auction_bites_pct': round(float(((sub.src1 >= THETA) & ~i2).mean() * 100), 1),
        'all_below_pct': round(float(((sub.src1 < THETA) & ~i2).mean() * 100), 1),
    }
out['regime_split_2025_amendment'] = split

json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- summary
print(json.dumps(out, ensure_ascii=False, indent=1))
print('\nwrote', OUT)
