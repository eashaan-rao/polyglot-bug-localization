# Retrieval recall by class (property of the setup)

Bug-level Recall@K — fraction of bugs with ≥1 ground-truth file in the Top-K:

| K | Mono-fix | Poly-fix |
|---|---|---|
| 10 | 0.026 | 0.051 |
| 30 | 0.050 | 0.110 |
| 50 | 0.070 | 0.143 |
| 75 | 0.092 | 0.191 |
| 100 | 0.113 | 0.235 |
| 150 | 0.138 | 0.281 |
| 200 | 0.163 | 0.329 |
| 300 | 0.207 | 0.387 |
| 500 | 0.259 | 0.472 |

**Operating K = 500** (smallest K with Mono bug-recall ≥ 0.95 and Poly bug-recall ≥ 0.85; falls back to 500 if none).

File-level Recall@500 for secondary-language ground-truth files, by extension:

| ext | n files | file-recall@500 |
|---|---|---|
| yml | 861 | 0.106 |
| yaml | 695 | 0.045 |
| json | 214 | 0.304 |
| xml | 137 | 0.234 |
| sql | 45 | 0.067 |
| gradle | 39 | 0.179 |
| j2 | 18 | 0.000 |
| json5 | 11 | 0.000 |
| css | 6 | 0.000 |
| xsd | 5 | 0.000 |
| jinja2 | 4 | 0.000 |
| tpl | 3 | 0.333 |
| kubernetes-helm-yaml | 3 | 0.333 |
| toml | 2 | 0.000 |
| tf | 2 | 1.000 |

endswith-vs-exact ground-truth match collisions: 38/12252 (0.31%)
