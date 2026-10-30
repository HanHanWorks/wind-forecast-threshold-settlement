# Wind forecast accuracy is a hinge, not a dial

Code for the paper:

> **One accuracy point is not one accuracy point: the threshold-shaped value of
> day-ahead wind forecast accuracy under grid-code assessment**
> *(manuscript under review — full citation to be added upon acceptance)*

The paper reconstructs, at the resolution it is applied (the farm-month), the
settlement rule that converts day-ahead wind forecast accuracy into assessed
energy under a threshold-based grid code, and shows that the marginal value of
accuracy is zero above the threshold and proportional to installed capacity
below it.

## What is in this repository

| Path | Contents |
|---|---|
| `code/figures/` | Hand-drawn SVG figure generator (Fig. 1, 5) and matplotlib figures (Fig. 2, 3, 4, 6) |
| `code/stats/` | Every headline number in the paper: recomputation, bootstrap resolution analysis, noise decomposition, integrity checks |
| `code/pipeline/` | Upstream pipeline: raw operational record → analysis-ready panels (runs where the raw data lives) |
| `code/exploratory/` | One-off analyses and superseded scripts kept for provenance |
| `data/` | Data dictionary, availability statement, and a synthetic sample-data generator |
| `outputs/` | Generated figures and tables (git-ignored), plus `outputs/expected/` with the published aggregates |
| `reproduce.sh` | One-command end-to-end run |

## Quick start

```bash
pip install -r requirements.txt   # python >= 3.8, matplotlib >= 3.3
bash reproduce.sh                 # generates sample data, then runs everything
```

`reproduce.sh` fabricates a synthetic record (`data/make_sample_data.py`) with
the same schema as the real one, then reproduces every figure, table and
headline number from it. Outputs land in `outputs/figures/`,
`outputs/figures_svg/`, `outputs/tables/` and `data/v5/*.json`.

Figure 5's bootstrap curve is drawn from the published constants in
`code/figures/make_fig1_nature.py`; every other figure and statistic is
computed from whatever record is present in `data/`.

## Data availability

The operational record analysed in this paper — day-ahead forecasts and actual
output at 15-minute resolution for 25 wind farms connected to a provincial
dispatch centre in southern China (January 2023 – August 2025) — was provided
under a data-sharing agreement and **cannot be redistributed**, in whole or in
part. This repository therefore contains **code only**.

To make the code runnable without the record:

* `data/README.md` documents every input file, column and unit;
* `data/make_sample_data.py` generates a synthetic sample with the same schema.
  The sample resembles no real plant, forecast or settlement, and is for testing
  the software only — numbers produced from it are not the paper's results;
* `outputs/expected/two_source_numbers.json` records the published aggregate
  statistics (all of which appear in the paper itself) as a reference target.

Derived tables sufficient to reproduce every figure and table of the paper are
available from the corresponding author on reasonable request, subject to the
data-sharing agreement.

## Environment

* Python ≥ 3.8
* pandas, numpy, matplotlib ≥ 3.3 (`requirements.txt`)
* [`rsvg-convert`](https://gitlab.gnome.org/GNOME/librsvg) (from `librsvg`) to
  convert the hand-drawn SVG figures to PDF/PNG; on macOS `brew install librsvg`

## Reproducing the published record

With the confidential record placed as described in `data/README.md`, the same
`reproduce.sh` reproduces the paper. `code/stats/recompute_two_source.py`
writes `data/v5/two_source_numbers.json`, which contains every headline number
quoted in the text, tables and abstract; `code/pipeline/` documents how the
analysis-ready panels are built from the raw operational exports.

## Citation and license

Please cite the paper when using this code. Code released under the MIT
License — see `LICENSE`. Fill in the author list in `LICENSE` and the citation
block above before publishing the repository.
