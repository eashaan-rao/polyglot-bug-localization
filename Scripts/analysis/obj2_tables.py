"""
Paper tables. Reads whatever is on disk and emits Markdown + CSV; techniques
that have not been run yet are simply absent from the technique tables.

Outputs: results/obj2/tables/*.md, *.csv

Run:  python Scripts/analysis/obj2_tables.py
"""

import glob
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from Scripts import paths as P
from Scripts.classification_rules import RULESET_VERSION

OUT = os.path.join(P.RESULT_PATH, "tables")
os.makedirs(OUT, exist_ok=True)


def w(name, df, note=""):
    df.to_csv(os.path.join(OUT, name + ".csv"), index=False)
    with open(os.path.join(OUT, name + ".md"), "w") as f:
        if note:
            f.write(note + "\n\n")
        f.write(df.to_markdown(index=False) + "\n")
    print(f"\n### {name}\n{note}")
    print(df.to_string(index=False))


# ---- Table 1: dataset ---------------------------------------------------
def table_dataset():
    cls = pd.read_parquet(P.BUG_CLASSIFICATION_PARQUET)
    kept = cls[cls["keep"]]
    rows = []
    for repo in P.SELECTED_REPO_NAMES:
        g = kept[kept.repo_name == repo]
        m = int((g["class"] == "Mono-fix").sum())
        p = int((g["class"] == "Poly-fix").sum())
        rows.append({
            "project": repo,
            "language": dict(P.SELECTED_PROJECTS)[repo].capitalize(),
            "kept bugs": len(g), "Mono-fix": m, "Poly-fix": p,
            "Poly% (broad)": round(100 * g["grain_broad"].sum() / (m + p), 1),
            "Poly% (headline)": round(100 * g["grain_headline"].sum() / (m + p), 1),
            "Poly% (strict)": round(100 * g["grain_strict"].sum() / (m + p), 1),
            "min class n": min(m, p),
        })
    tot = kept
    m, p = int((tot["class"] == "Mono-fix").sum()), int((tot["class"] == "Poly-fix").sum())
    rows.append({
        "project": "TOTAL", "language": "", "kept bugs": len(tot), "Mono-fix": m, "Poly-fix": p,
        "Poly% (broad)": round(100 * tot["grain_broad"].sum() / (m + p), 1),
        "Poly% (headline)": round(100 * tot["grain_headline"].sum() / (m + p), 1),
        "Poly% (strict)": round(100 * tot["grain_strict"].sum() / (m + p), 1),
        "min class n": "",
    })
    w("table1_dataset", pd.DataFrame(rows),
      f"**Table 1.** Dataset (BeetleBox, RULESET {RULESET_VERSION}). Kept = fix "
      f"touches the project's AST-parseable primary language.")


# ---- Table 2: feasibility --------------------------------------------
def table_feasibility():
    f = os.path.join(P.RESULT_PATH, "feasibility_matrix.csv")
    if not os.path.exists(f):
        return
    d = pd.read_csv(f)
    piv = (d[d.tier != "T3"]
           .assign(cell=lambda x: x.secondary_language + " (." + x.ext + ", " + x.configured_parser_language + ")")
           [["cell", "n_files", "BM25_outcome", "BLAZE_outcome", "FLIM_outcome", "COOBA_outcome"]])
    w("table2_feasibility", piv,
      "**Table 2.** Architectural feasibility: dominant outcome when each technique "
      "ingests a real file of the given type. `trivial_graph` / `degraded_wholefile` "
      "= the technique produced no structural representation.")


# ---- Table 3: WP performance by class -------------------------------
def table_wp_performance():
    s = os.path.join(P.RESULT_PATH, "wp_cp_summary.csv")
    if not os.path.exists(s):
        return
    d = pd.read_csv(s)
    d = d[(d.arm == "WP") & (d.bug_class.isin(["Mono-fix", "Poly-fix"]))]
    rows = []
    for (model, bclass), g in d.groupby(["model", "bug_class"]):
        rows.append({
            "technique": model, "class": bclass,
            "n bugs": int(g.n_test_bugs.sum()),
            "Top@1": round(g.top1.mean(), 3), "Top@5": round(g.top5.mean(), 3),
            "Top@10": round(g.top10.mean(), 3),
            "MAP": round(g.MAP.mean(), 3), "MRR": round(g.MRR.mean(), 3),
        })
    tbl = pd.DataFrame(rows).sort_values(["technique", "class"])
    w("table3_wp_performance", tbl,
      "**Table 3.** Within-project performance, macro-averaged over the six "
      "projects, by fix class. Full-snapshot ranking (no retrieval stage). "
      "BLAZE is reported on its own row and never averaged with the others.")

    # per-project detail
    det = d[["model", "source_project", "bug_class", "top1", "top10", "MAP", "MRR"]].copy()
    det.columns = ["technique", "project", "class", "Top@1", "Top@10", "MAP", "MRR"]
    w("table3b_wp_per_project", det.round(3))


# ---- Table 4: classical vs parsing on Poly-fix ---------------------
def table_classical_vs_parsing():
    cvp = os.path.join(P.RESULT_PATH, "analysis", "classical_vs_parsing.csv")
    if not os.path.exists(cvp):
        return
    d = pd.read_csv(cvp)
    w("table4_classical_vs_parsing", d,
      "**Table 4.** BM25 vs the parsing technique (FLIM) on Poly-fix bugs, per "
      "project. `inversion` = parsing >= BM25 on Mono-fix AND BM25 >= parsing on "
      "Poly-fix.")


if __name__ == "__main__":
    table_dataset()
    table_feasibility()
    table_wp_performance()
    table_classical_vs_parsing()
    print(f"\nWrote tables to {OUT}")
