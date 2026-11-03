"""
Dataset-wide impact of the rule readings the 50-bug annotators questioned
(results/obj2/annotation/v2/reconciliation.md).

For each candidate amendment, drop the files it would newly exclude and
re-classify every bug with the frozen ruleset; count bugs whose keep decision,
broad-grain Poly-fix label, or primary-language ground truth (= training
positives) would change. Also counts primary-language GT files whose is_test
flag comes only from a `test/` package directory under src/main/.

Uses the fix-commit files only, so the 9 bugs that classify_bugs.py classifies
with the dataset-GT fallback are approximated (totals 3593 / 984 here vs the
3594 kept / 985 broad Poly-fix of the classification).

    python Scripts/annotation_impact.py
"""

import json
import os
import re
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Scripts import paths as P
from Scripts.classification_rules import DEFAULT_TOGGLES, classify_file, classify_fix, keep_bug

PRIMARY = {"java": "Java", "python": "Python"}
AMEND = {   # amendment -> files it would newly exclude
    "any ci/ directory is CI config": re.compile(r"(^|/)ci/"),
    "*-generated.* / *_generated.* is generated": re.compile(r"[-_]generated\.[^/]+$", re.I),
    "everything under docs/ is documentation": re.compile(r"(^|/)docs?/"),
    "checkstyle / forbidden-apis / spotless config is dev tooling":
        re.compile(r"(^|/)(checkstyle|forbidden|spotless)[^/]*\.(xml|txt)$", re.I),
}
OUT = os.path.join(P.RESULT_PATH, "annotation", "v2", "amendment_impact.json")


def state(files, lang):
    if not files:
        return False, False, []
    fc = classify_fix(files, lang)
    k = keep_bug(fc, lang)
    poly = k and fc.label == "Poly-fix" and fc.grains["broad"]
    prim = sorted(v.path for v in fc.per_file if v.counts and v.language == PRIMARY[lang])
    return k, poly, prim


def main():
    raw = pd.read_parquet(P.FIX_FILES_RAW_PARQUET)
    raw = raw[raw["commit_recovered"]]
    res = {a: {"keep_changes": 0, "poly_label_changes": 0, "primary_gt_changes": 0} for a in AMEND}
    n_keep = n_poly = pkg_test = 0
    for _, r in raw.iterrows():
        files = json.loads(r["files_raw"]) if r["files_raw"] else []
        if not files:
            continue
        lang = r["language"]
        k0, p0, pr0 = state(files, lang)
        n_keep += k0
        n_poly += p0
        if k0:
            for f in files:
                v = classify_file(f["path"], f.get("ext", ""), f["change_type"], DEFAULT_TOGGLES)
                if v.counts and v.language == PRIMARY[lang] and "test" in v.flags and "src/main/" in f["path"]:
                    pkg_test += 1
        for a, rx in AMEND.items():
            k1, p1, pr1 = state([f for f in files if not rx.search(f["path"])], lang)
            res[a]["keep_changes"] += k0 != k1
            res[a]["poly_label_changes"] += k0 and p0 != p1
            res[a]["primary_gt_changes"] += k0 and pr0 != pr1
    out = {"kept_bugs": n_keep, "kept_broad_poly": n_poly, "amendments": res,
           "primary_gt_files_test_via_src_main_package_dir": pkg_test}
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
