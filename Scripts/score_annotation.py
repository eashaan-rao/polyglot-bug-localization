"""
Score the 50-bug classification agreement check (docs/ANNOTATION_PROTOCOL.md §4).

Inputs  results/obj2/annotation/v2/{bugs,files}_annotator_<X>.csv for two
        annotators, and key_{bugs,files}.csv (the frozen ruleset's answers).
Outputs results/obj2/annotation/v2/agreement_report.md, disagreements.csv

Every disagreement (A vs B, and each annotator vs the ruleset) gets an impact:
  training    a Java/Python file's counts / excluded_reason, or a bug's keep
              -> a rule change would alter training data (re-run)
  evaluation  everything else, including is_test (it feeds only the S1
              no-tests view and the Poly sub-type, never training)

    python Scripts/score_annotation.py [--a A --b B] [--dir results/obj2/annotation/human]
"""

import argparse
import os
import sys

import pandas as pd
from sklearn.metrics import cohen_kappa_score

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Scripts import paths as P

D = os.path.join(P.RESULT_PATH, "annotation", "v2")
BUG_FIELDS = ["label", "keep", "secondary_languages", "poly_subtype"]
FILE_FIELDS = ["counts", "excluded_reason", "language", "category", "is_test"]


def norm(x):
    x = "" if pd.isna(x) else str(x).strip()
    if ";" in x:
        x = "; ".join(sorted(t.strip() for t in x.split(";") if t.strip()))
    return x.lower()


def load(kind, who):
    fp = os.path.join(D, f"{kind}_annotator_{who}.csv") if who != "key" else os.path.join(D, f"key_{kind}.csv")
    df = pd.read_csv(fp, dtype=str, keep_default_na=False)
    keys = ["repo_name", "bug_id"] + (["path"] if kind == "files" else [])
    fields = BUG_FIELDS if kind == "bugs" else FILE_FIELDS
    for f in fields:
        df[f] = df[f].map(norm) if f in df else ""
    return df.set_index(keys)


def kappa(x, y):
    try:
        return round(cohen_kappa_score(x, y), 3) if len(set(x) | set(y)) > 1 else 1.0
    except Exception:
        return float("nan")


def compare(kind, left, right, ln, rn, key_files):
    fields = BUG_FIELDS if kind == "bugs" else FILE_FIELDS
    j = left[fields].join(right[fields], lsuffix="_l", rsuffix="_r", how="inner")
    stats, rows = {}, []
    for f in fields:
        a, b = j[f + "_l"], j[f + "_r"]
        stats[f] = {"agree_pct": round(100 * (a == b).mean(), 1), "kappa": kappa(list(a), list(b))}
        for idx in j.index[a != b]:
            if kind == "files":
                prim = key_files.loc[idx, "primary_language_file"] == "yes"
                impact = "training" if (prim and f in ("counts", "excluded_reason")) else "evaluation"
            else:
                impact = "training" if f == "keep" else "evaluation"
            rows.append({"pair": f"{ln} vs {rn}", "level": kind, "repo_name": idx[0], "bug_id": idx[1],
                         "path": idx[2] if kind == "files" else "", "field": f,
                         ln: j.at[idx, f + "_l"], rn: j.at[idx, f + "_r"], "impact": impact})
    return stats, rows


def main():
    global D
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", default="A")
    ap.add_argument("--b", default="B")
    ap.add_argument("--dir", default=D, help="folder with the annotator CSVs and key_*.csv (default: the AI round, v2)")
    a = ap.parse_args()
    D = a.dir
    kf = pd.read_csv(os.path.join(D, "key_files.csv"), dtype=str, keep_default_na=False) \
        .set_index(["repo_name", "bug_id", "path"])
    L = ["# 50-bug agreement check — results", ""]
    allrows = []
    for x, y in ((a.a, a.b), (a.a, "key"), (a.b, "key")):
        L += [f"## {x} vs {'ruleset' if y == 'key' else y}", ""]
        for kind in ("bugs", "files"):
            st, rows = compare(kind, load(kind, x), load(kind, y), x, "ruleset" if y == "key" else y, kf)
            allrows += rows
            L += [f"**{kind}** — " + "; ".join(f"{f}: {v['agree_pct']} % (κ {v['kappa']})" for f, v in st.items()), ""]
    dis = pd.DataFrame(allrows)
    dis.to_csv(os.path.join(D, "disagreements.csv"), index=False)
    if not dis.empty:
        L += ["## Disagreements by impact", "",
              dis.groupby(["pair", "impact"]).size().rename("n").reset_index().to_markdown(index=False), "",
              "## Training-impact disagreements (the ones that matter for re-runs)", ""]
        t = dis[dis.impact == "training"]
        L += [t.to_markdown(index=False) if not t.empty else "None.", ""]
    with open(os.path.join(D, "agreement_report.md"), "w") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L[:40]))


if __name__ == "__main__":
    main()
