# Tangling audit: results

Coder A: 48 bugs, 175 counted fix files; part_of_fix = yes: 164, no: 10, unsure: 1

## Unrelated (tangled) files by class and role

| cls      | secondary   |   files |   unrelated |   share |
|:---------|:------------|--------:|------------:|--------:|
| Mono-fix | False       |      41 |           0 |   0     |
| Poly-fix | False       |      76 |           6 |   0.079 |
| Poly-fix | True        |      58 |           4 |   0.069 |

Bugs with at least one unrelated file: Poly-fix 7 of 30, Mono-fix 0 of 18.
Poly-fix bugs whose secondary files are all unrelated (class would become Mono-fix): 1 of 30.

## Poly-fix minus Mono-fix MAP on the audited bugs, before and after removing unrelated files

(LocAgent uses full AP here, ranks beyond its ten files count as misses.)

| technique      |   map_mono |   map_poly |    gap |   map_poly_clean |   gap_clean |
|:---------------|-----------:|-----------:|-------:|-----------------:|------------:|
| BLAZE (all)    |      0.151 |      0.226 |  0.075 |            0.229 |       0.079 |
| BM25 (all)     |      0.22  |      0.258 |  0.038 |            0.277 |       0.057 |
| FLIM (parse)   |      0.36  |      0.218 | -0.141 |            0.233 |      -0.127 |
| LocAgent (all) |      0.423 |      0.158 | -0.265 |            0.159 |      -0.264 |
| SweRank (all)  |      0.368 |      0.188 | -0.18  |            0.197 |      -0.17  |

