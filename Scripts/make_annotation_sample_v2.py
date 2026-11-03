"""
50-bug two-person agreement check, version 2 (2026-11-03).

Version 1 (make_annotation_sample.py) sampled kept bugs only and asked for a
bug-level label. Version 2 also tests the decisions that feed TRAINING -- the
keep filter and the per-file rules on Java/Python files -- because an error
there would force re-running the experiments, while an error on a secondary
file only changes labels and evaluation.

Sample: 50 bugs from ALL 4 995, stratified by classification outcome
(kept Mono-fix with / without boundary flags, Poly behaviour-bearing,
Poly test-asset-only, Poly tier-3, no-primary single-language, Other-fix,
no-primary Poly, Excluded), spread over the six projects; fixed seed.

Outputs (results/obj2/annotation/v2/):
  bugs_blank.csv    one row per bug  -> annotator fills the bug-level columns
  files_blank.csv   one row per changed file -> annotator fills the file-level columns
  key_bugs.csv      the frozen ruleset's answers (do NOT give to annotators)
  key_files.csv
The protocol is docs/ANNOTATION_PROTOCOL.md.

    python Scripts/make_annotation_sample_v2.py
"""

import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Scripts import paths as P
from Scripts.classification_rules import RULESET_VERSION, DEFAULT_TOGGLES, classify_file, classify_fix, keep_bug

OUT = os.path.join(P.RESULT_PATH, "annotation", "v2")
SEED = 20261103
PRIMARY = {"java": "Java", "python": "Python"}
QUOTA = {   # stratum -> number of bugs (sums to 50)
    "kept Mono-fix, boundary flag": 7,
    "kept Mono-fix, no flag": 5,
    "kept Poly behaviour-bearing": 10,
    "kept Poly test-asset-only": 8,
    "kept Poly tier-3": 4,
    "no-primary single-language": 5,
    "Other-fix": 5,
    "no-primary Poly-fix": 2,
    "Excluded": 4,
}


def stratum(fc, lang, files):
    if fc.label == "Excluded":
        return "Excluded"
    kept = keep_bug(fc, lang)
    if not kept:
        return {"Mono-fix": "no-primary single-language", "Other-fix": "Other-fix",
                "Poly-fix": "no-primary Poly-fix"}[fc.label]
    if fc.label == "Mono-fix":
        return "kept Mono-fix, boundary flag" if fc.boundary_flags else "kept Mono-fix, no flag"
    if not fc.grains["broad"]:
        return "kept Poly tier-3"
    sec = [v for v in fc.per_file if v.counts and v.language and v.language != PRIMARY[lang]]
    return ("kept Poly behaviour-bearing" if any(not ({"test", "test_asset"} & set(v.flags)) for v in sec)
            else "kept Poly test-asset-only")


def main():
    raw = pd.read_parquet(P.FIX_FILES_RAW_PARQUET)
    raw = raw[raw["commit_recovered"]].copy()
    rows = []
    for _, r in raw.iterrows():
        files = json.loads(r["files_raw"]) if r["files_raw"] else []
        if not files or len(files) > 15:          # keep the sheet workable for a human
            continue
        fc = classify_fix(files, r["language"])
        rows.append({"repo_name": r["repo_name"], "bug_id": str(r["bug_id"]), "language": r["language"],
                     "stratum": stratum(fc, r["language"], files), "files": files, "fc": fc,
                     "summary": r["commit_summary"], "sha": r["fix_commit_sha"]})
    df = pd.DataFrame(rows)
    picks = []
    for st, n in QUOTA.items():
        g = df[df["stratum"] == st]
        # spread over projects: round-robin over a shuffled per-project order
        g = g.sample(frac=1.0, random_state=SEED)
        g = g.assign(_k=g.groupby("repo_name").cumcount()).sort_values(["_k", "repo_name"])
        picks.append(g.head(n))
    picks = pd.concat(picks).sample(frac=1.0, random_state=SEED).reset_index(drop=True)

    bugs_blank, files_blank, key_bugs, key_files = [], [], [], []
    for _, r in picks.iterrows():
        fc, lang = r["fc"], r["language"]
        bugs_blank.append({
            "annotator": "", "repo_name": r["repo_name"], "bug_id": r["bug_id"],
            "primary_language": PRIMARY[lang], "commit_summary": r["summary"], "fix_commit_sha": r["sha"],
            "n_files": len(r["files"]),
            "label": "", "keep": "", "secondary_languages": "", "poly_subtype": "", "notes": "",
        })
        sec = [v for v in fc.per_file if v.counts and v.language and v.language != PRIMARY[lang]]
        key_bugs.append({
            "repo_name": r["repo_name"], "bug_id": r["bug_id"], "stratum": r["stratum"],
            "label": fc.label, "keep": "yes" if keep_bug(fc, lang) else "no",
            "secondary_languages": "; ".join(sorted({v.language for v in sec})) if fc.label == "Poly-fix" else "",
            "grain_broad": fc.grains["broad"],
            "poly_subtype": ("" if fc.label != "Poly-fix" or not keep_bug(fc, lang) or not fc.grains["broad"]
                             else "behaviour-bearing" if any(not ({"test", "test_asset"} & set(v.flags)) for v in sec)
                             else "test-asset-only"),
        })
        for f in r["files"]:
            v = classify_file(f["path"], f.get("ext", ""), f["change_type"], DEFAULT_TOGGLES)
            files_blank.append({
                "annotator": "", "repo_name": r["repo_name"], "bug_id": r["bug_id"],
                "path": f["path"], "change_type": f["change_type"],
                "counts": "", "excluded_reason": "", "language": "", "category": "", "is_test": "", "notes": "",
            })
            excl = v.category.split(":", 1)[1] if v.category.startswith("excluded:") else ""
            key_files.append({
                "repo_name": r["repo_name"], "bug_id": r["bug_id"], "path": f["path"],
                "change_type": f["change_type"],
                "counts": "yes" if (v.counts and v.language) else "no", "excluded_reason": excl,
                "language": v.language or "", "category": "" if excl else v.category,
                "is_test": "yes" if {"test", "test_asset"} & set(v.flags) else "no",
                "primary_language_file": "yes" if (v.language == PRIMARY[lang]) else "no",
            })
    os.makedirs(OUT, exist_ok=True)
    pd.DataFrame(bugs_blank).to_csv(os.path.join(OUT, "bugs_blank.csv"), index=False)
    pd.DataFrame(files_blank).to_csv(os.path.join(OUT, "files_blank.csv"), index=False)
    pd.DataFrame(key_bugs).to_csv(os.path.join(OUT, "key_bugs.csv"), index=False)
    pd.DataFrame(key_files).to_csv(os.path.join(OUT, "key_files.csv"), index=False)
    kb = pd.DataFrame(key_bugs)
    print(f"RULESET {RULESET_VERSION}: {len(kb)} bugs, {len(files_blank)} files -> {OUT}")
    print(kb["stratum"].value_counts().to_string())
    print(kb["repo_name"].value_counts().to_string())


if __name__ == "__main__":
    main()
