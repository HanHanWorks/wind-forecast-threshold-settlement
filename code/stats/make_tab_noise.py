#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成表 6：农场月统计量的抽样噪声分解（读 01_data/v5/{gap_noise,mechanism_reg2}.json）"""
import os, json

BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
V5 = os.path.join(BASE, 'data', 'v5')
OUT = os.path.join(BASE, 'outputs', 'tables')
os.makedirs(OUT, exist_ok=True)

noise = json.load(open(f'{V5}/gap_noise.json'))
reg = json.load(open(f'{V5}/mechanism_reg2.json'))


def row(label, d, indef):
    return (f"{label} & {d['sd_observed']:.2f} & {d['median_se']:.2f} & "
            f"{d['noise_share_of_variance']*100:.0f} & {d['sd_true_implied']:.2f} & {indef} \\\\")


rows = [
    row('Accuracy of the incumbent', noise['acc'], 'n/a'),
    row('Incumbent minus challenger', noise['gap'],
        f"{noise['share_gap_indistinguishable_from_zero']*100:.0f}"),
]

head = ('Quantity & Observed & Median & Noise & Implied & Indist.\\\\\n'
        ' & s.d. & s.e. & share (\\%) & true s.d. & from 0 (\\%) \\\\')

tex = (f"\\begin{{table}}[htb]\n\\centering\n"
       f"\\caption{{How much of a farm-month's variation is sampling noise. Standard errors are estimated "
       f"from the daily series of each farm-month ($n={noise['n_farm_month']}$), deconvolved for first-order "
       f"autocorrelation; the implied true standard deviation is what remains after the noise variance is "
       f"removed. The last column gives the share of farm-months in which the observed difference is not "
       f"distinguishable from zero at 95\\%.}}\n"
       f"\\label{{tab:noise}}\n\\small\n\\setlength{{\\tabcolsep}}{{4pt}}\n"
       f"\\begin{{tabular}}{{lrrrrr}}\n\\toprule\n{head}\n\\midrule\n"
       + '\n'.join(rows) +
       f"\n\\bottomrule\n\\end{{tabular}}\n\\end{{table}}\n")

open(os.path.join(OUT, 'tab6_noise.tex'), 'w').write(tex)
print(tex)
