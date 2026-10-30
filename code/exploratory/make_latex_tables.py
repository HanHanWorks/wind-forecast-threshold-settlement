#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 12_writing/*.csv 转成 booktabs LaTeX 表格"""
import os
import pandas as pd

BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
SRC = os.path.join(BASE, '12_writing')
OUT = os.path.join(BASE, 'outputs', 'tables')
os.makedirs(OUT, exist_ok=True)


def wrap(fname, body, caption, label, size='\\small', colsep='3pt'):
    spec = body['spec']
    if 'X' in spec:
        begin = f"\\begin{{tabularx}}{{\\textwidth}}{{{spec}}}"
        end = "\\end{tabularx}"
    else:
        begin = f"\\begin{{tabular}}{{{spec}}}"
        end = "\\end{tabular}"
    return (f"\\begin{{table}}[htb]\n\\centering\n"
            f"\\caption{{{caption}}}\n\\label{{{label}}}\n"
            f"{size}\n\\setlength{{\\tabcolsep}}{{{colsep}}}\n"
            f"{begin}\n\\toprule\n"
            f"{body['head']}\n\\midrule\n{body['rows']}\n\\bottomrule\n"
            f"{end}\n\\end{{table}}\n")


def write(name, text):
    open(os.path.join(OUT, name), 'w').write(text)
    print('wrote', name)


# ---- Table 1 ----
d = pd.read_csv(f'{SRC}/table1_systems.csv')
rows = []
for _, r in d.iterrows():
    rows.append(f"{r.system.replace('Dispatch source', 'Source')} & {r.mean_acc:.2f} & {r.pct_below_threshold:.1f} & "
                f"{r.assessed_energy_GWh_per_year:.1f} \\\\")
write('tab1_systems.tex', wrap('t1', {
    'spec': 'lrrr',
    'head': 'Candidate & Mean ACC (\\%) & Below 60\\% (\\%) & GWh yr$^{-1}$ \\\\',
    'rows': '\n'.join(rows),
}, 'The three forecasting sources available to the dispatch centre. Assessed energy is computed with the published hinge, the coefficient $k=0.2$ and monthly installed capacity.', 'tab:systems'))

# ---- Table 2 ----
d = pd.read_csv(f'{SRC}/table2_crosstab.csv').set_index('cell')
def cell(k):
    return d.loc[k, 'share_farmmonths'], d.loc[k, 'share_of_assessed_energy']
above = cell('incumbent above threshold (zero marginal value)')
allall = cell('all candidates above threshold (choice irrelevant)')
live = cell('best above, incumbent below (decision has a price)')
none = cell('all candidates below threshold (no choice helps)')
rows = [
    f"Incumbent above threshold & {above[0]:.1f} & {above[1]:.1f} \\\\",
    f"\\quad\\ (every candidate above) & {allall[0]:.1f} & 0.0 \\\\",
    f"Best above, incumbent below & {live[0]:.1f} & {live[1]:.1f} \\\\",
    f"All below threshold & {none[0]:.1f} & {none[1]:.1f} \\\\",
    f"\\midrule",
    f"\\textbf{{Total}} & \\textbf{{{above[0]+live[0]+none[0]:.1f}}} & \\textbf{{{above[1]+live[1]+none[1]:.1f}}} \\\\",
]
write('tab2_crosstab.tex', wrap('t2', {
    'spec': 'lrr',
    'head': 'Cell & Share of farm-months (\\%) & Share of assessed energy (\\%) \\\\',
    'rows': '\n'.join(rows),
}, 'Where the assessed energy sits. The first, third and fourth rows partition the 545 farm-months in which all three sources are present; the second row is the subset of the first in which no choice could matter. Assessed energy is that of the incumbent system, and its total in the two cells where the incumbent is above the threshold is zero by construction.', 'tab:crosstab'))

# ---- Table 3 ----
d = pd.read_csv(f'{SRC}/table3_concentration.csv')
rows = [f"{str(r.top_share_of_farm_months).replace('%', chr(92)+'%')} & {r.n_farm_months} & {r.share_of_assessed_energy:.1f} \\\\"
        for _, r in d.iterrows()]
write('tab3_concentration.tex', wrap('t3', {
    'spec': 'rrr',
    'head': 'Worst share of farm-months & Count & Share of assessed energy (\\%) \\\\',
    'rows': '\n'.join(rows),
}, 'Concentration of the incumbent system\'s assessed energy across farm-months, ranked from worst to best.', 'tab:concentration'))

# ---- Table 4 ----
d = pd.read_csv(f'{SRC}/table4_resolution.csv')
rows = [f"{r.pair.replace('vs', 'vs.')} & {r.observed_gap_points:.2f} & {r.min_resolvable_90d:.2f} & "
        f"{r.ratio_at_90d:.2f} & {r.days_needed:.0f} \\\\" for _, r in d.iterrows()]
write('tab4_resolution.tex', wrap('t4', {
    'spec': 'lrrrr',
    'head': 'Pair & Observed gap (points) & Minimum resolvable at 90\\,d & Ratio & Window needed (d) \\\\',
    'rows': '\n'.join(rows),
}, 'Resolution of pairwise comparisons at a 95\\% level. A ratio below one means the 90-day assessment period cannot separate the two systems.', 'tab:resolution'))

# ---- Table 5 ----
d = pd.read_csv(f'{SRC}/table5_triage.csv')
rows = [f"{r.capacity_quartile} & {r.n_farm_months} & {r.mean_capacity_MW:.0f} & "
        f"{r.share_below_threshold:.1f} & {r.share_of_total_assessed:.1f} & {r.assessed_per_point_MWh:.1f} \\\\"
        for _, r in d.iterrows()]
write('tab5_triage.tex', wrap('tab5_triage.tex', {
    'spec': 'Xrrrrr',
    'head': 'Quartile & N & MW & Below (\\%) & Energy (\\%) & MWh/pt \\\\',
    'rows': '\n'.join(rows),
}, 'Assessed energy by installed-capacity quartile. The burden peaks in the two middle quartiles, not at either extreme.', 'tab:triage', size='\\footnotesize'))
