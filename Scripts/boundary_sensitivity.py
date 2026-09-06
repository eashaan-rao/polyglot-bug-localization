"""
Step 1 (sensitivity) — how the Poly-fix prevalence figure moves under each
alternative boundary rule. Reported as a range so a reader can see how much the
definition carries.

Re-classifies every bug under each named toggle set, re-applies the
primary-language keep filter, and reports Mono/Poly/Other + Poly-fix % against
the headline.

Output: results/obj2/boundary_sensitivity.csv
"""

import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Scripts import paths as P
from Scripts.classification_rules import (
    RULESET_VERSION, SENSITIVITY_SETS, classify_fix, keep_bug,
)

LANG = dict(P.SELECTED_PROJECTS)


def ext_of(path):
    base = path.rsplit("/", 1)[-1]
    if base.startswith(".") and base.count(".") == 1:
        return base.lower()
    return base.rsplit(".", 1)[-1].lower() if "." in base else ""


def main():
    raw = pd.read_parquet(P.FIX_FILES_RAW_PARQUET)
    # pre-build the (files, gt-fallback) per bug once
    bugs = []
    for _, r in raw.iterrows():
        files = json.loads(r["files_raw"]) if r["files_raw"] else []
        gt = json.loads(r["gt_files"]) if r["gt_files"] else []
        if not r["commit_recovered"] or not files or (r["n_gt_files"] and not r["gt_covered_by_commit"]):
            seen = {f["path"] for f in files}
            files = files + [{"path": g, "ext": ext_of(g), "change_type": "M"}
                             for g in gt if g not in seen]
        bugs.append((LANG[r["repo_name"]], files))

    rows = []
    headline_poly = None
    for name, tg in SENSITIVITY_SETS.items():
        m = p = o = x = dropped = 0
        for lang, files in bugs:
            fc = classify_fix(files, lang, tg)
            if not keep_bug(fc, lang):
                dropped += 1
                continue
            m += fc.label == "Mono-fix"
            p += fc.label == "Poly-fix"
            o += fc.label == "Other-fix"
            x += fc.label == "Excluded"
        poly_pct = round(100 * p / (m + p), 1) if (m + p) else 0.0
        if name == "headline":
            headline_poly = poly_pct
        rows.append({
            "toggle_set": name, "kept": m + p + o + x, "dropped_by_keep": dropped,
            "mono_fix": m, "poly_fix": p, "other_fix": o, "excluded": x,
            "poly_fix_pct": poly_pct,
            "delta_vs_headline_pp": round(poly_pct - headline_poly, 1) if headline_poly is not None else 0.0,
        })
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(P.RESULT_PATH, "boundary_sensitivity.csv"), index=False)
    print(f"RULESET_VERSION = {RULESET_VERSION}\n")
    print(out.to_string(index=False))
    lo = out["poly_fix_pct"].min()
    hi = out["poly_fix_pct"].max()
    print(f"\nHeadline Poly-fix prevalence {headline_poly}%  —  full range [{lo}% – {hi}%]")
    mover = out.reindex(out["delta_vs_headline_pp"].abs().sort_values(ascending=False).index)
    print("\nRules that move the headline most:")
    print(mover[["toggle_set", "poly_fix_pct", "delta_vs_headline_pp"]].head(4).to_string(index=False))
    print(f"\nWrote {os.path.join(P.RESULT_PATH, 'boundary_sensitivity.csv')}")


if __name__ == "__main__":
    main()
