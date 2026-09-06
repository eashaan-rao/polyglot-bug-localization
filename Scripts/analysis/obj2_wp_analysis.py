"""
Step 3 analysis — within-project Mono-fix vs Poly-fix.

Reads:
  results/obj2/wp_cp_summary.csv          (per arm/model/project/class metrics)
  results/obj2/diagnostics/*.csv          (per bug-file ranks, carry bug_class)

Produces, per technique (BLAZE reported in its own column, never pooled with FLIM):
  * per-project paired (Mono MRR, Poly MRR); Wilcoxon signed-rank across projects;
    Cliff's delta of the per-project Poly-minus-Mono deltas
  * balanced-subsampling estimate: larger test class sub-sampled to the smaller,
    N_SEEDS times, MRR mean with a 95% bootstrap CI, for Mono, Poly and the gap
  * per-extension MRR on secondary-language ground-truth files, with the FAISS
    rank alongside (did the reranker move them?)

Outputs: results/obj2/analysis/wp_*.csv, wp_analysis.md
"""

import glob
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from Scripts import paths as P

OUT = os.path.join(P.RESULT_PATH, "analysis")
os.makedirs(OUT, exist_ok=True)
N_SEEDS = 200
RNG = np.random.default_rng(42)


def mrr(ranks):
    ranks = np.asarray([r for r in ranks if r is not None], dtype=float)
    ranks = np.where(ranks > 0, ranks, np.inf)
    return float(np.mean(1.0 / ranks)) if len(ranks) else 0.0


def cliffs_delta(a, b):
    a, b = np.asarray(a), np.asarray(b)
    if not len(a) or not len(b):
        return 0.0
    gt = sum((x > b).sum() for x in a)
    lt = sum((x < b).sum() for x in a)
    return (gt - lt) / (len(a) * len(b))


def load_diag():
    frames = []
    for f in glob.glob(os.path.join(P.RESULT_PATH, "diagnostics", "*.csv")):
        name = os.path.basename(f)[:-4]
        parts = name.split("_")
        arm, model = parts[0], parts[1]
        d = pd.read_csv(f)
        d["arm"], d["model"], d["run"] = arm, model, name
        frames.append(d)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def bug_first_rank(df):
    """min model_rank per bug, as a positive value or inf."""
    r = df.groupby("bug_id")["model_rank"].min()
    return np.where(r.values > 0, r.values, np.inf)


def main():
    diag = load_diag()
    if diag.empty:
        print("no diagnostics yet — run Scripts/run_obj2_experiments.py first")
        return
    wp = diag[diag.arm == "WP"].copy()

    # ---- per-project paired Mono vs Poly, per model ----------------
    rows = []
    for model in sorted(wp.model.unique()):
        m = wp[wp.model == model]
        per_proj = []
        for run, g in m.groupby("run"):
            proj = run.split(f"{model}_", 1)[1]
            mono = g[g.bug_class == "Mono-fix"]
            poly = g[g.bug_class == "Poly-fix"]
            rr_mono = 1.0 / bug_first_rank(mono)
            rr_poly = 1.0 / bug_first_rank(poly)
            per_proj.append({
                "project": proj, "n_mono": mono.bug_id.nunique(), "n_poly": poly.bug_id.nunique(),
                "mrr_mono": round(float(rr_mono.mean()), 4),
                "mrr_poly": round(float(rr_poly.mean()), 4),
                "delta_poly_minus_mono": round(float(rr_poly.mean() - rr_mono.mean()), 4),
            })
        pp = pd.DataFrame(per_proj)
        rows.append(pp.assign(model=model))
        # Wilcoxon across projects
        try:
            from scipy.stats import wilcoxon
            stat, pval = wilcoxon(pp.mrr_mono, pp.mrr_poly)
        except Exception:
            pval = np.nan
        cd = cliffs_delta(pp.mrr_poly, pp.mrr_mono)
        print(f"[{model}] per-project MRR  Mono {pp.mrr_mono.mean():.3f}  Poly {pp.mrr_poly.mean():.3f}  "
              f"Wilcoxon p={pval:.3g}  Cliff's δ(Poly,Mono)={cd:+.2f}")
    per_proj_df = pd.concat(rows, ignore_index=True)
    per_proj_df.to_csv(os.path.join(OUT, "wp_per_project_paired.csv"), index=False)

    # ---- balanced subsampling per project x model -----------------
    bs = []
    for (model, run), g in wp.groupby(["model", "run"]):
        proj = run.split(f"{model}_", 1)[1]
        mono_ids = g[g.bug_class == "Mono-fix"].bug_id.unique()
        poly_ids = g[g.bug_class == "Poly-fix"].bug_id.unique()
        n = min(len(mono_ids), len(poly_ids))
        if n < 10:
            continue
        rr = g.assign(rr=1.0 / np.where(g.model_rank > 0, g.model_rank, np.inf))
        first = rr.groupby("bug_id").rr.max()
        dm, dp, dg = [], [], []
        for _ in range(N_SEEDS):
            ms = RNG.choice(mono_ids, n, replace=False)
            ps = RNG.choice(poly_ids, n, replace=False)
            a, b = first.loc[ms].mean(), first.loc[ps].mean()
            dm.append(a); dp.append(b); dg.append(b - a)
        bs.append({
            "model": model, "project": proj, "n_per_class": n,
            "mrr_mono_mean": round(np.mean(dm), 4),
            "mrr_mono_ci": [round(np.percentile(dm, 2.5), 4), round(np.percentile(dm, 97.5), 4)],
            "mrr_poly_mean": round(np.mean(dp), 4),
            "mrr_poly_ci": [round(np.percentile(dp, 2.5), 4), round(np.percentile(dp, 97.5), 4)],
            "gap_mean": round(np.mean(dg), 4),
            "gap_ci": [round(np.percentile(dg, 2.5), 4), round(np.percentile(dg, 97.5), 4)],
        })
    pd.DataFrame(bs).to_json(os.path.join(OUT, "wp_balanced_subsampling.json"), orient="records", indent=2)

    # ---- per-extension MRR on secondary GT files -----------------
    wp2 = wp.copy()
    wp2["is_hit_model"] = wp2.model_rank.between(1, 500)
    wp2["rr_model"] = 1.0 / np.where(wp2.model_rank > 0, wp2.model_rank, np.inf)
    wp2["rr_faiss"] = 1.0 / np.where(wp2.faiss_rank > 0, wp2.faiss_rank, np.inf)
    ext = (wp2.groupby(["model", "ext"])
              .agg(n_gt_files=("rr_model", "size"),
                   mrr_model=("rr_model", "mean"),
                   mrr_faiss=("rr_faiss", "mean"))
              .reset_index())
    ext["reranker_moved"] = (ext.mrr_model - ext.mrr_faiss).round(4)
    ext = ext[ext.n_gt_files >= 5].sort_values(["model", "n_gt_files"], ascending=[True, False])
    ext.round(4).to_csv(os.path.join(OUT, "wp_per_extension_mrr.csv"), index=False)

    md = ["# Step 3 — within-project Mono vs Poly", ""]
    md.append("## Per-project paired MRR (BLAZE and FLIM in separate columns)\n")
    md.append(per_proj_df.to_markdown(index=False))
    md.append("\n## Per-extension MRR on ground-truth files (model vs the FAISS baseline)\n")
    md.append(ext.round(4).to_markdown(index=False))
    with open(os.path.join(OUT, "wp_analysis.md"), "w") as f:
        f.write("\n".join(str(x) for x in md) + "\n")
    print(f"\nWrote {OUT}/wp_*.csv, wp_analysis.md")


if __name__ == "__main__":
    main()
