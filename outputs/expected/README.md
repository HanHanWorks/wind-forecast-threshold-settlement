# Expected aggregates

`two_source_numbers.json` records every headline number of the published paper
(Tables 1-3, 5, 7, the resolution analysis, the vendor-replicate integrity
check and the generation denominators), recomputed by
`code/stats/recompute_two_source.py` on the confidential record.

All of these values are quoted in the paper itself; the file contains
aggregate statistics only - no row-level data. Numbers produced by running the
code on the synthetic sample will differ, and are not the paper's results.
