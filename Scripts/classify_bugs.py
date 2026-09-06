"""
Step 0 (part 3) — apply the frozen rules to every bug and emit the labelled
Mono-fix / Poly-fix classification. This CSV is the study's reusable artifact.

Inputs : data/obj2/fix_files_raw.parquet   (from extract_fix_commits.py)
         Scripts/classification_rules.py    (RULESET_VERSION)
Outputs: data/obj2/bug_classification.parquet
         results/obj2/bug_classification.csv

Run:  python Scripts/classify_bugs.py
"""

import json
import os
import sys
from collections import Counter

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Scripts import paths as P
from Scripts.classification_rules import (
    RULESET_VERSION, classify_fix, keep_bug, GRAMMAR_LANGUAGES,
)

LANG = dict(P.SELECTED_PROJECTS)  # repo_name -> "java"/"python"


def ext_of(path: str) -> str:
    base = path.rsplit("/", 1)[-1]
    if base.startswith(".") and base.count(".") == 1:
        return base.lower()
    return base.rsplit(".", 1)[-1].lower() if "." in base else ""


def main():
    raw = pd.read_parquet(P.FIX_FILES_RAW_PARQUET)
    rows = []
    for _, r in raw.iterrows():
        repo = r["repo_name"]
        lang = LANG[repo]
        files = json.loads(r["files_raw"]) if r["files_raw"] else []
        gt = json.loads(r["gt_files"]) if r["gt_files"] else []

        classified_from = "commit"
        if not r["commit_recovered"] or not files or (r["n_gt_files"] and not r["gt_covered_by_commit"]):
            # fall back: union the fix-commit files with the dataset ground truth,
            # so a bug is never mis-classified because its commit diff was thin.
            classified_from = "commit+gt_fallback" if files else "gt_only"
            seen = {f["path"] for f in files}
            for g in gt:
                if g not in seen:
                    files.append({"path": g, "ext": ext_of(g), "change_type": "M"})

        fc = classify_fix(files, lang)
        keep = keep_bug(fc, lang)

        # C4 — which admitted secondary languages actually have a file in the ground truth
        gt_set = set(gt)
        sec_in_gt = sorted({
            v.language for v in fc.per_file
            if v.counts and v.language in GRAMMAR_LANGUAGES
            and v.language != fc.primary_language
            and any(v.path == g or v.path.endswith("/" + g) for g in gt_set)
        })

        rows.append({
            "repo_name": repo, "language": lang, "bug_id": r["bug_id"],
            "fix_commit_sha": r["fix_commit_sha"],
            "ruleset_version": RULESET_VERSION,
            "classified_from": classified_from,
            "commit_recovered": bool(r["commit_recovered"]),
            "n_parents": r["n_parents"],
            "class": fc.label,
            "keep": keep,
            "primary_language": fc.primary_language,
            "languages": json.dumps(fc.languages),
            "programming_languages": json.dumps(fc.programming_languages),
            "secondary_languages": json.dumps(fc.secondary_languages),
            "secondary_in_ground_truth": json.dumps(sec_in_gt),
            "grain_headline": fc.grains["headline"],
            "grain_broad": fc.grains["broad"],
            "grain_strict": fc.grains["strict"],
            "grain_tier3_only": fc.grains["tier3_only"],
            "n_files_raw": r["n_files_raw"],
            "n_files_counted": fc.n_files_counted,
            "n_gt_files": r["n_gt_files"],
            "gt_covered_by_commit": r["gt_covered_by_commit"],
            "boundary_flags": json.dumps(fc.boundary_flags),
            "tangled_flag": bool(r["n_parents"] and r["n_parents"] > 1),
            "commit_summary": r["commit_summary"],
        })

    df = pd.DataFrame(rows)
    os.makedirs(P.OBJ2_DATA_DIR, exist_ok=True)
    os.makedirs(P.RESULT_PATH, exist_ok=True)
    df.to_parquet(P.BUG_CLASSIFICATION_PARQUET, index=False)
    df.to_csv(P.BUG_CLASSIFICATION_CSV, index=False)

    # ---- report --------------------------------------------------------
    print(f"RULESET_VERSION = {RULESET_VERSION}\n")
    tot = len(df)
    kept = df[df["keep"]]
    print(f"All bugs: {tot}   |   kept (fix touches project primary language): {len(kept)}  "
          f"({100*len(kept)/tot:.1f}%)")
    print(f"classified_from: {dict(df['classified_from'].value_counts())}\n")

    print(f"{'project':26s} {'kept':>5s} {'Mono':>5s} {'Poly':>5s} {'Other':>5s} "
          f"{'head':>5s} {'broad':>6s} {'strict':>6s} {'T3only':>6s}")
    agg = Counter()
    for repo in P.SELECTED_REPO_NAMES:
        g = kept[kept["repo_name"] == repo]
        m = (g["class"] == "Mono-fix").sum()
        p = (g["class"] == "Poly-fix").sum()
        o = (g["class"] == "Other-fix").sum()
        h = g["grain_headline"].sum()
        b = g["grain_broad"].sum()
        s = g["grain_strict"].sum()
        t3 = g["grain_tier3_only"].sum()
        print(f"{repo:26s} {len(g):5d} {m:5d} {p:5d} {o:5d} {h:5d} {b:6d} {s:6d} {t3:6d}")
        for k, v in dict(mono=m, poly=p, other=o, head=h, broad=b, strict=s, t3=t3).items():
            agg[k] += v
    print(f"{'TOTAL':26s} {len(kept):5d} {agg['mono']:5d} {agg['poly']:5d} {agg['other']:5d} "
          f"{agg['head']:5d} {agg['broad']:6d} {agg['strict']:6d} {agg['t3']:6d}")

    mp = agg['mono'] + agg['poly']
    print(f"\nPoly-fix prevalence (kept set): "
          f"headline {100*agg['head']/mp:.1f}%  broad {100*agg['broad']/mp:.1f}%  "
          f"strict {100*agg['strict']/mp:.1f}%   (of {mp} Mono+Poly)")

    print("\nSecondary languages in kept Poly-fix (bug counts):")
    c = Counter()
    for _, r in kept[kept["class"] == "Poly-fix"].iterrows():
        for l in json.loads(r["secondary_languages"]):
            c[l] += 1
    for l, n in c.most_common():
        print(f"  {l:14s} {n}")

    print(f"\nWrote {P.BUG_CLASSIFICATION_PARQUET}")
    print(f"      {P.BUG_CLASSIFICATION_CSV}")


if __name__ == "__main__":
    main()
