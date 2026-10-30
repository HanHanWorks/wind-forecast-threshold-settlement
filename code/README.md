# Code inventory

Everything the paper's figures, tables and numbers are made of.

## `figures/` — the figures

| script | produces | notes |
|---|---|---|

## `stats/` — the numbers

| script | produces | where it appears |
|---|---|---|
| `recompute_two_source.py` | `two_source_numbers.json` | every headline number: Tables 1–3, 5, 7, §4 resolution analysis, vendor-replicate integrity check, generation denominators |
| `g6_resolution.py` | `g6_pairs.csv`, `g6_resolution.csv` | §4.3 moving-block bootstrap resolution curves |
| `gap_noise.py` | `gap_noise.json` | Table 6 (sampling noise of farm-month statistics) |
| `make_tab_noise.py` | `tab6_noise.tex` | Table 6 LaTeX |
| `var_decomp.py` | `var_decomp.json` | §5.2 variance decomposition |
| `mechanism_reg2.py` | `mechanism_reg2.json` | §5.2 weather-proxy regressions (needs raw operational record) |
| `clones.py` | — | §3.4 data-integrity check (duplicated series detection) |

## `pipeline/` — raw record → analysis panels

Runs where the raw operational exports live (see `pipeline/README.md`).
`p2_v5_pipeline.py` computes the official accuracy definition and the assessed
energy ledger; `p2_extend.py` extends the panel to the end of the record.

## `exploratory/` — provenance

One-off analyses and superseded generators, kept so the analysis trail is
complete. Not needed to reproduce the paper; see `exploratory/README.md`.
