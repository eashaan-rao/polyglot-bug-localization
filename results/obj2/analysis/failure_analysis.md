# Step 4 — failure mechanism sub-analysis (Poly-fix secondary files)

Failure set (missed by every technique, rank > 10 or absent): **329** (bug, file) pairs; success set: 26.

## File-type composition — failure vs success

| category    |   failure_set |   success_set |   failure_% |   success_% |
|:------------|--------------:|--------------:|------------:|------------:|
| data-config |           316 |            26 |        96   |         100 |
| schema      |             6 |             0 |         1.8 |           0 |
| style       |             1 |             0 |         0.3 |           0 |
| build       |             6 |             0 |         1.8 |           0 |

Chi-squared p (failure vs success composition): 0.785

## Truncation check

Failure-set secondary files whose first changed line sits beyond a 512-token window (~8 tokens/line): **19.5%** of 329 files with a recoverable hunk.

Semantic-link coding (report ↔ secondary file) is left for manual annotation on the failure set.
