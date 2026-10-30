#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fig. 1 —— 系统与制度流程（手写 SVG）

要让审稿人一眼看出"这是流程"，图里必须有：阶段编号、阶段括号、重复单元、方向明确的箭头。
因此本版相对上一版加了四样东西：
  ① 四个编号阶段（① 供给 → ② 基准与授标 → ③ 锁定运行 → ④ 按月结算）
  ② 顶部阶段括号：TRIAL YEAR / ASSESSMENT YEAR，把"什么时候发生"放到时间轴上
  ③ ④ 用一个虚线容器包住，标明"每个场站每月迭代一次"——这是流程里的循环单元
  ④ 底部可观测性带：授标之后另外两条预报不再存在（论文的论证起点）

输出：13_latex/figures_svg/fig1_chain.svg
     13_latex/figures/fig1_chain.pdf（rsvg-convert，供 LaTeX 用）
"""
import os
import subprocess

BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
SVG_DIR = os.path.join(BASE, 'outputs', 'figures_svg')
FIG_DIR = os.path.join(BASE, 'outputs', 'figures')
os.makedirs(SVG_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)

INK, GREY, LINE = '#2D3748', '#5A6474', '#4A5568'
INC, ACCENT, S1 = '#1F4E79', '#9B2C2C', '#2E7D5B'
CHIP, EDGE = '#F4F6F9', '#C3CAD5'
GREEN_T, GREY_T = '#EAF3EE', '#E9ECF1'
RED_T, BLUE_T = '#FBEFEF', '#E8EFF7'

W, H = 164.0, 98.0
OUT_W = 140.0                    # 出图 140 mm，LaTeX 拉到 164 mm 版心 → 字号 ≈ 8.2 pt
FS_T, FS_S, FS_XS = 2.42, 2.10, 1.94

# ---- 布局
SPLIT = 100.0                    # 授标完成处 = 可观测性分界 = 阶段括号分界
S_X, S_W = 8.0, 40.0
B_X, B_W = 58.0, 42.0
D_X, D_W = 110.0, 46.0
L1_Y, L1_H = 14.0, 18.0

BOX_Y, BOX_H = 61.0, 16.0
MEAS_X, MEAS_W = 8.0, 26.0        # 实测出力：容器左侧的输入列
ACC_X, ACC_W = 42.0, 38.0
ENE_X, ENE_W = 86.0, 38.0
BIL_X, BIL_W = 130.0, 22.0
CONT_X, CONT_Y, CONT_W, CONT_H = 38.0, 54.0, 118.0, 28.0

BAND_Y, BAND_H = 86.0, 9.2


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


class Svg:
    def __init__(self):
        self.p = []

    def rect(self, x, y, w, h, fill='#FFFFFF', stroke=INK, sw=0.30, rx=1.4, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.p.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
                      f'rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def text(self, x, y, s_, size=FS_T, fill=INK, anchor='middle', weight='normal', ls=None):
        l = f' letter-spacing="{ls}"' if ls else ''
        self.p.append(f'<text x="{x:.2f}" y="{y:.2f}" font-family="Arial, Helvetica, sans-serif" '
                      f'font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
                      f'font-weight="{weight}"{l}>{esc(s_)}</text>')

    def line(self, x1, y1, x2, y2, color=LINE, sw=0.30, dash=None, marker=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        m = f' marker-end="url(#{marker})"' if marker else ''
        self.p.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
                      f'stroke="{color}" stroke-width="{sw}"{d}{m} stroke-linecap="round"/>')

    def path(self, d, color=LINE, sw=0.30, marker=None, dash=None):
        m = f' marker-end="url(#{marker})"' if marker else ''
        dd = f' stroke-dasharray="{dash}"' if dash else ''
        self.p.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}"{m}{dd} '
                      f'stroke-linejoin="round" stroke-linecap="round"/>')

    def box(self, x, y, w, h, title, sub=None, sub2=None, fill='#FFFFFF', stroke=INK,
            tcol=INK, scol=GREY):
        self.rect(x, y, w, h, fill=fill, stroke=stroke)
        cy = y + h / 2
        if sub is None:
            self.text(x + w / 2, cy + 0.85, title, FS_T, tcol, weight='bold')
        elif sub2 is None:
            self.text(x + w / 2, cy - 0.55, title, FS_T, tcol, weight='bold')
            self.text(x + w / 2, cy + 2.55, sub, FS_S, scol)
        else:
            self.text(x + w / 2, cy - 1.9, title, FS_T, tcol, weight='bold')
            self.text(x + w / 2, cy + 1.1, sub, FS_S, scol)
            self.text(x + w / 2, cy + 3.9, sub2, FS_S, scol)

    def badge(self, x, y, n, color=INK):
        """阶段编号：白底圆 + 数字"""
        self.p.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="2.35" fill="#FFFFFF" '
                      f'stroke="{color}" stroke-width="0.34"/>')
        self.text(x, y + 0.82, str(n), 2.32, color, weight='bold')

    def render(self):
        head = (
            f'<?xml version="1.0" encoding="utf-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{OUT_W}mm" '
            f'height="{OUT_W * H / W:.2f}mm" viewBox="0 0 {W} {H}" version="1.1">\n<defs>\n'
            + ''.join(
                f'  <marker id="{mid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.0" '
                f'markerHeight="5.0" orient="auto-start-reverse">'
                f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{col}"/></marker>\n'
                for mid, col in (('ar', LINE), ('ar-blue', INC), ('ar-red', ACCENT)))
            + '</defs>\n'
            f'<rect x="0" y="0" width="{W}" height="{H}" fill="#FFFFFF"/>\n')
        return head + '\n'.join(self.p) + '\n</svg>\n'


s = Svg()

# ================================================================ 阶段括号
def bracket(x1, x2, label, col=GREY, y=8.6):
    s.line(x1, y + 2.6, x1, y, color=col, sw=0.30)
    s.line(x2, y + 2.6, x2, y, color=col, sw=0.30)
    s.line(x1, y, x2, y, color=col, sw=0.30)
    s.text((x1 + x2) / 2, y - 1.1, label, FS_XS, col, ls='0.2')


bracket(S_X, SPLIT, 'TRIAL YEAR  \u2014  all three candidates run')
bracket(SPLIT, D_X + D_W, 'ASSESSMENT YEAR  \u2014  one runs', col=ACCENT)

# ================================================================ 阶段 ① 预报源
s.box(S_X, L1_Y, S_W, L1_H, '', )
s.rect(S_X, L1_Y, S_W, L1_H, fill='#FFFFFF', stroke=INK)
s.text(S_X + S_W / 2, L1_Y + 2.4, 'Forecast sources', FS_S, GREY)
for cy, lab, fill, edge, tc in ((L1_Y + 4.6, 'source 1', CHIP, EDGE, INK),
                                (L1_Y + 9.0, 'source 2 \u2014 incumbent', BLUE_T, INC, INC),
                                (L1_Y + 13.4, 'vendor F', CHIP, EDGE, INK)):
    s.rect(S_X + 2.4, cy, S_W - 4.8, 3.9, fill=fill, stroke=edge, sw=0.26, rx=0.9)
    s.text(S_X + S_W / 2, cy + 2.75, lab, FS_S, tc)

# ================================================================ 阶段 ② 基准与授标
s.box(B_X, L1_Y, B_W, L1_H, 'Benchmark, award', 'one system', 'locked for the year',
      fill=RED_T, stroke=ACCENT, tcol=ACCENT)

# ================================================================ 阶段 ③ 锁定运行
s.box(D_X, L1_Y, D_W, L1_H, 'Dispatch centre', 'schedules with', 'the locked forecast')

s.line(S_X + S_W, 23.0, B_X - 0.6, 23.0, marker='ar')
s.text((S_X + S_W + B_X) / 2, 21.3, 'trial', FS_XS, GREY)
s.line(B_X + B_W, 23.0, D_X - 0.6, 23.0, marker='ar')

# 编号
s.badge(S_X + 3.6, L1_Y, '1')
s.badge(B_X + 3.4, L1_Y, '2', ACCENT)
s.badge(D_X + 3.4, L1_Y, '3')

# ================================================================ 阶段 ④ 按月结算（循环单元）
s.rect(CONT_X, CONT_Y, CONT_W, CONT_H, fill='#FBFCFD', stroke='#B9C2CE', sw=0.28,
       rx=1.6, dash='2.2 1.5')
s.text(CONT_X + 13.2, CONT_Y + 4.4,
       'EVERY MONTH OF THE ASSESSMENT YEAR  \u2014  12 iterations per farm',
       FS_XS, '#5A6474', anchor='start', ls='0.15')

# 输入列：风电场及其实测出力（会计链的被考核方）
s.box(MEAS_X, BOX_Y, MEAS_W, BOX_H, 'Wind farms', 'measured output', '15-min SCADA')
s.line(MEAS_X + MEAS_W, 69.0, ACC_X - 0.6, 69.0, marker='ar')

s.box(ACC_X, BOX_Y, ACC_W, BOX_H, 'Monthly accuracy', 'ACC = 1 \u2212 nRMSE', '\u03b8 = 60%')
s.box(ENE_X, BOX_Y, ENE_W, BOX_H, 'Assessed energy', 'Cap \u00b7 k \u00b7 max(0, \u03b8 \u2212 ACC)')
s.rect(BIL_X, BOX_Y, BIL_W, BOX_H, fill='#FFFFFF', stroke=INK, sw=0.55, rx=3.2)
s.text(BIL_X + BIL_W / 2, BOX_Y + 5.6, 'Monthly bill', FS_T, INK, weight='bold')
s.text(BIL_X + BIL_W / 2, BOX_Y + 9.8, 'MWh per farm', FS_S, GREY)

s.line(ACC_X + ACC_W, 69.0, ENE_X - 0.6, 69.0, marker='ar')
s.line(ENE_X + ENE_W, 69.0, BIL_X - 0.6, 69.0, marker='ar')

# 授标后的那条预报进入会计链
s.path(f'M {B_X + B_W / 2:.2f} {L1_Y + L1_H} L {B_X + B_W / 2:.2f} 46.5 '
       f'L {ACC_X + 5.0:.2f} 46.5 L {ACC_X + 5.0:.2f} {BOX_Y - 0.4}',
       color=INC, sw=0.34, marker='ar-blue')
s.text(ACC_X + 7.0, 45.2, 'the awarded source', FS_XS, INC, anchor='start')

# 阶段编号 ④ 落在容器左上
s.badge(CONT_X + 2.4, CONT_Y, '4')

# ================================================================ 可观测性带
s.rect(S_X, BAND_Y, SPLIT - S_X, BAND_H, fill=GREEN_T, stroke='none', rx=1.2)
s.rect(SPLIT, BAND_Y, D_X + D_W - SPLIT, BAND_H, fill=GREY_T, stroke='none', rx=1.2)
mid_l, mid_r = (S_X + SPLIT) / 2, (SPLIT + D_X + D_W) / 2
s.text(mid_l, BAND_Y + 3.8, 'all three forecasts exist \u2014 every candidate can be compared', FS_S, S1)
s.text(mid_l, BAND_Y + 7.3, 'after the award the comparison cannot be repeated', FS_XS, S1)
s.text(mid_r, BAND_Y + 3.8, 'one forecast exists', FS_S, GREY, weight='bold')
s.text(mid_r, BAND_Y + 7.3, 'the other two are no longer issued', FS_XS, GREY)
s.line(SPLIT, CONT_Y + CONT_H + 0.6, SPLIT, BAND_Y, color=ACCENT, sw=0.30, dash='1.3 1.2')
s.text(SPLIT + 1.8, BAND_Y - 1.0, 'from here on the alternatives are gone', FS_XS, ACCENT,
       anchor='start')

svg = s.render()
out_svg = os.path.join(SVG_DIR, 'fig1_chain.svg')
open(out_svg, 'w').write(svg)
print('wrote', out_svg)

for ext in ('pdf', 'png'):
    out = os.path.join(FIG_DIR, f'fig1_chain.{ext}')
    args = ['-f', ext] + (['-w', '1938'] if ext == 'png' else [])
    subprocess.run(['rsvg-convert', *args, '-o', out, out_svg], check=True)
    print('wrote', out, f'{os.path.getsize(out)/1024:.0f} KB')
