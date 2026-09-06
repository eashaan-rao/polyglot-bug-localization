# 50-bug classification agreement check  (RULESET 0.2.0)

`sample_blank.csv` — 50 bugs. Two annotators each fill, independently,
from `changed_files` and `docs/CLASSIFICATION_RULES.md`, WITHOUT opening
`sample_key.csv`:

- `label__Mono_Poly_Other_Excluded` — one of: Mono-fix | Poly-fix | Other-fix | Excluded
- `secondary_languages` — for Poly-fix only: the non-primary languages, e.g. "YAML; JSON"
- `notes` — any rule that was ambiguous

## Scoring

```python
import pandas as pd
a = pd.read_csv("annotator_A.csv"); b = pd.read_csv("annotator_B.csv")
k = pd.read_csv("sample_key.csv")
from sklearn.metrics import cohen_kappa_score
print("A vs B  kappa:", cohen_kappa_score(a.label__Mono_Poly_Other_Excluded, b.label__Mono_Poly_Other_Excluded))
print("A vs rules   :", cohen_kappa_score(a.label__Mono_Poly_Other_Excluded, k.ruleset_label))
print("B vs rules   :", cohen_kappa_score(b.label__Mono_Poly_Other_Excluded, k.ruleset_label))
```

Target: kappa >= 0.8 A-vs-B. Every disagreement -> amend a rule in
`classification_rules.py`, bump RULESET_VERSION to 0.2.1, rerun
`classify_bugs.py` + `prevalence_report.py` + `boundary_sensitivity.py`.
