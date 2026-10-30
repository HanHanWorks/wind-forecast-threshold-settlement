# Data

## Availability

The real record is **not included** and cannot be shared: it is the operational
record of a provincial dispatch centre (southern China), released to the authors
under a data-sharing agreement. It covers 25 wind farms, January 2023 – August
2025, at 15-minute resolution.

To run the code without it, generate the synthetic sample (same schema, no real
content):

```bash
python data/make_sample_data.py [--force]
```

Files under `data/` and `data/v5/` are git-ignored so the confidential record
can never be committed by accident. **Do not remove these ignore rules.**

## Input files (provided by the data owner)

### `data/daily_acc_panel.csv`

Daily accuracy of every forecasting series, per farm-day. A day enters only if
at least 90 of the 96 quarter-hour points survive.

| column | type | description |
|---|---|---|
| `date` | date | calendar day |
| `farm_id` | str | plant identifier (pseudonymised) |
| `acc_S01_src1` | float | daily accuracy of operational source 1 (%) |
| `acc_S02_src2` | float | daily accuracy of operational source 2, the incumbent (%) |
| `acc_S03_limit` | float | curtailment-corrected variant of source 2 (%) |
| `acc_S04_vendorF` | float | series supplied under a commercial vendor label (%) |
| `acc_S05_vendorG` | float | second vendor product (disjoint plant coverage) (%) |
| `acc_S06_scale` … `acc_S14_med8` | float | declared post-processing variants of source 1 (scaling 0.85/1.15/0.9/1.05, smoothing, floor at 5% of capacity, clipping, blend with previous day, median filter); analyst-generated stress tests, not supplier products (%) |

### `data/v5/farmmonth_v2_ext.csv`

The farm-month ledger — the unit at which the settlement is applied.

| column | type | description |
|---|---|---|
| `ym` | str | month, `YYYY-MM` |
| `farm_id` | str | plant identifier |
| `src1`, `src2`, `vendorF` | float | monthly accuracy = mean of daily values (%) |
| `def_src1`, `def_src2`, `def_vendorF` | float | shortfall `max(0, 60 − accuracy)` (points) |
| `E_src1`, `E_src2`, `E_vendorF` | float | assessed energy `Cap × 0.2 × max(0, 60 − accuracy)` (MWh) |
| `Cap_MW`, `Cap_stat_global`, `Cap` | float | installed capacity of the month (MW); `Cap` is the value used |
| `days` | int | number of usable daily observations in the month |
| `cap_src` | str | provenance of the capacity value (monthly snapshot / static fallback) |
| `best` | float | best accuracy among the candidates (%) |
| `n_pass` | int | number of series above the 60% threshold that month |

### `data/v5/farmmonth_se.csv`

Standard errors of each farm-month's statistics, from its own daily series,
deconvolved for first-order autocorrelation.

| column | type | description |
|---|---|---|
| `farm_id`, `ym` | str | plant, month |
| `n_days` | int | daily observations used |
| `gap` | float | mean daily difference incumbent − source 1 (points) |
| `acc` | float | incumbent monthly accuracy (%) |
| `se_gap`, `se_acc` | float | standard errors of the two quantities |

### `data/v5/realmonth_stats.csv`

Monthly output statistics of each plant (used for fleet-generation denominators
and the weather proxies).

| column | type | description |
|---|---|---|
| `farm_id`, `ym` | str | plant, month |
| `pm_mean`, `pm_sd`, `pm_p95`, `pm_ramp`, `pm_calm` | float | mean power and variability descriptors (MW) |
| `n_pts` | int | quarter-hour points in the month |
| `Cap_MW`, `Cap0`, `Capr` | float | installed capacity snapshots (MW) |
| `cf`, `cf_sd`, `cf_p95`, `ramp`, `calm` | float | capacity-factor descriptors (–) |

## Derived files (written by the code into `data/v5/`)

| file | written by | contents |
|---|---|---|
| `gap_noise.json` | `code/stats/gap_noise.py` | noise decomposition of farm-month statistics (Table 6) |
| `var_decomp.json` | `code/stats/var_decomp.py` | variance decomposition used in §5.2 |
| `g6_pairs.csv`, `g6_resolution.csv`, `g6_summary.json` | `code/stats/g6_resolution.py` | pairwise resolution curves (Fig. 5 analysis) |
| `mechanism_panel.csv` | `code/pipeline/` | farm-month ledger plus weather-proxy variables (Fig. 6) |
| `mechanism_reg2.json` | `code/stats/mechanism_reg2.py` | regression summary of the mechanism tests (§5.2) |
| `two_source_numbers.json` | `code/stats/recompute_two_source.py` | **every headline number of the paper** |
