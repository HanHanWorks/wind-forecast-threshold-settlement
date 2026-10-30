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
| `code/stats/` | Every headline number in the paper: recomputation, bootstrap resolution analysis, noise decomposition, integrity checks |
| `code/pipeline/` | Upstream pipeline: raw operational record → analysis-ready panels (runs where the raw data lives) |
| `code/exploratory/` | One-off analyses and superseded scripts kept for provenance |
| `data/` | Data dictionary, availability statement, and a synthetic sample-data generator |
| `outputs/` | Generated tables and statistics (git-ignored) |
| `reproduce.sh` | One-command end-to-end run (statistics and tables) |

## Quick start

```bash
pip install -r requirements.txt   # python >= 3.8, matplotlib >= 3.3
bash reproduce.sh                 # generates sample data, then runs everything
```

`reproduce.sh` fabricates a synthetic record (`data/make_sample_data.py`) with
the same schema as the real one, then reproduces every figure, table and
headline number from it. Outputs land in `outputs/figures/`,
`outputs/figures_svg/`, `outputs/tables/` and `data/v5/*.json`.

Every statistic is computed from whatever record is present in `data/`.
The figure-generation scripts used for the manuscript are not part of this
release.

## Data availability

The operational record analysed in this paper — day-ahead forecasts and actual
output at 15-minute resolution for 25 wind farms connected to a provincial
dispatch centre in southern China (January 2023 – August 2025) — was provided
under a data-sharing agreement and **cannot be redistributed**, in whole or in
part. This repository contains the analysis code and a synthetic sample-data
generator. It does not contain the confidential operational data or record-level
derived data.

To make the code runnable without the record:

* `data/README.md` documents the input schemas needed to run the analysis on an
  authorised local copy of the operational record;
* `data/make_sample_data.py` generates a synthetic sample with the same schema.
  The sample resembles no real plant, forecast or settlement, and is for testing
  the software only — numbers produced from it are not the paper's results;

The synthetic sample is for checking that the scripts run and for illustrating
the input schema. It does not reproduce the paper's empirical results. Reproducing
those results requires the confidential operational record, which cannot be
distributed. No derived record-level data are available for download.

## Environment

* Python ≥ 3.8
* pandas, numpy, matplotlib ≥ 3.3 (`requirements.txt`)
* [`rsvg-convert`](https://gitlab.gnome.org/GNOME/librsvg) (from `librsvg`) to
  convert the hand-drawn SVG figures to PDF/PNG; on macOS `brew install librsvg`

## Reproducing the published record

With the confidential record placed as described in `data/README.md`, the same
`reproduce.sh` reproduces the paper. `code/stats/recompute_two_source.py`
writes `data/v5/two_source_numbers.json` from the input record; `code/pipeline/`
documents how the analysis-ready panels are built from the raw operational exports.

## Citation and license

Please cite the paper when using this code. Code is released under the MIT
License; see `LICENSE`. A repository URL and Zenodo DOI will be added here when
the public release and archive are created.
