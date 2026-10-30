#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成论文插图（矢量 PDF）到 13_latex/figures/"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import pandas as pd

BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
FIG = os.path.join(BASE, 'outputs', 'figures')
os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({'font.size': 8, 'font.family': 'DejaVu Sans',
                     'axes.linewidth': 0.6, 'pdf.fonttype': 42})


def box(ax, x, y, w, h, text, fc='#eef2f7', ec='#33475b'):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.012,rounding_size=0.02',
                                fc=fc, ec=ec, lw=0.7))
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center', fontsize=7.2, wrap=True)


def arrow(ax, p, q, style='-|>', ls='-'):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=8,
                                 lw=0.7, color='#33475b', linestyle=ls,
                                 shrinkA=2, shrinkB=2))


# ---------- Fig. 1 系统示意 ----------
fig, ax = plt.subplots(figsize=(7.0, 3.2))
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
box(ax, 0.02, 0.62, 0.17, 0.22, 'Wind farms\n(18--25,\n25--250 MW)')
box(ax, 0.02, 0.20, 0.17, 0.22, 'Actual power\n(15-min)\n+ theory power')
box(ax, 0.25, 0.72, 0.17, 0.14, 'Source 1\n(dispatch)')
box(ax, 0.25, 0.55, 0.17, 0.14, 'Source 2\n(incumbent)')
box(ax, 0.25, 0.38, 0.17, 0.14, 'Vendor F')
box(ax, 0.25, 0.12, 0.17, 0.18, 'Settlement\nrules\n$\\theta$, $k$, Cap$_m$')
box(ax, 0.50, 0.45, 0.19, 0.30, 'Provincial\ndispatch centre\n\none system\nlocked for\nthe year', fc='#fdf1e3')
box(ax, 0.76, 0.62, 0.21, 0.22, 'Assessed energy\n$E=Cap_m k\\max(0,\\theta-ACC)$', fc='#fbe6e6')
box(ax, 0.76, 0.20, 0.21, 0.22, 'Balance of plant\ncash flow', fc='#eaf3de')
arrow(ax, (0.19, 0.73), (0.25, 0.79)); arrow(ax, (0.19, 0.73), (0.25, 0.62))
arrow(ax, (0.19, 0.73), (0.25, 0.45))
arrow(ax, (0.19, 0.31), (0.25, 0.21), ls='--')
arrow(ax, (0.42, 0.79), (0.50, 0.68)); arrow(ax, (0.42, 0.62), (0.50, 0.60))
arrow(ax, (0.42, 0.45), (0.50, 0.52))
arrow(ax, (0.42, 0.21), (0.50, 0.45), ls='--')
arrow(ax, (0.69, 0.66), (0.76, 0.72))
arrow(ax, (0.865, 0.62), (0.865, 0.42))
ax.text(0.865, 0.53, 'money', ha='center', fontsize=6.5, color='#7a4a2a')
fig.tight_layout()
fig.savefig(f'{FIG}/fig1_system.pdf'); fig.savefig(f'{FIG}/fig1_system.png', dpi=300)
plt.close(fig)

# ---------- Fig. 2 铰链 ----------
fig, ax = plt.subplots(figsize=(3.4, 2.6))
acc = np.linspace(40, 80, 400)
for cap, c in [(250, '#2B6CB0'), (100, '#2F855A'), (47, '#C05621')]:
    e = cap * 0.2 * np.maximum(0, 60 - acc)
    ax.plot(acc, e, color=c, lw=1.4, label=f'{cap} MW')
ax.axvline(60, color='#888888', ls=':', lw=0.9)
ax.text(60.8, ax.get_ylim()[1] * 0.55, '$\\theta=60\\%$', fontsize=7, color='#555555')
ax.set_xlabel('Monthly accuracy ACC (%)')
ax.set_ylabel('Assessed energy (MWh per month)')
ax.legend(frameon=False, fontsize=6.5, title='Installed capacity', title_fontsize=6.5)
ax.set_xlim(40, 80); ax.set_ylim(0, None)
ax.grid(alpha=.25, lw=.5)
fig.tight_layout()
fig.savefig(f'{FIG}/fig2_hinge.pdf'); fig.savefig(f'{FIG}/fig2_hinge.png', dpi=300)
plt.close(fig)

# ---------- Fig. 3 分辨率 ----------
d = pd.read_csv(os.path.join(BASE, 'data', 'v5', 'g6_resolution.csv'))
gaps = {'src1-src2': 2.60, 'src2-vendorF': 2.89, 'src1-vendorF': 0.20}
colors = {'src1-src2': '#2B6CB0', 'src2-vendorF': '#2F855A', 'src1-vendorF': '#C05621'}
fig, ax = plt.subplots(figsize=(3.6, 2.7))
for pair, g in d.groupby('pair'):
    g = g.sort_values('L_days')
    ax.plot(g.L_days, g.min_resolvable, marker='o', ms=3, lw=1.1,
            color=colors.get(pair), label=pair.replace('-', ' vs '))
for pair, gp in gaps.items():
    ax.axhline(gp, color=colors[pair], ls='--', lw=0.8, alpha=.5)
ax.axvline(90, color='#888888', ls=':', lw=1.0)
ax.text(94, ax.get_ylim()[1] * 0.92, 'assessment\nwindow', fontsize=6.5, color='#555555', va='top')
ax.set_xscale('log')
ax.set_xticks([30, 60, 90, 180, 365, 730]); ax.set_xticklabels(['30', '60', '90', '180', '365', '730'])
ax.set_xlim(28, 780); ax.set_ylim(0, None)
ax.set_xlabel('Evaluation window $L$ (days)')
ax.set_ylabel('Minimum resolvable\ndifference (points, 95%)')
ax.legend(frameon=False, fontsize=6.2, loc='upper right')
ax.grid(alpha=.25, lw=.5)
fig.tight_layout()
fig.savefig(f'{FIG}/fig3_resolution.pdf'); fig.savefig(f'{FIG}/fig3_resolution.png', dpi=300)
plt.close(fig)
print('figures done')
