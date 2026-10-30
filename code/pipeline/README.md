# Pipeline: raw operational record → analysis panels

These two scripts run **where the raw operational exports live** (they are not
redistributable). All paths are environment-driven:

| variable | meaning |
|---|---|
| `P2_RAW` | root of the raw operational exports (15-minute forecasts, actual and available power, capacity snapshots) |
| `P2_OUT` | output root; defaults to `data/v5` of this repository |
| `P2_CAPTBL` | monthly installed-capacity table; defaults to `$P2_RAW/monthly_capacity.csv` |

| script | role |
|---|---|
| `p2_v5_pipeline.py` | computes the official accuracy definition (Art. 23(5) of the Southern Region rules), the assessed-energy ledger, the capacity handling and the summary statistics for the full record |
| `p2_extend.py` | re-computes the final months from a later export and merges them into the panel (overlap resolved in favour of the newer export) |

The exact directory names expected under `P2_RAW` are those of the dispatch
centre's export convention (see the constants at the top of each script); adjust
them if your export layout differs.

`code/stats/mechanism_reg2.py` additionally reads raw series to build the
weather-proxy regressions and expects `$P2_RAW/second`, `$P2_RAW/farm_static.csv`
and `$P2_RAW/monthly_capacity.csv`.
