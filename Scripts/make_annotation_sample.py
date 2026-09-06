"""
Two-person classification agreement check (SANER: rules must be applied
consistently). Samples 50 bugs stratified across the six projects and the
classes/grains the rules produce, and writes a blank annotation sheet plus a
"key" (the ruleset's own label, hidden from annotators until reconciliation).

Each annotator independently fills `label` and `secondary_languages` from the
`changed_files` column using docs/CLASSIFICATION_RULES.md, WITHOUT looking at the
key. Disagreements are resolved by amending a rule, not adjudicating the case.

Outputs (results/obj2/annotation/):
  sample_blank.csv     give this to each annotator (no ruleset label)
  sample_key.csv        the ruleset's label + grains, for reconciliation
  README.md            instructions + how to score Cohen's kappa

Run:  python Scripts/make_annotation_sample.py
"""

import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Scripts import paths as P

N = 50
SEED = 20260906
OUT = os.path.join(P.RESULT_PATH, "annotation")
os.makedirs(OUT, exist_ok=True)


def main():
    cls = pd.read_parquet(P.BUG_CLASSIFICATION_PARQUET)
    raw = pd.read_parquet(P.FIX_FILES_RAW_PARQUET)
    raw = raw.set_index(["repo_name", "bug_id"])

    kept = cls[cls["keep"]].copy()
    # strata: project x class x (has a boundary flag or not) -> spread the 50
    kept["has_flag"] = kept["boundary_flags"].apply(lambda s: len(json.loads(s)) > 0)
    kept["stratum"] = kept["repo_name"] + " | " + kept["class"] + " | flags=" + kept["has_flag"].astype(str)

    rng = pd.Series(range(len(kept)))
    per = max(1, N // kept["stratum"].nunique())
    picks = (kept.groupby("stratum", group_keys=False)
                 .apply(lambda g: g.sample(min(len(g), per), random_state=SEED)))
    if len(picks) < N:
        extra = kept.drop(picks.index).sample(N - len(picks), random_state=SEED)
        picks = pd.concat([picks, extra])
    picks = picks.sample(min(N, len(picks)), random_state=SEED).reset_index(drop=True)

    rows_blank, rows_key = [], []
    for _, r in picks.iterrows():
        rr = raw.loc[(r["repo_name"], r["bug_id"])]
        files = json.loads(rr["files_raw"]) if rr["files_raw"] else []
        changed = "; ".join(f"{f['path']} [{f['change_type']}]" for f in files)
        rows_blank.append({
            "annotator": "", "repo_name": r["repo_name"], "bug_id": r["bug_id"],
            "fix_commit_sha": r["fix_commit_sha"],
            "commit_summary": r["commit_summary"],
            "changed_files": changed,
            "label__Mono_Poly_Other_Excluded": "",
            "secondary_languages": "",
            "notes": "",
        })
        rows_key.append({
            "repo_name": r["repo_name"], "bug_id": r["bug_id"],
            "ruleset_label": r["class"],
            "ruleset_secondary_languages": r["secondary_languages"],
            "grain_headline": r["grain_headline"], "grain_broad": r["grain_broad"],
            "grain_strict": r["grain_strict"],
            "boundary_flags": r["boundary_flags"],
        })

    pd.DataFrame(rows_blank).to_csv(os.path.join(OUT, "sample_blank.csv"), index=False)
    pd.DataFrame(rows_key).to_csv(os.path.join(OUT, "sample_key.csv"), index=False)

    readme = f"""# 50-bug classification agreement check  (RULESET 0.2.0)

`sample_blank.csv` — {len(rows_blank)} bugs. Two annotators each fill, independently,
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
"""
    with open(os.path.join(OUT, "README.md"), "w") as f:
        f.write(readme)
    print(f"Wrote {len(rows_blank)} bugs to {OUT}/sample_blank.csv (+ key, README)")
    print(picks.groupby(["repo_name", "class"]).size().to_string())


if __name__ == "__main__":
    main()
