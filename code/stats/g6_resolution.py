#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G6：评估期的分辨率规则

问题：一个 L 天的评估期，能分辨多大的系统差距？
做法：
 1) 对每一对系统 i,j，构造日级 ACC 差序列 d_t = ACC_i,t − ACC_j,t
 2) 对窗口长度 L，用移动块 bootstrap 估计 mean(d) 的标准误 SE_L
    （块长 = L，重采样 B=2000 次；避开日度自相关导致的 SE 低估）
 3) 最小可分辨差 = 1.96 × SE_L
 4) 与实测差距比较：ratio = |mean d| / 最小可分辨差
 5) 反解：要把某一差距分辨出来，需要多长的评估期

对比组：
 · 真实系统（src1 / src2 / vendorF）——来自 v5 面板
 · 后处理变体（0.85×src1、1.15×src1、抬底5%、昨日混合）——**声明为按固定规则生成的
   压力测试，不代表任何投标方行为**

输出：g6_resolution.csv, g6_pairs.csv, g6_summary.json, fig5_resolution.pdf
"""
import os, json
import numpy as np
import pandas as pd

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'data', 'v5')
V5 = os.path.join(ROOT, 'data', 'daily_acc_panel.csv')
OLD = V5
RNG = np.random.default_rng(20261029)

L_GRID = [30, 60, 90, 120, 180, 270, 365, 540, 730]
B = 2000


def mb_se(d, L, B=B, rng=RNG):
    """移动块 bootstrap：窗口长度 L 下 mean(d) 的标准误"""
    d = np.asarray(d, float)
    n = len(d)
    if n <= L + 1:
        return np.nan
    starts = rng.integers(0, n - L, size=(B,))
    means = np.array([d[s:s + L].mean() for s in starts])
    return float(means.std(ddof=1))


def days_needed(d, gap, Lmax=3000):
    """反解：要分辨 |gap|，需要多长的评估期（线性外推 SE ∝ 1/sqrt(L)）"""
    L0 = 90
    se0 = mb_se(d, L0)
    if not np.isfinite(se0) or se0 <= 0:
        return np.nan
    need = (1.96 * se0 / abs(gap)) ** 2 * L0
    return float(need)


def main():
    v5 = pd.read_csv(V5, parse_dates=['date'])
    v5['ymd'] = v5.date.dt.normalize()
    v5 = v5.rename(columns={'acc_S01_src1': 'v2_src1', 'acc_S02_src2': 'v2_src2',
                           'acc_S04_vendorF': 'v2_vendorF'})
    real = v5.groupby('ymd')[['v2_src1', 'v2_src2', 'v2_vendorF']].mean()
    real.columns = ['src1', 'src2', 'vendorF']

    try:
        old = pd.read_csv(OLD, parse_dates=['date'])
        old['ymd'] = old.date.dt.normalize()
        var = old.groupby('ymd')[['acc_S06_scale', 'acc_S09_scale',
                                  'acc_S11_floor05', 'acc_S13_blendY']].mean()
        var.columns = ['scale085', 'scale115', 'floor05', 'blendY']
        df = real.join(var, how='inner')
        df = df.dropna(subset=['src1', 'src2', 'vendorF'])   # 与表 1-3 同一窗口（三源齐全）
        df = df.dropna(subset=[c for c in ['scale085', 'scale115', 'floor05', 'blendY'] if c in df.columns])
    except Exception as e:
        print('变体面板缺失，仅跑真实系统：', e)
        df = real.copy()

    print(f'日级序列：{len(df)} 天  {df.index.min().date()} .. {df.index.max().date()}')
    print('各系统日均 ACC：')
    for c in df.columns:
        print(f'  {c:9s} {df[c].mean():6.2f}  (有效 {df[c].notna().mean()*100:5.1f}%)')

    names = list(df.columns)
    real_set = ['src1', 'src2', 'vendorF']
    pairs = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            d = (df[a] - df[b]).dropna().values
            if len(d) < 120:
                continue
            gap = float(np.mean(d))
            se90 = mb_se(d, 90)
            minres90 = 1.96 * se90 if np.isfinite(se90) else np.nan
            pairs.append({
                'a': a, 'b': b,
                'group': 'real' if (a in real_set and b in real_set) else 'variant',
                'gap_points': gap,
                'sd_daily': float(np.std(d, ddof=1)),
                'n_days': int(len(d)),
                'se90': se90,
                'min_resolvable_90d': minres90,
                'ratio_90d': float(abs(gap) / minres90) if minres90 and np.isfinite(minres90) else np.nan,
                'days_needed': days_needed(d, gap),
            })
    P = pd.DataFrame(pairs).sort_values(['group', 'gap_points'], ascending=[True, False])
    P.to_csv(f'{OUT}/g6_pairs.csv', index=False)

    print('\n=== 配对：90 天窗口下的可分辨性 ===')
    print(P[['a', 'b', 'group', 'gap_points', 'se90', 'min_resolvable_90d',
             'ratio_90d', 'days_needed']].to_string(index=False, float_format=lambda x: f'{x:8.2f}'))

    # 分辨率曲线（以真实配对的中位 SE 为参照）
    realP = P[P.group == 'real']
    rows = []
    for _, r in realP.iterrows():
        d = (df[r.a] - df[r.b]).dropna().values
        for L in L_GRID:
            se = mb_se(d, L)
            rows.append({'pair': f'{r.a}-{r.b}', 'L_days': L,
                         'se': se, 'min_resolvable': 1.96 * se if np.isfinite(se) else np.nan,
                         'gap_points': r.gap_points})
    R = pd.DataFrame(rows)
    R.to_csv(f'{OUT}/g6_resolution.csv', index=False)

    # 反解：在哪些 L 上各差距变得可分辨
    print('\n=== 可分辨所需的评估期长度 ===')
    need = []
    for _, r in P.iterrows():
        need.append({'pair': f"{r.a}-{r.b}", 'group': r.group, 'gap': r.gap_points,
                     'days_needed': r.days_needed})
    N = pd.DataFrame(need).sort_values('days_needed')
    print(N.to_string(index=False, float_format=lambda x: f'{x:8.0f}'))

    summary = {
        'n_days': int(len(df)),
        'period': [str(df.index.min().date()), str(df.index.max().date())],
        'mean_acc': {c: float(df[c].mean()) for c in names},
        'resolution_90d': {f"{r.a}-{r.b}": float(r.min_resolvable_90d) for _, r in P.iterrows()},
        'real_gaps': {f"{r.a}-{r.b}": float(r.gap_points) for _, r in realP.iterrows()},
        'variant_gaps': {f"{r.a}-{r.b}": float(r.gap_points) for _, r in P[P.group == 'variant'].iterrows()},
    }
    json.dump(summary, open(f'{OUT}/g6_summary.json', 'w'), ensure_ascii=False, indent=2)

    # ---------- 图 ----------
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(7.0, 4.0))
        colors = {'src1-src2': '#2B6CB0', 'src2-vendorF': '#2F855A', 'src1-vendorF': '#C05621'}
        for pair, g in R.groupby('pair'):
            g = g.sort_values('L_days')
            ax.plot(g.L_days, g.min_resolvable, marker='o', ms=3.5, lw=1.3,
                    color=colors.get(pair), label=pair.replace('-', ' vs '))
        ax.axvline(90, color='#888888', ls=':', lw=1.0)
        ax.text(92, ax.get_ylim()[1] * 0.94, 'assessment window\n(90 d)', fontsize=7,
                color='#555555', va='top')
        ypos = {'src1-src2': 2.60, 'src2-vendorF': 2.89, 'src1-vendorF': 0.20}
        for pair, gp in ypos.items():
            ax.axhline(gp, color=colors.get(pair), ls='--', lw=0.9, alpha=.55)
            ax.text(735, gp, f'  {pair.replace("-", " vs ")}: {gp:.2f}', fontsize=7,
                    color=colors.get(pair), va='center')
        ax.set_xscale('log')
        ax.set_xticks([30, 60, 90, 180, 365, 730])
        ax.set_xticklabels(['30', '60', '90', '180', '365', '730'])
        ax.set_xlim(28, 900)
        ax.set_ylim(0, 6.6)
        ax.set_xlabel('Evaluation window length L (days)')
        ax.set_ylabel('Minimum resolvable difference\n(accuracy points, 95%)')
        ax.legend(fontsize=7, frameon=False, loc='upper right', bbox_to_anchor=(1.0, 0.86))
        ax.grid(alpha=.25, lw=.5)
        fig.tight_layout()
        fig.savefig(f'{OUT}/fig5_resolution.pdf')
        fig.savefig(f'{OUT}/fig5_resolution.png', dpi=300)
        print('\n图已输出：fig5_resolution.pdf / .png')
    except Exception as e:
        print('出图失败：', e)


if __name__ == '__main__':
    main()
