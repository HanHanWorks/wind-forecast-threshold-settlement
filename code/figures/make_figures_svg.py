#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P2 论文插图（Fig. 2–6），矢量输出：SVG（交付/可编辑）+ PDF（供 LaTeX 编译）

设计原则
- 每张图承载一个论点，而不是装饰结果；
- 双栏宽 17.4 cm，字号 7 pt，按最终尺寸直接绘制（不做缩放）；
- 语义配色全组一致：
    阈值以上（零价值区）  浅灰 #DEE2E8
    决策真正有钱的单元    深红 #9B2C2C
    任何候选都救不了的区  石板蓝 #4A5568
    在役系统 深蓝 #1F4E79 / 源1 绿 #2E7D5B / 厂商F 橙 #C05621

输出：13_latex/figures_svg/*.svg、13_latex/figures/*.pdf、*.png（预览）
"""
import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter, NullLocator, FixedLocator
from matplotlib.patches import Rectangle, Patch

BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
V5 = os.path.join(BASE, 'data', 'v5')
SVG = os.path.join(BASE, 'outputs', 'figures_svg')
PDF = os.path.join(BASE, 'outputs', 'figures')
os.makedirs(SVG, exist_ok=True)
os.makedirs(PDF, exist_ok=True)

plt.rcParams.update({
    'font.family': 'Helvetica',
    'font.size': 7.0,
    'axes.labelsize': 7.0,
    'axes.titlesize': 7.5,
    'xtick.labelsize': 6.4,
    'ytick.labelsize': 6.4,
    'legend.fontsize': 6.4,
    'axes.linewidth': 0.6,
    'xtick.major.width': 0.6,
    'ytick.major.width': 0.6,
    'xtick.major.size': 2.6,
    'ytick.major.size': 2.6,
    'lines.linewidth': 1.0,
    'patch.linewidth': 0.5,
    'svg.fonttype': 'none',
    'pdf.fonttype': 42,
    'savefig.bbox': 'tight',        # 裁掉画布空白：图随内容收紧，再由 LaTeX 拉到版心
    'savefig.pad_inches': 0.0,
})

C_INC, C_S1, C_VF = '#A33A28', '#3F6480', '#8A94A6'
C_ZERO, C_LIVE, C_DEAD = '#C2CDD9', '#A33A28', '#6E7683'
C_GREY, C_DARK = '#AAB2BE', '#15171C'
W = 6.46                         # 16.4 cm = 版心宽度，与 LaTeX 1:1


def save(fig, name):
    for ext, d in (('svg', SVG), ('pdf', PDF), ('png', PDF)):
        fig.savefig(os.path.join(d, f'{name}.{ext}'), dpi=400 if ext == 'png' else None,
                    facecolor='white')
    plt.close(fig)
    print('  wrote', name)


def despine(ax, keep=('left', 'bottom')):
    for s in ('top', 'right', 'left', 'bottom'):
        if s not in keep:
            ax.spines[s].set_visible(False)


FM = pd.read_csv(os.path.join(V5, 'farmmonth_v2_ext.csv'), dtype={'farm_id': str})
C = FM[FM.ym.astype(str) <= '2025-05'].dropna(subset=['src1', 'src2']).copy()
C['best'] = C[['src1', 'src2']].max(axis=1)
C['n_pass'] = (C[['src1', 'src2']] >= 60).sum(axis=1)
THETA, K = 60.0, 0.2

MECH = pd.read_csv(os.path.join(V5, 'mechanism_panel.csv'), dtype={'farm_id': str})
G6R = pd.read_csv(os.path.join(V5, 'g6_resolution.csv'))
SE = pd.read_csv(os.path.join(V5, 'farmmonth_se.csv'), dtype={'farm_id': str})

# ================================================================ Fig. 2
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(W, 2.95), gridspec_kw={'width_ratios': [1, 1.05]})

acc = np.linspace(40, 78, 600)
for cap, col, lab in ((250, C_INC, '250 MW'), (105, C_S1, '105 MW'), (47, C_VF, '47 MW')):
    ax1.plot(acc, np.where(acc < THETA, cap * K, 0.0), color=col, lw=1.2, label=lab,
             solid_capstyle='butt')
    ax1.annotate(f'{cap*K:.0f}', xy=(41.0, cap * K - 2.0), color=col, fontsize=6.2, va='top')
ax1.axvspan(THETA, 78, color=C_ZERO, zorder=0)
ax1.text(69, 38, 'zero\nmarginal\nvalue', ha='center', va='center', fontsize=6.3, color=C_DEAD)
ax1.axvline(THETA, color=C_DARK, lw=0.7, ls=(0, (3, 2)))
ax1.set_xlim(40, 78)
ax1.set_ylim(-2, 54)
ax1.set_xlabel('Monthly accuracy ACC (%)')
ax1.set_ylabel('Marginal value of one point\n(MWh per month)')
ax1.set_title('(a) the rule pays a step, not a slope', loc='left', pad=3)
ax1.legend(frameon=False, loc='center right', bbox_to_anchor=(1.01, 0.42), handlelength=1.5,
           title='installed capacity', title_fontsize=6.1, borderpad=0.1, labelspacing=0.3)
ax1.text(41.0, 45.0, 'below the threshold\none point = 0.2 h\nof full output',
         fontsize=6.2, color=C_DARK, va='top')
despine(ax1)

HI = 82
ax2.add_patch(Rectangle((20, THETA), THETA - 20, HI - THETA, facecolor=C_LIVE, alpha=0.13, ec='none'))
ax2.add_patch(Rectangle((THETA, THETA), HI - THETA, HI - THETA, facecolor=C_ZERO, alpha=0.8, ec='none'))
ax2.add_patch(Rectangle((20, 20), THETA - 20, THETA - 20, facecolor=C_DEAD, alpha=0.10, ec='none'))
ok = C[(C.src2 > 20) & (C.best > 20)]
ax2.scatter(ok.src2, ok.best, s=3.0, color=C_INC, alpha=0.45, lw=0)
ax2.axvline(THETA, color=C_DARK, lw=0.7, ls=(0, (3, 2)))
ax2.axhline(THETA, color=C_DARK, lw=0.7, ls=(0, (3, 2)))
ax2.set_xlim(20, HI)
ax2.set_ylim(20, HI)
ax2.set_aspect('equal')
ax2.set_xlabel('Incumbent accuracy (%)')
ax2.set_ylabel('Best challenger accuracy (%)')
ax2.set_title('(b) and the decision lives in one corner', loc='left', pad=3)

n_inc_above = (C.src2 >= 60).mean() * 100
n_live = ((C.src2 < 60) & (C.best >= 60)).mean() * 100
n_dead = ((C.src2 < 60) & (C.best < 60)).mean() * 100
E_tot = C.E_src2.sum()
e_live = C.loc[(C.src2 < 60) & (C.best >= 60), 'E_src2'].sum() / E_tot * 100
e_dead = C.loc[(C.src2 < 60) & (C.best < 60), 'E_src2'].sum() / E_tot * 100

ax2.text(71.5, 79.2, f'{n_inc_above:.0f}% of months:\nno candidate can\nreduce the bill',
         ha='center', va='top', fontsize=6.3, color='#4A5568',
         bbox=dict(boxstyle='round,pad=0.22', fc='white', ec='none', alpha=0.9))
ax2.text(20.4, 78.8, f'{n_live:.0f}% of farm-months\ncarry {e_live:.0f}% of the bill',
         ha='left', va='top', fontsize=6.6, color=C_LIVE, fontweight='bold')
ax2.text(20.4, 21.2, f'{n_dead:.0f}% of farm-months carry {e_dead:.0f}% of the bill',
         ha='left', va='bottom', fontsize=6.4, color='white',
         bbox=dict(boxstyle='round,pad=0.26', fc=C_DEAD, ec='none', alpha=0.92))
ax2.annotate('', xy=(THETA - 1.0, 62.5), xytext=(THETA - 9.5, 74.5),
             arrowprops=dict(arrowstyle='-|>', color=C_LIVE, lw=0.8,
                             connectionstyle='arc3,rad=0.22'))
despine(ax2)
fig.subplots_adjust(wspace=0.28)
save(fig, 'fig2_value')

# ================================================================ Fig. 3
# (a) 洛伦兹；(b) 账单的季节性
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(W, 2.8), gridspec_kw={'width_ratios': [1, 1.12]})

e = np.sort(C.E_src2.values)[::-1]
cum_e = np.cumsum(e) / e.sum() * 100
x = np.arange(1, len(e) + 1) / len(e) * 100
ax1.plot([0, 100], [0, 100], color=C_GREY, lw=0.7, ls=(0, (3, 2)))
ax1.plot(x, cum_e, color=C_LIVE, lw=1.3)
ax1.fill_between(x, cum_e, x, color=C_LIVE, alpha=0.09, lw=0)
ax1.text(64, 59, 'equal shares', fontsize=6.0, color=C_GREY, rotation=45, ha='center')
y10 = np.interp(10, x, cum_e)
y20 = np.interp(20, x, cum_e)
for q, yq in ((10, y10), (20, y20)):
    ax1.plot([q, q], [0, yq], color=C_DARK, lw=0.6, ls=':')
    ax1.plot([0, q], [yq, yq], color=C_DARK, lw=0.6, ls=':')
ax1.scatter([10, 20], [y10, y20], s=12, color=C_LIVE, zorder=5)
ax1.annotate(f'the worst 10% of farm-months\ncarry {y10:.0f}% of the bill', xy=(12.0, y10 - 5),
             fontsize=6.3, color=C_DARK, va='top')
ax1.annotate(f'the worst 20% carry {y20:.0f}%', xy=(22.0, y20 + 4), fontsize=6.2,
             color=C_DARK, va='bottom')
ax1.set_xlim(0, 100)
ax1.set_ylim(0, 100)
ax1.set_xticks([0, 25, 50, 75, 100])
ax1.set_yticks([0, 25, 50, 75, 100])
ax1.set_xlabel('Farm-months, ranked by assessed energy (%)')
ax1.set_ylabel('Cumulative assessed energy (%)')
ax1.set_title('(a) concentrated in farm-months', loc='left', pad=3)
despine(ax1)

C2 = C.copy()
C2['moy'] = C2.ym.str[-2:].astype(int)
mo = C2.groupby('moy').agg(E=('E_src2', 'sum'), acc=('src2', 'mean'))
mo['share'] = mo.E / mo.E.sum() * 100
cols = [C_LIVE if a < THETA else C_GREY for a in mo.acc.values]   # 语义色：均值是否低于阈值
ax2.bar(mo.index, mo.share.values, width=0.70, color=cols, edgecolor='white', lw=0.5)
ax2.set_xlim(0.4, 12.6)
ax2.set_xticks(range(1, 13))
ax2.set_xticklabels(['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'])
ax2.set_ylim(0, 21)
ax2.set_ylabel('Share of the annual\nassessed energy (%)')
ax2.set_xlabel('Month of the year (all years pooled)')
q1 = mo.loc[[1, 2, 3], 'share'].sum()
q3 = mo.loc[[7, 8, 9], 'share'].sum()
ax2.annotate(f'Jan--Mar: {q1:.0f}% of the bill', xy=(3.2, 18.6), ha='left', fontsize=6.4,
             color=C_LIVE, fontweight='bold')
ax2.annotate(f'Jul--Sep: {q3:.0f}%', xy=(8, 6.2), ha='center', fontsize=6.3, color=C_DEAD)
ax2b = ax2.twinx()
ax2b.plot(mo.index, mo.acc.values, color=C_INC, lw=1.0, marker='o', ms=2.6, zorder=5)
ax2b.axhline(THETA, color=C_DARK, lw=0.6, ls=(0, (3, 2)))
ax2b.set_ylim(52, 68)
ax2b.set_yticks([54, 58, 62, 66])
ax2b.set_ylabel('Mean accuracy\nof the incumbent (%)', fontsize=6.6)
despine(ax2b, keep=('right',))
ax2.spines['right'].set_visible(False)
ax2b.spines['right'].set_linewidth(0.6)
ax2.set_title('(b) and in months', loc='left', pad=3)
fig.subplots_adjust(wspace=0.42)
save(fig, 'fig3_tail')

# ================================================================ Fig. 4
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(W, 2.9), gridspec_kw={'width_ratios': [1.12, 1]})

d = C.dropna(subset=['Cap', 'src2'])
above = d.src2 >= THETA
sz = np.sqrt(d.E_src2.clip(lower=0)) * 0.55
ax1.scatter(d.Cap[~above], d.src2[~above], s=sz[~above], facecolor=C_LIVE, alpha=0.30,
            edgecolor='none', label='below threshold')
ax1.scatter(d.Cap[above], d.src2[above], s=sz[above] + 1.5, facecolor=C_ZERO,
            edgecolor=C_GREY, lw=0.35, alpha=0.95, label='above threshold')
ax1.axhline(THETA, color=C_DARK, lw=0.8, ls=(0, (3, 2)))
ax1.set_xscale('log')
ax1.set_xlim(35, 330)
ax1.set_ylim(15, 92)
ax1.xaxis.set_major_locator(FixedLocator([40, 60, 100, 200, 300]))
ax1.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, p: f'{v:.0f}'))
ax1.xaxis.set_minor_locator(NullLocator())
ax1.xaxis.set_minor_formatter(NullFormatter())
ax1.set_xlabel('Installed capacity of the farm (MW, log scale)')
ax1.set_ylabel('Monthly accuracy of the incumbent (%)')
ax1.text(36.5, 61.8, r'$\theta$ = 60%', fontsize=6.5, color=C_DARK)
ax1.set_title('(a) big farms rarely fail; small farms fail cheaply', loc='left', pad=3)
ax1.legend(frameon=False, loc='lower right', handletextpad=0.4, borderpad=0.2,
           bbox_to_anchor=(1.02, -0.02))
ax1.text(0.03, 0.035, 'bubble area $\\propto$ assessed energy', transform=ax1.transAxes,
         fontsize=6.0, color=C_GREY)
despine(ax1)

q = pd.qcut(d.Cap, 4, labels=['Q1', 'Q2', 'Q3', 'Q4'])
g = d.groupby(q, observed=True).agg(E=('E_src2', 'sum'), n=('src2', 'size'),
                                    cap=('Cap', 'mean'),
                                    fail=('src2', lambda s: (s < THETA).mean() * 100))
share = g.E / g.E.sum() * 100
xb = np.arange(len(g))
ax2.bar(xb, share.values, width=0.60, color=[C_GREY, C_LIVE, C_LIVE, C_GREY],
        edgecolor='white', lw=0.6)
for i, s in enumerate(share.values):
    ax2.text(i, s + 1.2, f'{s:.0f}%', ha='center', va='bottom', fontsize=7.0,
             color=C_LIVE if 0 < i < 3 else C_DARK, fontweight='bold')
ax2.set_xticks(xb)
ax2.set_xticklabels([f'{lab}\n{c:.0f} MW' for lab, c in zip(g.index, g.cap.values)], fontsize=6.3)
ax2.set_ylim(0, 40)
ax2.set_ylabel('Share of total\nassessed energy (%)')
ax2.set_xlabel('Capacity quartile (mean capacity)', labelpad=3)
ax2b = ax2.twinx()
ax2b.plot(xb, g.fail.values, color=C_DARK, lw=1.0, marker='o', ms=3.4, zorder=5,
          clip_on=False)
ax2b.set_ylim(0, 100)
ax2b.set_yticks([0, 25, 50, 75, 100])
ax2b.set_ylabel('Farm-months below\nthe threshold (%)', fontsize=6.6)
despine(ax2b, keep=('right',))
ax2.spines['right'].set_visible(False)
ax2b.spines['right'].set_linewidth(0.6)
ax2.set_title('(b) the burden peaks away from both extremes', loc='left', pad=3)
fig.subplots_adjust(wspace=0.44)
save(fig, 'fig4_capacity')

# Fig. 5 is hand-drawn (make_fig1_nature.py) so that it matches Fig. 1.

# ================================================================ Fig. 6
fig, axes = plt.subplots(2, 2, figsize=(W, 5.0))
(a, b), (c, d2) = axes

gap = MECH.gap.values
a.hist(gap, bins=np.arange(-40, 46, 4), color=C_INC, alpha=0.85, edgecolor='white', lw=0.4)
a.axvline(0, color=C_DARK, lw=0.7)
a.axvline(gap.mean(), color=C_LIVE, lw=1.0)
a.annotate(f'mean {gap.mean():.1f}', xy=(gap.mean() + 1.6, a.get_ylim()[1] * 0.90),
           fontsize=6.3, color=C_LIVE, va='top')
a.annotate(f'{(gap < 0).mean()*100:.0f}% of months:\nthe challenger wins',
           xy=(-38, a.get_ylim()[1] * 0.55), fontsize=6.2, color=C_DEAD, va='top')
a.set_xlim(-40, 45)
a.set_xlabel('Incumbent minus challenger (accuracy points)')
a.set_ylabel('Farm-months')
a.set_title('(a) a difference with a fat tail on both sides', loc='left', pad=3)
despine(a)

ok = SE.dropna(subset=['gap', 'se_gap'])
xx = ok.gap.abs().values
yy = 1.96 * ok.se_gap.values
b.scatter(xx, yy, s=4, color=C_INC, alpha=0.35, lw=0)
b.plot([0, 90], [0, 90], color=C_LIVE, lw=0.9, ls=(0, (3, 2)))
b.set_xlim(0, 90)
b.set_ylim(0, 90)
frac = (xx <= yy).mean() * 100
b.text(2.5, 84, 'below the line:\nindistinguishable\nfrom zero', fontsize=6.2,
       color=C_LIVE, va='top', fontweight='bold')
b.text(87, 6, f'{frac:.0f}% of farm-months', fontsize=6.5, color=C_LIVE,
       ha='right', va='bottom', fontweight='bold')
b.set_xlabel('Observed difference in the month (|points|)')
b.set_ylabel('Its own 95% resolution (points)')
b.set_title('(b) the draw is as wide as the difference', loc='left', pad=3)
despine(b)

m = MECH.groupby('ym').agg(g=('gap', 'mean'), w=('W_cf', 'mean'), n=('gap', 'size')).reset_index()
c.scatter(m.w, m.g, s=11, facecolor=C_INC, edgecolor='white', lw=0.4, zorder=4)
k, b0 = np.polyfit(m.w, m.g, 1)
xs = np.linspace(m.w.min(), m.w.max(), 20)
c.plot(xs, k * xs + b0, color=C_LIVE, lw=1.0, zorder=5)
c.axhline(0, color=C_DARK, lw=0.6)
r = m.g.corr(m.w)
c.text(0.035, 0.93, f'r = {r:.2f}, n = {len(m)} months', transform=c.transAxes,
       fontsize=6.3, color=C_LIVE, va='top', fontweight='bold')
c.set_xlabel("Capacity factor of the other farms\nin the same month")
c.set_ylabel('Fleet-average difference\n(accuracy points)')
c.set_title('(c) windy months favour the incumbent', loc='left', pad=3)
despine(c)

mm = MECH.groupby('ym').agg(g=('gap', 'mean'), n=('gap', 'size'))
serr = SE.groupby('ym').agg(se=('se_gap', 'mean'))
mm = mm.join(serr, how='left')
mm['ci'] = 1.96 * mm.se / np.sqrt(mm.n)
xi = np.arange(len(mm))
d2.axhline(0, color=C_DARK, lw=0.6)
d2.errorbar(xi, mm.g.values, yerr=mm.ci.values, fmt='o', ms=2.3, lw=0.6, color=C_INC,
            ecolor=C_GREY, capsize=0)
pos = (mm.g > 0).sum()
d2.text(0.03, 0.94, f'{pos} of {len(mm)} months favour\nthe incumbent; {len(mm) - pos} do not',
        transform=d2.transAxes, fontsize=6.2, color=C_DEAD, va='top')
d2.set_xticks([0, 6, 12, 18, 24])
d2.set_xticklabels([mm.index[i] for i in (0, 6, 12, 18, 24)], fontsize=6.0)
d2.set_xlabel('Month')
d2.set_ylabel('Fleet-average difference\n(points, ±95% CI)')
d2.set_title('(d) and the sign is re-taken every month', loc='left', pad=3)
despine(d2)

fig.subplots_adjust(hspace=0.62, wspace=0.33)
save(fig, 'fig6_draw')

print('\nSVG:', SVG)
for f in sorted(os.listdir(SVG)):
    print('  ', f, f'{os.path.getsize(os.path.join(SVG, f))/1024:.0f} KB')
