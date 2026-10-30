# Exploratory and superseded scripts

Kept for provenance; **not needed to reproduce the paper**. Each reads the
analysis panels in `data/` and prints or writes small diagnostics.

| script | what it was for |
|---|---|
| `recompute.py` | earlier recomputation over candidate pools (superseded by `stats/recompute_two_source.py`) |
| `tie.py`, `tiebreak.py`, `sig_gap.py` | tie rates between candidates, significance of gaps |
| `season.py`, `nested.py`, `pool.py`, `ladder2.py`, `detail365.py` | seasonal structure, window/pool sensitivity, long-window detail |
| `econ2.py`, `econ3.py` | early monetary illustrations (replaced by the tariff arithmetic in §4.2) |
| `make_fig1_svg.py`, `make_figs2.py`, `make_figures_latex.py`, `make_latex_tables.py` | superseded figure/table generators (replaced by `code/figures/` and `code/stats/make_tab_noise.py`) |
