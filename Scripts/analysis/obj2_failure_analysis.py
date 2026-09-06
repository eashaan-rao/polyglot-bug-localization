"""
Step 4 mechanism sub-analysis — why do techniques miss on Poly-fix secondary files?

Failure set = (bug, secondary ground-truth file) pairs where every technique that
ran ranks the file outside the top-10 (or not at all). Success set = ranked in
the top-10 by at least one technique.

Reports:
  * file-type composition of the failure set vs the success set, with a
    chi-squared test  (is the failure set disproportionately config/build/schema?)
  * truncation check: for each failure-set secondary file, the line number of the
    first changed line in the fix diff; if the text before it exceeds a
    512-token budget (~8 tokens/line) the bug-relevant change sits beyond a
    512-token model window. Reports the truncation-correlated fraction.
  * (semantic link between report and secondary file is left for manual coding)

Outputs: results/obj2/analysis/failure_analysis.{csv,md}

Run:  python Scripts/analysis/obj2_failure_analysis.py
"""

import glob
import json
import os
import re
import subprocess
import sys
from collections import Counter

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from Scripts import paths as P
from Scripts.classification_rules import EXT_LANG, GRAMMAR_LANGUAGES

OUT = os.path.join(P.RESULT_PATH, "analysis")
os.makedirs(OUT, exist_ok=True)
TOP = 10
TOKENS_PER_LINE = 8
TOKEN_BUDGET = 512
LANG = dict(P.SELECTED_PROJECTS)
_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", re.M)


def load_diag():
    frames = []
    for f in glob.glob(os.path.join(P.RESULT_PATH, "diagnostics", "*.csv")):
        parts = os.path.basename(f)[:-4].split("_")
        d = pd.read_csv(f, dtype={"bug_id": str})
        d["model"] = parts[1]
        d["project"] = "_".join(parts[2:])
        frames.append(d)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def category_of(ext):
    return EXT_LANG.get(str(ext), (None, "other"))[1]


def first_changed_line(repo_dir, sha, path):
    try:
        out = subprocess.run(
            ["git", "-C", repo_dir, "show", "--unified=0", "--format=", sha, "--", path],
            capture_output=True, text=True, timeout=20, errors="replace").stdout
        m = _HUNK.search(out)
        return int(m.group(1)) if m else None
    except Exception:
        return None


def main():
    diag = load_diag()
    if diag.empty:
        print("no diagnostics yet"); return
    cls = pd.read_parquet(P.BUG_CLASSIFICATION_PARQUET).set_index(["repo_name", "bug_id"])

    # keep only Poly-fix secondary-language ground-truth files
    diag = diag[diag.bug_class == "Poly-fix"].copy()
    diag["lang"] = diag.ext.map(lambda e: EXT_LANG.get(str(e), (None,))[0])
    diag["is_secondary"] = diag.lang.isin(GRAMMAR_LANGUAGES) & (
        diag.ext.map(lambda e: EXT_LANG.get(str(e), (None, None))[1]) != "source")
    sec = diag[diag.is_secondary & (diag.gt_path != "")].copy()
    if sec.empty:
        print("no secondary-file diagnostics (need BM25/BLAZE per-path ranks)"); return

    # best rank across techniques per (project, bug, gt_path)
    g = (sec.groupby(["project", "bug_id", "gt_path", "ext"])
            .agg(best_rank=("model_rank", lambda s: min([x for x in s if x and x > 0], default=-1)),
                 n_tech=("model", "nunique"))
            .reset_index())
    g["hit"] = g.best_rank.between(1, TOP)
    g["category"] = g.ext.map(category_of)

    fail = g[~g.hit].copy()
    succ = g[g.hit].copy()

    # ---- composition test ----
    comp = pd.DataFrame({
        "failure_set": Counter(fail.category),
        "success_set": Counter(succ.category),
    }).fillna(0).astype(int)
    comp["failure_%"] = (100 * comp.failure_set / max(comp.failure_set.sum(), 1)).round(1)
    comp["success_%"] = (100 * comp.success_set / max(comp.success_set.sum(), 1)).round(1)
    chi_p = np.nan
    try:
        from scipy.stats import chi2_contingency
        tab = comp[["failure_set", "success_set"]].values
        tab = tab[tab.sum(axis=1) > 0]
        if tab.shape[0] > 1 and tab.sum() > 0:
            chi_p = chi2_contingency(tab)[1]
    except Exception:
        pass
    comp.to_csv(os.path.join(OUT, "failure_composition.csv"))

    # ---- truncation check ----
    proj_dir = {r.replace("/", "_"): os.path.join(P.REPO_BASE_PATH, l, r.replace("/", "_"))
                for r, l in P.SELECTED_PROJECTS}
    proj_repo = {r.replace("/", "_"): r for r, _ in P.SELECTED_PROJECTS}
    tr_rows = []
    for _, r in fail.iterrows():
        rd = proj_dir.get(r["project"])
        if not rd:
            continue
        repo_name = proj_repo[r["project"]]
        try:
            sha = cls.loc[(repo_name, r["bug_id"]), "fix_commit_sha"]
        except KeyError:
            continue
        fcl = first_changed_line(rd, sha, r["gt_path"])
        tr_rows.append({
            "project": r["project"], "bug_id": r["bug_id"], "gt_path": r["gt_path"],
            "ext": r["ext"], "first_changed_line": fcl,
            "tokens_before": (fcl * TOKENS_PER_LINE) if fcl else None,
            "beyond_512": (fcl is not None and fcl * TOKENS_PER_LINE > TOKEN_BUDGET),
        })
    tr = pd.DataFrame(tr_rows)
    tr.to_csv(os.path.join(OUT, "failure_truncation.csv"), index=False)
    trunc_frac = tr["beyond_512"].mean() if len(tr) else float("nan")

    md = ["# Step 4 — failure mechanism sub-analysis (Poly-fix secondary files)", ""]
    md.append(f"Failure set (missed by every technique, rank > {TOP} or absent): "
              f"**{len(fail)}** (bug, file) pairs; success set: {len(succ)}.\n")
    md.append("## File-type composition — failure vs success\n")
    md.append(comp.reset_index().rename(columns={"index": "category"}).to_markdown(index=False))
    md.append(f"\nChi-squared p (failure vs success composition): "
              f"{'%.3g' % chi_p if chi_p == chi_p else 'n/a'}\n")
    md.append("## Truncation check\n")
    md.append(f"Failure-set secondary files whose first changed line sits beyond a "
              f"512-token window (~{TOKENS_PER_LINE} tokens/line): "
              f"**{100*trunc_frac:.1f}%** of {len(tr)} files with a recoverable hunk.\n")
    md.append("Semantic-link coding (report ↔ secondary file) is left for manual "
              "annotation on the failure set.")
    with open(os.path.join(OUT, "failure_analysis.md"), "w") as f:
        f.write("\n".join(str(x) for x in md) + "\n")
    print("\n".join(str(x) for x in md))
    print(f"\nWrote failure_analysis.md, failure_composition.csv, failure_truncation.csv")


if __name__ == "__main__":
    main()
