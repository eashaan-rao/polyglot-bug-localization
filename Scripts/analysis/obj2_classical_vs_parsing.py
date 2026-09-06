"""
Step 4 — classical retrieval vs the parsing technique on Poly-fix bugs.

The question that turns a performance observation into a claim about the field:
on Poly-fix bugs, does BM25 hold where the parsing technique (FLIM in the WP arm,
COOBA in the CP arm) cannot build a structural representation?

Reads results/obj2/diagnostics/*.csv. Reports, per project:
  * MRR of BM25 vs the parsing technique, split Mono-fix / Poly-fix
  * the INVERSION test: parsing >= BM25 on Mono-fix  AND  BM25 >= parsing on Poly-fix
  * secondary-file focus: rank of the non-primary ground-truth file specifically
    (YAML / JSON / XML / SQL), BM25 vs parsing
  * BLAZE reported alongside, never merged into an aggregate

Outputs: results/obj2/analysis/classical_vs_parsing.csv, .md
"""

import glob
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from Scripts import paths as P
from Scripts.classification_rules import EXT_LANG, GRAMMAR_LANGUAGES, TIER1_SECONDARY

OUT = os.path.join(P.RESULT_PATH, "analysis")
os.makedirs(OUT, exist_ok=True)
PARSING = {"WP": "FLIM", "CP": "COOBA"}


def load_diag():
    frames = []
    for f in glob.glob(os.path.join(P.RESULT_PATH, "diagnostics", "*.csv")):
        parts = os.path.basename(f)[:-4].split("_")
        d = pd.read_csv(f)
        d["arm"], d["model"] = parts[0], parts[1]
        d["project"] = "_".join(parts[2:])
        frames.append(d)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def bug_mrr(df):
    r = df.groupby("bug_id")["model_rank"].min()
    r = np.where(r.values > 0, r.values, np.inf)
    return float(np.mean(1.0 / r)) if len(r) else 0.0


def main():
    diag = load_diag()
    if diag.empty:
        print("no diagnostics yet — run Scripts/run_obj2_experiments.py first")
        return

    # secondary-language flag per gt-file row
    def is_sec(ext):
        lc = EXT_LANG.get(str(ext), (None, None))
        return lc[0] in GRAMMAR_LANGUAGES and lc[1] != "source"
    diag["is_secondary"] = diag["ext"].map(is_sec)
    diag["is_tier1"] = diag["ext"].map(lambda e: EXT_LANG.get(str(e), (None,))[0] in TIER1_SECONDARY)

    rows = []
    for arm in ("WP", "CP"):
        a = diag[diag.arm == arm]
        if a.empty:
            continue
        parsing = PARSING[arm]
        for proj in sorted(a.project.unique()):
            cell = {"arm": arm, "project": proj}
            for cls in ("Mono-fix", "Poly-fix"):
                for mdl in ("BM25", parsing, "BLAZE"):
                    g = a[(a.model == mdl) & (a.project == proj) & (a.bug_class == cls)]
                    cell[f"{mdl}_{cls}_MRR"] = round(bug_mrr(g), 4) if not g.empty else None
                # secondary-file rank (Poly-fix only, Tier-1 secondary GT files)
                if cls == "Poly-fix":
                    for mdl in ("BM25", parsing, "BLAZE"):
                        g = a[(a.model == mdl) & (a.project == proj)
                              & (a.bug_class == "Poly-fix") & (a.is_tier1)]
                        r = np.where(g.model_rank > 0, g.model_rank, np.inf)
                        cell[f"{mdl}_secondary_file_MRR"] = (
                            round(float(np.mean(1.0 / r)), 4) if len(r) else None)
            # inversion test
            bm_mono = cell.get(f"BM25_Mono-fix_MRR")
            pa_mono = cell.get(f"{parsing}_Mono-fix_MRR")
            bm_poly = cell.get(f"BM25_Poly-fix_MRR")
            pa_poly = cell.get(f"{parsing}_Poly-fix_MRR")
            cell["inversion"] = (
                None if None in (bm_mono, pa_mono, bm_poly, pa_poly)
                else bool(pa_mono >= bm_mono and bm_poly >= pa_poly))
            cell["parsing_technique"] = parsing
            rows.append(cell)

    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(OUT, "classical_vs_parsing.csv"), index=False)

    md = ["# Step 4 — classical retrieval vs parsing technique on Poly-fix", ""]
    md.append(out.to_markdown(index=False))
    md.append("")
    inv = out[out.inversion == True]
    md.append(f"**Inversion** (parsing ≥ BM25 on Mono-fix AND BM25 ≥ parsing on "
              f"Poly-fix): {len(inv)}/{out.inversion.notna().sum()} projects "
              f"{'— ' + ', '.join(inv.project) if len(inv) else ''}.")
    md.append("\nIf no inversion appears, the paper is a performance study and the "
              "venue decision changes (ICPC / IST rather than FSE).")
    with open(os.path.join(OUT, "classical_vs_parsing.md"), "w") as f:
        f.write("\n".join(str(x) for x in md) + "\n")
    print("\n".join(str(x) for x in md))
    print(f"\nWrote {OUT}/classical_vs_parsing.csv, .md")


if __name__ == "__main__":
    main()
