#!/usr/bin/env bash
# End-to-end reproduction on the synthetic sample data.
# With the real (confidential) record in data/, the same commands reproduce
# every figure, table and headline number of the paper.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"

"$PY" data/make_sample_data.py "$@"        # add --force to regenerate the sample
"$PY" code/stats/gap_noise.py              # -> data/v5/gap_noise.json
"$PY" code/stats/g6_resolution.py          # -> data/v5/g6_{pairs,resolution}.csv
"$PY" code/stats/var_decomp.py             # -> data/v5/var_decomp.json
"$PY" code/stats/recompute_two_source.py   # -> data/v5/two_source_numbers.json
"$PY" code/figures/make_fig1_nature.py     # Fig 1 + Fig 5
"$PY" code/figures/make_figures_svg.py     # Fig 2, 3, 4, 6
"$PY" code/stats/make_tab_noise.py         # Table 6 (LaTeX)

echo
echo "done."
echo "  figures : outputs/figures/  outputs/figures_svg/"
echo "  tables  : outputs/tables/"
echo "  stats   : data/v5/*.json"
