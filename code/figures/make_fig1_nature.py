#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fig. 1  --  hand-drawn SVG, journal camera-ready (164 mm x 128 mm).

Design brief
------------
One idea: a 3-point-wide ranking is taken once, one series is locked, and a
threshold rule then converts only that series into money cell by cell.

  a  the chain over time: three candidate sources, one award, two deletions
  b  the ledger: 25 farms x 32 months, coloured by which side of the threshold
  c  the hinge: what the rule pays for, and where the 545 cells actually sit

Everything is drawn from primitives (no plotting library). All numbers are
read from 01_data/v5/ and 01_data/daily_acc_panel.csv.

Output: 13_latex/figures_svg/fig1_chain.svg
        13_latex/figures/fig1_chain.pdf   (rsvg-convert)
"""
import os
import csv
import math
import subprocess

BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
SVG_DIR = os.path.join(BASE, 'outputs', 'figures_svg')
FIG_DIR = os.path.join(BASE, 'outputs', 'figures')
FM_CSV = os.path.join(BASE, 'data', 'v5', 'farmmonth_v2_ext.csv')
DAY_CSV = os.path.join(BASE, 'data', 'daily_acc_panel.csv')

# ---------------------------------------------------------------- palette
INK = '#15171C'
BODY = '#2B2F36'
MUTE = '#6E7683'
FAINT = '#AAB2BE'
RULE = '#D9DEE5'
HAIR = '#EBEEF2'
WASH = '#F4F5F7'
ACCENT = '#A33A28'          # the locked / charged colour
ACCENT_S = '#C4664F'        # lighter accent, for fills
PALE = '#EDC9BD'            # lightest charge
FLAT = '#C2CDD9'            # above threshold: no value
FLAT_S = '#B9C5D3'
FAM = 'Helvetica Neue, Helvetica, Arial, sans-serif'

# ---------------------------------------------------------------- type (mm)
T_LET = 3.05
T_HEAD = 2.52
T_MAIN = 2.36
T_SM = 2.14
T_TINY = 1.98
T_MIC = 1.92

W, H = 164.0, 128.0


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def hx2rgb(c):
    c = c.lstrip('#')
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def lerp(c1, c2, t):
    a, b = hx2rgb(c1), hx2rgb(c2)
    return '#%02X%02X%02X' % tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


class Svg:
    def __init__(self, w=W, h=H):
        self.p = []
        self.defs = []
        self.w, self.h = w, h

    # ---- primitives
    def line(self, x1, y1, x2, y2, stroke=BODY, w=0.3, dash=None, cap='butt', op=1.0, arrow=False):
        d = ' stroke-dasharray="%s"' % dash if dash else ''
        a = ' marker-end="url(#%s)"' % ('ah' if arrow is True else arrow) if arrow else ''
        self.p.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" '
                      'stroke-width="%.2f" stroke-linecap="%s"%s%s opacity="%.2f"/>'
                      % (x1, y1, x2, y2, stroke, w, cap, d, a, op))

    def path(self, d, stroke=BODY, w=0.3, fill='none', dash=None, cap='butt', join='miter',
             op=1.0, arrow=False):
        da = ' stroke-dasharray="%s"' % dash if dash else ''
        a = ' marker-end="url(#%s)"' % ('ah' if arrow is True else arrow) if arrow else ''
        self.p.append('<path d="%s" fill="%s" stroke="%s" stroke-width="%.2f" '
                      'stroke-linecap="%s" stroke-linejoin="%s"%s%s opacity="%.2f"/>'
                      % (d, fill, stroke, w, cap, join, da, a, op))

    def rect(self, x, y, w, h, fill='none', stroke='none', sw=0.25, rx=0.0, dash=None, op=1.0):
        r = ' rx="%.2f"' % rx if rx else ''
        d = ' stroke-dasharray="%s"' % dash if dash else ''
        self.p.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="%s" '
                      'stroke="%s" stroke-width="%.2f"%s%s opacity="%.2f"/>'
                      % (x, y, w, h, fill, stroke, sw, r, d, op))

    def circle(self, cx, cy, r, fill='none', stroke='none', sw=0.25, op=1.0):
        self.p.append('<circle cx="%.2f" cy="%.2f" r="%.2f" fill="%s" stroke="%s" '
                      'stroke-width="%.2f" opacity="%.2f"/>' % (cx, cy, r, fill, stroke, sw, op))

    def text(self, x, y, s, size=T_MAIN, fill=BODY, anchor='start', weight='normal',
             style='normal', ls=0.0, rot=None, op=1.0):
        tr = ' transform="rotate(%.1f %.2f %.2f)"' % (rot, x, y) if rot is not None else ''
        l = ' letter-spacing="%.2f"' % ls if ls else ''
        self.p.append('<text x="%.2f" y="%.2f" font-family="%s" font-size="%.2f" fill="%s" '
                      'text-anchor="%s" font-weight="%s" font-style="%s"%s%s opacity="%.2f">%s</text>'
                      % (x, y, FAM, size, fill, anchor, weight, style, l, tr, op, esc(s)))

    def rich(self, x, y, parts, size=T_MAIN, fill=BODY, anchor='start', ls=0.0):
        """parts = [(text, {opts})] rendered as one text element with tspans."""
        tr = []
        for txt, o in parts:
            attrs = ''
            if o.get('w'):
                attrs += ' font-weight="%s"' % o['w']
            if o.get('st'):
                attrs += ' font-style="%s"' % o['st']
            if o.get('fill'):
                attrs += ' fill="%s"' % o['fill']
            if o.get('size'):
                attrs += ' font-size="%.2f"' % o['size']
            if o.get('dx'):
                attrs += ' dx="%.2f"' % o['dx']
            if o.get('dy'):
                attrs += ' dy="%.2f"' % o['dy']
            if o.get('ls'):
                attrs += ' letter-spacing="%.2f"' % o['ls']
            tr.append('<tspan%s>%s</tspan>' % (attrs, esc(txt)))
        l = ' letter-spacing="%.2f"' % ls if ls else ''
        self.p.append('<text x="%.2f" y="%.2f" font-family="%s" font-size="%.2f" fill="%s" '
                      'text-anchor="%s" xml:space="preserve"%s>%s</text>'
                      % (x, y, FAM, size, fill, anchor, l, ''.join(tr)))

    def render(self):
        head = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<svg xmlns="http://www.w3.org/2000/svg" width="%gmm" height="%gmm" '
                'viewBox="0 0 %g %g" version="1.1">\n' % (self.w, self.h, self.w, self.h))
        defs = ('<defs>\n'
                ' <marker id="ah" viewBox="0 0 6 6" refX="5.2" refY="3" markerWidth="4.2" '
                'markerHeight="4.2" orient="auto-start-reverse">'
                '<path d="M0.4,0.7 L5.4,3 L0.4,5.3" fill="none" stroke="%s" '
                'stroke-width="1.1" stroke-linecap="round" stroke-linejoin="round"/></marker>\n'
                ' <marker id="ahg" viewBox="0 0 6 6" refX="5.2" refY="3" markerWidth="4.0" '
                'markerHeight="4.0" orient="auto-start-reverse">'
                '<path d="M0.4,0.7 L5.4,3 L0.4,5.3" fill="none" stroke="%s" '
                'stroke-width="1.1" stroke-linecap="round" stroke-linejoin="round"/></marker>\n'
                ' <marker id="ahf" viewBox="0 0 6 6" refX="5.2" refY="3" markerWidth="4.0" '
                'markerHeight="4.0" orient="auto-start-reverse">'
                '<path d="M0.4,0.7 L5.4,3 L0.4,5.3" fill="none" stroke="%s" '
                'stroke-width="1.1" stroke-linecap="round" stroke-linejoin="round"/></marker>\n'
                '</defs>\n' % (BODY, FAINT, FAINT))
        body = ('<rect x="0" y="0" width="%g" height="%g" fill="#FFFFFF"/>\n' % (self.w, self.h))
        return head + defs + body + '\n'.join(self.p) + '\n</svg>\n'


# ---------------------------------------------------------------- data
def load():
    rows = []
    with open(FM_CSV) as f:
        for r in csv.DictReader(f):
            def fnum(v):
                try:
                    return float(v)
                except (TypeError, ValueError):
                    return None
            rows.append(dict(ym=r['ym'], farm=r['farm_id'],
                             s1=fnum(r['src1']), s2=fnum(r['src2']), vf=fnum(r['vendorF']),
                             cap=fnum(r['Cap']), E2=fnum(r['E_src2']), days=fnum(r['days'])))
    months = sorted({r['ym'] for r in rows})
    # farm order: by mean installed capacity, largest first
    capsum = {}
    for r in rows:
        capsum.setdefault(r['farm'], []).append(r['cap'])
    order = sorted(capsum, key=lambda k: -sum(capsum[k]) / len(capsum[k]))
    return rows, months, order


def load_daily(farm, ym):
    out = []
    with open(DAY_CSV) as f:
        for r in csv.DictReader(f):
            if r['farm_id'] == farm and r['date'][:7] == ym:
                v = r['acc_S02_src2']
                if v:
                    out.append((r['date'], float(v)))
    out.sort()
    return out


ROWS, MONTHS, ORDER = load()
CELL = {(r['ym'], r['farm']): r for r in ROWS}
NM = len(MONTHS)          # 32
NF = len(ORDER)           # 25

# the three-source window (the distribution used in panel c)
TRI = [r for r in ROWS if r['s1'] is not None and r['s2'] is not None
       and r['ym'] <= '2025-05']
ACC = [r['s2'] for r in TRI]
N_ABOVE = sum(1 for a in ACC if a >= 60)

# zoom cell
ZFARM, ZYM = None, None   # pin a (farm_id, ym) here to force the zoom cell;
                          # left unset, a qualifying cell is picked automatically
if (ZYM, ZFARM) not in CELL:  # published cell absent (e.g. synthetic sample data)
    import collections as _c
    _days = {}
    for _r in ROWS:
        if _r['s2'] is not None and _r['ym'] <= '2025-05':
            _days[(_r['ym'], _r['farm'])] = _r.get('days', 0)
    _cand = [k for k, v in _days.items() if v >= 27 and k in CELL
             and CELL[k]['s2'] is not None and 44 <= CELL[k]['s2'] <= 58]
    if not _cand:
        _cand = [k for k in CELL if CELL[k]['s2'] is not None]
    ZYM, ZFARM = sorted(_cand)[len(_cand) // 2]
    print('zoom cell fallback ->', ZFARM, ZYM)
ZC = CELL[(ZYM, ZFARM)]
ZDAYS = load_daily(ZFARM, ZYM)

s = Svg()

# ================================================================ PANEL a
# time axis 2023-01 .. 2025-08, award at 2024-01
AX_L, AX_R = 30.0, 156.0
TOT = NM - 1.0


def xt(t):
    return AX_L + (AX_R - AX_L) * t / TOT


XA = xt(12.0)              # award: 2024-01
Y_S1, Y_IN, Y_VF = 27.0, 34.2, 34.2
Y_AX = 41.6

s.text(0, 7.6, 'a', size=T_LET, fill=INK, weight='bold')

# --- phase brackets
BR = 11.6
for x0, x1, lab, sub in ((AX_L, XA, 'TRIAL YEAR', '12-month backtest \u00b7 2 candidates'),
                         (XA, AX_R, 'ASSESSMENT YEAR', '1 awarded source \u00b7 replayed month by month')):
    s.line(x0, BR, x1, BR, stroke=FAINT, w=0.26)
    s.line(x0, BR - 1.5, x0, BR, stroke=FAINT, w=0.26)
    s.line(x1, BR - 1.5, x1, BR, stroke=FAINT, w=0.26)
    s.text((x0 + x1) / 2.0, BR - 2.6, lab, size=T_SM, fill=INK, anchor='middle',
           weight='bold', ls=0.30)
    s.text(x0 + 0.9, BR + 3.5, sub, size=T_MIC, fill=MUTE, anchor='start')

# --- trial-year field (very light, behind the lanes)
s.rect(AX_L, 17.6, XA - AX_L, 21.2, fill='#F2F4F7')

# --- lanes
LANES = [('Source 1', 'challenger', Y_S1), ('Source 2', 'incumbent', Y_IN)]
for name, tag, y in LANES:
    parts = [(name, {})]
    if tag:
        parts.append((' \u00b7 ' + tag, {'st': 'italic', 'fill': MUTE, 'size': T_SM}))
    s.rich(AX_L - 4.0, y + 0.78, parts, size=T_MAIN, fill=BODY, anchor='end')

# pre-award: both candidates, equal weight
for name, tag, y in LANES:
    s.line(AX_L, y, XA, y, stroke='#5A6270', w=0.34)
    s.circle(AX_L, y, 0.42, fill='#5A6270')

# post-award: incumbent locked, the other two cease
s.line(XA, Y_IN, AX_R - 0.6, Y_IN, stroke=ACCENT, w=0.62, cap='round', arrow=True)
s.circle(XA, Y_IN, 0.95, fill='#FFFFFF', stroke=ACCENT, sw=0.45)
for name, tag, y in LANES:
    if y == Y_IN:
        continue
    s.line(XA + 1.0, y, XA + 13.0, y, stroke=FAINT, w=0.30, dash='0.55 0.85', op=0.85)
    s.circle(XA + 13.6, y, 0.55, fill='#FFFFFF', stroke=FAINT, sw=0.26)
    s.line(XA + 13.1, y, XA + 14.1, y, stroke='#FFFFFF', w=0.9)
    s.line(XA + 13.1, y - 0.40, XA + 14.1, y + 0.40, stroke=MUTE, w=0.28)

# award marker
s.line(XA, BR - 1.4, XA, Y_AX, stroke=INK, w=0.26, dash='1.0 1.1')
s.text(XA - 1.5, Y_S1 - 3.0, 'AWARD', size=T_MIC, fill=INK, anchor='end', ls=0.24)

# right-hand annotation on the locked lane
s.text(AX_R, Y_IN - 1.7, 'the only series priced', size=T_MIC, fill=ACCENT, anchor='end')
s.text(XA + 15.2, Y_S1 - 1.4, 'not issued after the award', size=T_MIC, fill=MUTE)

# --- axis
s.line(AX_L, Y_AX, AX_R, Y_AX, stroke=RULE, w=0.30)
for t in (0, 6, 12, 18, 24, 30, 32):
    s.line(xt(t), Y_AX, xt(t), Y_AX + 1.15, stroke=RULE, w=0.30)
for a, b, lab in ((0, 12, '2023'), (12, 24, '2024'), (24, 32, '2025')):
    s.text((xt(a) + xt(b)) / 2.0, Y_AX + 4.1, lab, size=T_SM, fill=MUTE, anchor='middle', ls=0.18)

# --- stamp line
s.line(AX_L, 49.2, AX_R, 49.2, stroke=HAIR, w=0.30)
s.rich(AX_L, 51.4, [
    ('620 farm-months', {'w': 'bold'}),
    ('  25 wind farms  \u00b7  32 months  \u00b7  Jan 2023 \u2013 Aug 2025', {'fill': MUTE}),
], size=T_MIC, fill=BODY)

# ================================================================ PANEL b
GX, GY = 11.0, 70.6
CW = 1.55
GW, GH = CW * NM, CW * NF

s.text(0, 61.8, 'b', size=T_LET, fill=INK, weight='bold')
s.text(4.6, 61.8, 'One cell is one settlement', size=T_HEAD, fill=INK, weight='bold')

# year labels above the grid
for a, b, lab in ((0, 12, '2023'), (12, 24, '2024'), (24, 32, '2025')):
    s.text(GX + CW * (a + b) / 2.0, GY - 1.5, lab, size=T_MIC, fill=MUTE, anchor='middle', ls=0.18)

s.rect(GX, GY, GW, GH, fill=WASH)
s.rect(GX, GY, GW, GH, fill='none', stroke=RULE, sw=0.24)

# cells
r_i = {f: i for i, f in enumerate(ORDER)}
for ym in MONTHS:
    j = MONTHS.index(ym)
    for f in ORDER:
        r = CELL.get((ym, f))
        if r is None or r['s2'] is None:
            continue
        a = r['s2']
        if a >= 60:
            fill = FLAT
        else:
            t = min(1.0, (60.0 - a) / 27.0) ** 1.30
            fill = lerp(PALE, '#85281A', t)
        s.rect(GX + j * CW + 0.05, GY + r_i[f] * CW + 0.05, CW - 0.10, CW - 0.10, fill=fill)

# highlight the zoom cell
jz = MONTHS.index(ZYM)
iz = r_i[ZFARM]
cx0, cy0 = GX + jz * CW, GY + iz * CW
s.rect(cx0 - 0.55, cy0 - 0.55, CW + 1.10, CW + 1.10, fill='none', stroke='#FFFFFF', sw=0.55)
s.rect(cx0 - 0.42, cy0 - 0.42, CW + 0.84, CW + 0.84, fill='none', stroke=INK, sw=0.30)

# grid axes labels
s.text(GX - 2.2, GY + GH / 2.0, '25 wind farms', size=T_MIC, fill=MUTE, anchor='middle', rot=-90)

# ---- zoom
ZX0, ZX1 = 66.0, 100.0
ZY0, ZY1 = 73.4, 89.4
s.rect(ZX0, ZY0, ZX1 - ZX0, ZY1 - ZY0, fill='#FCFCFD')
s.rect(ZX0, ZY0, ZX1 - ZX0, ZY1 - ZY0, fill='none', stroke=HAIR, sw=0.3)

# connector from cell to zoom: out, up, then into the box
ymid = ZY0 + 8.6
s.path('M%.2f,%.2f L%.2f,%.2f L%.2f,%.2f L%.2f,%.2f' % (
    cx0 + CW + 0.2, cy0 + CW / 2.0,
    ZX0 - 3.0, cy0 + CW / 2.0,
    ZX0 - 3.0, ymid,
    ZX0 - 0.5, ymid), stroke=MUTE, w=0.24, arrow=True)

yvals = [v for _, v in ZDAYS]
ymin = math.floor(min(yvals) / 10.0) * 10
ymax = max(70.0, math.ceil(max(yvals) / 10.0) * 10)


def zy(v):
    return ZY1 - (v - ymin) / (ymax - ymin) * (ZY1 - ZY0 - 3.0) - 1.4


def zx(i):
    return ZX0 + 2.0 + (ZX1 - ZX0 - 4.0) * i / max(1, len(ZDAYS) - 1)


# threshold
if ymin < 60 < ymax:
    s.line(ZX0 + 1.2, zy(60), ZX1 - 1.2, zy(60), stroke=FAINT, w=0.24, dash='0.9 0.7')
    s.text(ZX0 + 3.0, zy(60) - 0.9, '\u03b8', size=T_MIC, fill=MUTE, style='italic')

for i, v in enumerate(yvals):
    s.circle(zx(i), zy(v), 0.36, fill='#4A525E', op=0.62)
mz = sum(yvals) / len(yvals)
s.line(ZX0 + 1.1, zy(mz), ZX1 - 1.5, zy(mz), stroke=ACCENT, w=0.38)


s.text(ZX0, 71.4, '2024-11  \u00b7  day by day', size=T_MIC, fill=MUTE)
s.rich(ZX0, ZY1 + 2.6, [('monthly ACC', {}),
                        (' = mean of %d days = ' % len(ZDAYS), {'fill': MUTE}),
                        ('%.1f' % mz, {'fill': ACCENT, 'w': 'bold'})], size=T_MIC, fill=BODY)

# ---- equation
EQY = 97.4
LBL_W = 2.6
s.text(ZX0, EQY, 'the cell is then priced', size=T_MIC, fill=MUTE)

s.rich(ZX0, EQY + 3.4, [('E', {'st': 'italic'})], size=T_MAIN, fill=BODY)
s.text(ZX0 + LBL_W, EQY + 3.4, '=', size=T_MAIN, fill=MUTE)
s.rich(ZX0 + LBL_W + 2.2, EQY + 3.4, [
    ('Cap', {'st': 'italic'}), ('  \u00b7  ', {'fill': MUTE}),
    ('k', {'st': 'italic'}), ('  \u00b7  max(0, ', {}),
    ('\u03b8', {'st': 'italic'}), (' \u2212 ', {}), ('ACC', {'st': 'italic'}), (')', {}),
], size=T_MAIN, fill=BODY)

E_val = ZC['E2']
s.text(ZX0 + LBL_W, EQY + 7.1, '=', size=T_SM, fill=MUTE)
s.rich(ZX0 + LBL_W + 2.2, EQY + 7.1, [
    ('%.0f' % ZC['cap'], {}), (' MW \u00d7 0.2 h \u00d7 (60 \u2212 %.1f)'
                              % ZC['s2'], {}),
], size=T_SM, fill=BODY)

s.text(ZX0 + LBL_W, EQY + 10.8, '=', size=T_SM, fill=MUTE)
s.rich(ZX0 + LBL_W + 2.2, EQY + 10.8, [
    ('%.0f' % round(E_val), {'w': 'bold'}), (' MWh', {'w': 'bold'}),
], size=T_SM, fill=ACCENT)

# ---- legend
LY = GY + GH + 5.6
s.rect(GX, LY, 2.4, 1.3, fill=lerp(PALE, '#8E2B1B', 0.75))
s.text(GX + 3.4, LY + 1.2, 'below \u03b8: charged', size=T_MIC, fill=BODY)
s.rect(GX + 24.0, LY, 2.4, 1.3, fill=FLAT)
s.text(GX + 27.4, LY + 1.2, 'above \u03b8: nothing', size=T_MIC, fill=BODY)
s.rect(GX + 47.0, LY, 2.4, 1.3, fill=WASH, stroke=RULE, sw=0.2)
s.text(GX + 50.4, LY + 1.2, 'no farm yet', size=T_MIC, fill=BODY)

# ---- footnote
s.text(GX, LY + 6.4, 'Each cell is the monthly accuracy of one farm under the awarded system.',
       size=T_MIC, fill=MUTE)
s.text(GX, LY + 9.8, 'Daily and annual aggregation would each hide the kink.', size=T_MIC, fill=MUTE)

# ================================================================ PANEL c
CX0, CX1 = 124.0, 162.0
A0, A1 = 40.0, 85.0


def cx(a):
    return CX0 + (a - A0) / (A1 - A0) * (CX1 - CX0)


# --- histogram (545 three-source farm-months)
HY0, HY1 = 86.4, 68.6
NB = 45
counts = [0] * NB
for a in ACC:
    k = int(math.floor(a - A0))
    if 0 <= k < NB:
        counts[k] += 1
cmax = max(counts)
bw = (CX1 - CX0) / NB
for k, c in enumerate(counts):
    if c == 0:
        continue
    h = c / cmax * (HY0 - HY1)
    fill = FLAT if (k * 1.0 + A0) >= 60 else ACCENT_S
    s.rect(CX0 + k * bw + 0.06, HY0 - h, bw - 0.12, h, fill=fill)

s.line(CX0, HY0, CX1, HY0, stroke=RULE, w=0.30)

# --- curve: assessed energy for a 100 MW farm
CY0, CY1 = 88.6, 117.4
EMAX = 400.0


def cy(e):
    return CY1 - e / EMAX * (CY1 - CY0)


for e in (0, 200, 400):
    s.line(CX0, cy(e), CX1, cy(e), stroke=HAIR if e else RULE, w=0.26 if e else 0.34)
    s.text(CX0 - 1.6, cy(e) + 0.7, '%d' % e, size=T_MIC, fill=MUTE, anchor='end')

pts = []
a = A0
while a <= 60.0 + 1e-9:
    pts.append((cx(a), cy(20.0 * (60.0 - a))))
    a += 0.5
d = 'M' + ' L'.join('%.2f,%.2f' % p for p in pts)
# fill under the slope
s.path(d + ' L%.2f,%.2f Z' % (cx(60), cy(0)), fill=PALE, stroke='none', op=0.6)
s.path(d + ' L%.2f,%.2f' % (CX1, cy(0)), stroke=ACCENT, w=0.66, cap='round', join='round')

# threshold line
s.line(cx(60), HY1 - 1.2, cx(60), CY1, stroke=INK, w=0.26, dash='1.0 1.1')

# split shares between the two sub-panels
share_above = N_ABOVE / len(ACC) * 100.0
s.text(cx(60) - 1.0, HY0 + 3.4, '%.0f %%' % (100 - share_above), size=T_MIC, fill=ACCENT,
       anchor='end', weight='bold')
s.text(cx(60) + 1.0, HY0 + 3.4, '%.0f %%' % share_above, size=T_MIC, fill=MUTE, weight='bold')

# callout on the slope, inside the charged region
s.text(cx(41.0), cy(72), 'one point', size=T_MIC, fill=BODY)
s.text(cx(41.0), cy(72) + 3.0, '= 20 MWh', size=T_MIC, fill=BODY)

# the empty right half carries the "nothing above the threshold" statement
s.text(cx(60) + 1.3, 95.4, '\u03b8 = 60 %', size=T_MIC, fill=INK, style='italic')
s.text(cx(60) + 1.3, 101.6, 'one point = 0', size=T_MIC, fill=MUTE)

# axes
for a in (40, 50, 60, 70, 80):
    s.line(cx(a), CY1, cx(a), CY1 + 1.1, stroke=RULE, w=0.26)
    s.text(cx(a), CY1 + 4.0, '%d' % a, size=T_MIC, fill=MUTE, anchor='middle')
s.text((CX0 + CX1) / 2.0, CY1 + 8.0, 'monthly accuracy ACC (%)', size=T_SM, fill=BODY, anchor='middle')
s.text(CX0 - 8.6, (CY0 + CY1) / 2.0, 'assessed energy (MWh)', size=T_SM,
       fill=BODY, anchor='middle', rot=-90)


# header
s.text(106, 61.8, 'c', size=T_LET, fill=INK, weight='bold')
s.text(110.6, 61.8, 'The rule prices a hinge, not a slope', size=T_HEAD, fill=INK, weight='bold')
s.text(CX0, 66.2, '545 farm-months, awarded system', size=T_MIC, fill=MUTE)

out = s.render()
os.makedirs(SVG_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)
svg_path = os.path.join(SVG_DIR, 'fig1_chain.svg')
with open(svg_path, 'w') as f:
    f.write(out)
print('wrote', svg_path)

pdf = os.path.join(FIG_DIR, 'fig1_chain.pdf')
png = os.path.join(FIG_DIR, 'fig1_preview.png')
subprocess.run(['rsvg-convert', '-f', 'pdf', svg_path, '-o', pdf], check=True)
subprocess.run(['rsvg-convert', '-f', 'png', '-z', '3.2', svg_path, '-o', png], check=True)
print('wrote', pdf, png)


# ================================================================ FIG. 5
# Resolution of the difference between the two systems. Single curve, hand-drawn,
# same visual language as Fig. 1.  Data: moving-block bootstrap of the 906-day
# daily fleet-mean difference (see recompute_two_source.py).
FW, FH = 141.0, 80.0
f = Svg(FW, FH)
X0, X1, Y0, Y1 = 26.0, 133.0, 15.0, 57.0
LX0, LX1 = math.log(25.0), math.log(430.0)
LY0, LY1 = math.log(0.25), math.log(9.0)


def fx(L):
    return X0 + (math.log(L) - LX0) / (LX1 - LX0) * (X1 - X0)


def fy(v):
    return Y1 - (math.log(v) - LY0) / (LY1 - LY0) * (Y1 - Y0)


CURVE = [(30, 6.265), (45, 5.254), (60, 4.499), (75, 3.889), (90, 3.481), (105, 3.084),
         (120, 2.787), (150, 2.398), (180, 2.134), (240, 1.706), (300, 1.467), (365, 1.226)]
GAP = 3.043
LCROSS = 107.0

# the monthly accounting period the rule uses
f.rect(X0, Y0, fx(30) - X0, Y1 - Y0, fill='#F2F4F7')
f.line(fx(30), Y0, fx(30), Y1, stroke=FAINT, w=0.28, dash='1.0 1.1')

# y grid
for v in (0.5, 1, 2, 3, 5):
    f.line(X0, fy(v), X1, fy(v), stroke=HAIR, w=0.26)
    f.text(X0 - 1.7, fy(v) + 0.65, ('%.1f' % v).rstrip('0').rstrip('.') if v < 1 else '%d' % v,
           size=T_MIC, fill=MUTE, anchor='end')

# the gap line
f.line(X0, fy(GAP), X1, fy(GAP), stroke=ACCENT, w=0.34, dash='1.6 1.2')
f.text(X1 - 1.0, fy(GAP) - 1.15, 'the gap that exists: 3.0 points', size=T_MIC,
       fill=ACCENT, anchor='end')

# curve
d = 'M' + ' L'.join('%.2f,%.2f' % (fx(L), fy(v)) for L, v in CURVE)
f.path(d, stroke=BODY, w=0.62, cap='round', join='round')
for L, v in CURVE:
    f.circle(fx(L), fy(v), 0.34, fill=BODY)

# crossing
f.circle(fx(LCROSS), fy(GAP), 1.15, fill='#FFFFFF', stroke=ACCENT, sw=0.52)
f.line(fx(LCROSS), fy(GAP) + 1.6, fx(LCROSS), fy(GAP) + 6.2, stroke=MUTE, w=0.24)
f.text(fx(LCROSS) + 1.2, fy(GAP) + 7.6, '107 days to resolve it', size=T_MIC, fill=BODY)
f.text(fx(LCROSS) + 1.2, fy(GAP) + 10.6, 'the accounting period is 30', size=T_MIC, fill=MUTE)

# band label
for i, ln in enumerate(('30-day', 'monthly', 'accounting')):
    f.text(fx(33), Y1 - 7.6 + i * 2.4, ln, size=T_MIC, fill=MUTE)

# axes
f.line(X0, Y1, X1, Y1, stroke=RULE, w=0.32)
f.line(X0, Y0, X0, Y1, stroke=RULE, w=0.32)
for L in (30, 60, 90, 120, 180, 270, 365):
    f.line(fx(L), Y1, fx(L), Y1 + 1.15, stroke=RULE, w=0.28)
    f.text(fx(L), Y1 + 4.1, '%d' % L, size=T_MIC, fill=MUTE, anchor='middle')
f.text((X0 + X1) / 2.0, Y1 + 8.2, 'window length L (days, log scale)', size=T_SM,
       fill=BODY, anchor='middle')
f.text(X0 - 8.6, (Y0 + Y1) / 2.0, 'minimum resolvable difference (points, log scale)',
       size=T_SM, fill=BODY, anchor='middle', rot=-90)

svg5 = f.render()
p5 = os.path.join(SVG_DIR, 'fig5_resolution.svg')
with open(p5, 'w') as fh:
    fh.write(svg5)
print('wrote', p5)
subprocess.run(['rsvg-convert', '-f', 'pdf', p5, '-o', os.path.join(FIG_DIR, 'fig5_resolution.pdf')], check=True)
subprocess.run(['rsvg-convert', '-f', 'png', '-z', '3.0', p5, '-o', os.path.join(FIG_DIR, 'fig5_resolution.png')], check=True)
print('wrote fig5 pdf/png')
