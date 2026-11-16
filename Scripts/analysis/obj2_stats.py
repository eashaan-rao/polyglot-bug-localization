"""
Statistics for RQ3 and RQ4 (docs/JOURNAL_PLAN.md, paper Section 3.7).

Input : results/obj2/eval/per_bug.parquet   (Scripts/evaluate.py)
        OBJ2_SMOKE=1 -> results/obj2/eval_smoke/
Output: results/obj2/stats/  (CSV per table + stats_report.md)

Unit of analysis = one test bug. Metrics of the seeded techniques are first
averaged over seeds per bug (seed spread is reported separately). Folds have
disjoint test bugs and are pooled with fold as a fixed effect.

Primary condition: universe R, ground truth = all counted fix files, bugs from
the kept dataset. Every estimate is recomputed under the sensitivity
conditions S1-S6 (same definitions as the paper):
  S1 gt_filter = no_tests      S2 Poly-fix at the headline / strict grain
  S3 universe T                S4 tangled (merge) fix commits removed
  S5 each fold separately      S6 removed bugs only / kept + removed
  P_behavioural / P_test_only  Poly-fix restricted to bugs whose secondary
                               files include a non-test file / are all test assets

RQ3  Mono-fix vs Poly-fix, per technique x view
  per project : Mann-Whitney U, Cliff's delta with bootstrap 95 % CI
  pooled      : linear mixed model  y ~ class + n_gt + log(n_cand) + log1p(report_len)
                + fold + (1 | project) (fallback: project fixed effects, HC3);
                logistic model on Top-10 with project fixed effects
  decomposition: RR / AP on primary- vs secondary-language GT files,
                reach@parse, random-ranking baseline
RQ4  BM25 vs the parser-dependent techniques, paired on the same bugs
  per class x project: Wilcoxon signed-rank, Cliff's delta, Holm across projects
  inversion  : per-bug difference d = y(BM25) - y(other); mixed model
               d ~ class + covariates + fold + (1 | project). The class
               coefficient equals the technique x class interaction of the
               long-format model; the inversion pattern is d >= 0 on Poly-fix
               together with d < 0 on Mono-fix.
  LocAgent   : Top-10 and RR@10 only (it returns at most ten files)
BLAZE is analysed in its own rows and never pooled with the other techniques.

    python Scripts/analysis/obj2_stats.py
"""

import os
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, wilcoxon

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from Scripts import paths as P

warnings.filterwarnings("ignore")
SMOKE = os.environ.get("OBJ2_SMOKE") == "1"
SFX = "_smoke" if SMOKE else ""
EVAL = os.environ.get("OBJ2_STATS_INPUT") or os.path.join(P.RESULT_PATH, "eval" + SFX, "per_bug.parquet")
OUT = os.environ.get("OBJ2_STATS_OUT") or os.path.join(P.RESULT_PATH, "stats" + SFX)
MONO, POLY = "Mono-fix", "Poly-fix"
# Primary outcome (decided 2026-10-30, G1): AP per bug -> MAP. Secondary:
# complete-fix recall@10, RR, Top-10. LocAgent returns <= 10 files, so any
# comparison that includes it uses AP@10 as the primary outcome for all techniques.
PRIMARY = "ap"
OUTCOMES = ["ap", "cfr10", "rr", "top10"]
TOPK_OUTCOMES = ["ap10", "cfr10", "top10", "rr10"]
N_BOOT = 2000
MIN_CLASS_N_TEST = 5        # per-project tests need >= 5 bugs per class
MIN_CLASS_N_MODEL = 10      # pooled models need >= 10 bugs per class
RNG = np.random.default_rng(20261030)
METRIC_COLS = ["rr", "ap", "ap10", "top1", "top5", "top10", "cfr10", "rr10", "rr_primary", "ap_primary",
               "cfr10_primary", "rr_secondary", "ap_secondary", "cfr10_secondary",
               "rand_rr", "rand_top10", "first_rank"]
KEYS = ["tech", "view", "universe", "gt_filter", "fold", "project", "bug_id"]

# RQ4 pairs: (label, technique A, view A, technique B, view B, outcomes)
PAIRS = [
    ("BM25 vs FLIM-strict", "BM25", "all", "FLIM", "parse", OUTCOMES),
    ("BM25 vs FLIM-fallback", "BM25", "all", "FLIM", "all", OUTCOMES),
    ("BM25-parse vs FLIM-strict (control)", "BM25", "parse", "FLIM", "parse", OUTCOMES),
    ("BM25 vs LocAgent", "BM25", "all", "LocAgent", "all", TOPK_OUTCOMES),
    # SweRank (added 2026-11-08): full ranking of the files it can see (non-test
    # .py files with a function); every other file unscored, i.e. tied last.
    # Python projects only -- the pairing on (fold, project, bug) restricts BM25
    # to the same bugs. AP@10 version for a like-for-like line next to LocAgent.
    ("BM25 vs SweRank", "BM25", "all", "SweRank", "all", OUTCOMES),
    ("BM25 vs SweRank (top-10)", "BM25", "all", "SweRank", "all", TOPK_OUTCOMES),
    ("SweRankEmbed vs SweRank (reranker effect)", "SweRankEmbed", "all", "SweRank", "all", OUTCOMES),
    # ablation (fold 1, seed 13): does training BLAZE on all fix files help?
    ("BLAZE_ALL vs BLAZE (ablation)", "BLAZE_ALL", "all", "BLAZE", "all", OUTCOMES),
]


# ---------------------------------------------------------------------------
def cliffs_delta(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) == 0 or len(b) == 0:
        return np.nan
    gt = (a[:, None] > b[None, :]).sum()
    lt = (a[:, None] < b[None, :]).sum()
    return float((gt - lt) / (len(a) * len(b)))


def boot_ci(fn, *samples, n=N_BOOT):
    vals = []
    for _ in range(n):
        vals.append(fn(*[s[RNG.integers(0, len(s), len(s))] for s in samples]))
    vals = np.array([v for v in vals if np.isfinite(v)])
    return (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))) if len(vals) else (np.nan, np.nan)


def holm(p):
    p = np.asarray(p, float)
    out = np.full_like(p, np.nan)
    ok = np.where(np.isfinite(p))[0]
    if len(ok) == 0:
        return out
    order = ok[np.argsort(p[ok])]
    m, run = len(order), 0.0
    for i, j in enumerate(order):
        run = max(run, (m - i) * p[j])
        out[j] = min(1.0, run)
    return out


def _fit_mixed(formula, data, group="project"):
    """Linear mixed model with a random intercept per project. If it cannot be
    fitted (e.g. zero between-project variance -> singular), fall back to OLS
    with project fixed effects and HC3 standard errors. Cluster-robust SEs are
    not used: with six projects they are unreliable."""
    import statsmodels.formula.api as smf
    if data[group].nunique() >= 3:
        for method in ("lbfgs", "powell"):
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")    # boundary / singular RE warnings
                    r = smf.mixedlm(formula, data, groups=data[group]).fit(reml=True, method=method)
                if np.all(np.isfinite(r.bse.values)):
                    return r, f"mixedlm_{method}"
            except Exception:
                continue
    fe = formula + (f" + C({group})" if data[group].nunique() > 1 else "")
    return smf.ols(fe, data).fit(cov_type="HC3"), "ols_project_fe_hc3"


def _coef(res, name):
    try:
        ci = res.conf_int().loc[name]
        return float(res.params[name]), float(ci.iloc[0]), float(ci.iloc[1]), float(res.pvalues[name])
    except Exception:
        return (np.nan,) * 4


# ---------------------------------------------------------------------------
def load():
    d = pd.read_parquet(EVAL)
    d = d[d["study_class"].isin([MONO, POLY])].copy()
    agg = {c: "mean" for c in METRIC_COLS if c in d.columns}
    first = {c: "first" for c in ["study_class", "poly_type", "source", "grain_headline", "grain_strict", "tangled",
                                  "report_len", "n_cand", "n_gt", "n_gt_added", "n_gt_reach",
                                  "n_gt_reach_parseable"] if c in d.columns}
    seeds = d.groupby(KEYS)["seed"].nunique().rename("n_seeds")
    b = d.groupby(KEYS).agg({**agg, **first}).join(seeds).reset_index()
    b["log_ncand"] = np.log(b["n_cand"].clip(lower=1))
    b["log_report"] = np.log1p(b["report_len"])
    b["poly"] = (b["study_class"] == POLY).astype(int)
    return d, b


CONDITIONS = {
    # name: (filter on the seed-averaged table, how Poly-fix is defined)
    "primary":      (lambda x: (x.universe == "R") & (x.gt_filter == "all") & (x.source == "kept"), None),
    "S1_no_tests":  (lambda x: (x.universe == "R") & (x.gt_filter == "no_tests") & (x.source == "kept"), None),
    "S2_headline":  (lambda x: (x.universe == "R") & (x.gt_filter == "all") & (x.source == "kept"), "grain_headline"),
    "S2_strict":    (lambda x: (x.universe == "R") & (x.gt_filter == "all") & (x.source == "kept"), "grain_strict"),
    "S3_universe_T": (lambda x: (x.universe == "T") & (x.gt_filter == "all") & (x.source == "kept"), None),
    "S4_untangled": (lambda x: (x.universe == "R") & (x.gt_filter == "all") & (x.source == "kept") & (~x.tangled.astype(bool)), None),
    "S5_fold1":     (lambda x: (x.universe == "R") & (x.gt_filter == "all") & (x.source == "kept") & (x.fold == 1), None),
    "S5_fold2":     (lambda x: (x.universe == "R") & (x.gt_filter == "all") & (x.source == "kept") & (x.fold == 2), None),
    "S6_removed":   (lambda x: (x.universe == "R") & (x.gt_filter == "all") & (x.source == "removed"), None),
    "S6_kept+removed": (lambda x: (x.universe == "R") & (x.gt_filter == "all"), None),
    # Poly-fix split by what the secondary files are (decided 2026-10-31)
    "P_behavioural": (lambda x: (x.universe == "R") & (x.gt_filter == "all") & (x.source == "kept"), "poly_behavioural"),
    "P_test_only":   (lambda x: (x.universe == "R") & (x.gt_filter == "all") & (x.source == "kept"), "poly_test_only"),
}


def condition(b, name):
    f, grain = CONDITIONS[name]
    x = b[f(b)].dropna(subset=["rr"]).copy()
    if grain and grain.startswith("poly_"):
        # Poly-fix restricted to one sub-type; Mono-fix unchanged
        x = x[(x.study_class == MONO) | (x.poly_type == grain)]
    elif grain:
        # Poly-fix redefined by the stricter grain; Mono-fix unchanged; others dropped
        x = x[(x.study_class == MONO) | x[grain].astype(bool)]
    return x


# ---------------------------------------------------------------------------
def rq3(x, cond):
    rows, models = [], []
    for (tech, view), g in x.groupby(["tech", "view"]):
        outs = (TOPK_OUTCOMES if tech == "LocAgent" else
                OUTCOMES + ["ap10", "rr10"] if tech.startswith("SweRank") else OUTCOMES)
        for y in outs:
            groups = list(g.groupby("project")) + ([("POOLED", g)] if g.project.nunique() > 1 else [])
            for proj, h in groups:
                m, p = h.loc[h.poly == 0, y].values, h.loc[h.poly == 1, y].values
                if len(m) < MIN_CLASS_N_TEST or len(p) < MIN_CLASS_N_TEST:
                    continue
                try:
                    pu = float(mannwhitneyu(p, m, alternative="two-sided").pvalue)
                except ValueError:
                    pu = np.nan
                lo, hi = boot_ci(cliffs_delta, p, m)
                rows.append({"condition": cond, "tech": tech, "view": view, "outcome": y, "project": proj,
                             "n_mono": len(m), "n_poly": len(p), "mean_mono": m.mean(), "mean_poly": p.mean(),
                             "cliffs_delta_poly_vs_mono": cliffs_delta(p, m), "delta_ci_lo": lo,
                             "delta_ci_hi": hi, "mwu_p": pu})
            if min((g.poly == 0).sum(), (g.poly == 1).sum()) >= MIN_CLASS_N_MODEL:
                fold_term = " + C(fold)" if g.fold.nunique() > 1 else ""
                res, kind = _fit_mixed(f"{y} ~ poly + n_gt_reach + log_ncand + log_report{fold_term}", g)
                c, lo, hi, pv = _coef(res, "poly")
                models.append({"condition": cond, "tech": tech, "view": view, "outcome": y, "model": kind,
                               "n_bugs": len(g), "class_effect_poly": c, "ci_lo": lo, "ci_hi": hi, "p": pv})
        # logistic model on Top-10 with project fixed effects (robustness; a
        # cluster-robust GEE is not used because there are only six projects)
        if min((g.poly == 0).sum(), (g.poly == 1).sum()) >= MIN_CLASS_N_MODEL:
            try:
                import statsmodels.formula.api as smf
                gg = g.assign(top10_bin=(g.top10 >= 0.5).astype(int))
                fe = " + C(project)" if gg.project.nunique() > 1 else ""
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    r = smf.logit(f"top10_bin ~ poly + n_gt_reach + log_ncand + log_report{fe}", gg).fit(disp=0)
                c, lo, hi, pv = _coef(r, "poly")
                models.append({"condition": cond, "tech": tech, "view": view, "outcome": "top10 (logit, log-odds)",
                               "model": "logit_project_fe", "n_bugs": len(g), "class_effect_poly": c,
                               "ci_lo": lo, "ci_hi": hi, "p": pv})
            except Exception:
                pass
    t = pd.DataFrame(rows)
    if not t.empty:
        t["mwu_p_holm"] = np.nan
        for _, idx in t[t.project != "POOLED"].groupby(["condition", "tech", "view", "outcome"]).groups.items():
            t.loc[idx, "mwu_p_holm"] = holm(t.loc[idx, "mwu_p"].values)
    return t, pd.DataFrame(models)


def decomposition(x, cond):
    """Poly-fix: primary- vs secondary-language GT; reach@parse; random baseline."""
    rows = []
    for (tech, view, cls), g in x.groupby(["tech", "view", "study_class"]):
        rows.append({"condition": cond, "tech": tech, "view": view, "class": cls, "n_bugs": len(g),
                     "MRR": g.rr.mean(), "MAP": g.ap.mean(), "CFR10": g.cfr10.mean(),
                     "MRR_primary_gt": g.rr_primary.mean() if "rr_primary" in g else np.nan,
                     "MRR_secondary_gt": g.rr_secondary.mean() if "rr_secondary" in g else np.nan,
                     "MAP_primary_gt": g.ap_primary.mean() if "ap_primary" in g else np.nan,
                     "MAP_secondary_gt": g.ap_secondary.mean() if "ap_secondary" in g else np.nan,
                     "reach_at_parse": float((g.n_gt_reach_parseable > 0).mean()),
                     "all_gt_parseable": float((g.n_gt_reach_parseable == g.n_gt_reach).mean()),
                     "random_MRR": g.rand_rr.mean(), "random_top10": g.rand_top10.mean()})
    return pd.DataFrame(rows)


def rq4(x, cond):
    rows, models = [], []
    for label, ta, va, tb, vb, outs in PAIRS:
        A = x[(x.tech == ta) & (x.view == va)].set_index(["fold", "project", "bug_id"])
        B = x[(x.tech == tb) & (x.view == vb)].set_index(["fold", "project", "bug_id"])
        common = A.index.intersection(B.index)
        if len(common) == 0:
            continue
        A, B = A.loc[common], B.loc[common]
        for y in outs:
            if y not in A or y not in B:
                continue
            dd = A[["poly", "n_gt_reach", "log_ncand", "log_report"]].copy()
            dd["d"] = A[y].values - B[y].values
            dd["a"], dd["b"] = A[y].values, B[y].values
            dd = dd.reset_index()
            for cls_v, cls in ((0, MONO), (1, POLY)):
                sub = dd[dd.poly == cls_v]
                pr = []
                groups = list(sub.groupby("project")) + ([("POOLED", sub)] if sub.project.nunique() > 1 else [])
                for proj, h in groups:
                    if len(h) < MIN_CLASS_N_TEST:
                        continue
                    try:
                        pw = float(wilcoxon(h.a, h.b, zero_method="pratt").pvalue) if (h.d != 0).any() else 1.0
                    except ValueError:
                        pw = np.nan
                    lo, hi = boot_ci(lambda v: float(np.mean(v)), h.d.values)
                    pr.append({"condition": cond, "pair": label, "outcome": y, "class": cls, "project": proj,
                               "n_bugs": len(h), "mean_A": h.a.mean(), "mean_B": h.b.mean(),
                               "mean_diff_A_minus_B": h.d.mean(), "diff_ci_lo": lo, "diff_ci_hi": hi,
                               "share_A_better": float((h.d > 0).mean()), "share_B_better": float((h.d < 0).mean()),
                               "cliffs_delta_A_vs_B": cliffs_delta(h.a.values, h.b.values), "wilcoxon_p": pw})
                pr = pd.DataFrame(pr)
                if not pr.empty:
                    m = pr.project != "POOLED"
                    pr.loc[m, "wilcoxon_p_holm"] = holm(pr.loc[m, "wilcoxon_p"].values)
                    rows.append(pr)
            if min((dd.poly == 0).sum(), (dd.poly == 1).sum()) >= MIN_CLASS_N_MODEL:
                fold_term = " + C(fold)" if dd.fold.nunique() > 1 else ""
                res, kind = _fit_mixed(f"d ~ poly + n_gt_reach + log_ncand + log_report{fold_term}", dd)
                c, lo, hi, pv = _coef(res, "poly")
                c0, lo0, hi0, _ = _coef(res, "Intercept")
                mono_d, poly_d = dd.loc[dd.poly == 0, "d"].mean(), dd.loc[dd.poly == 1, "d"].mean()
                models.append({"condition": cond, "pair": label, "outcome": y, "model": kind, "n_bugs": len(dd),
                               "interaction_poly": c, "ci_lo": lo, "ci_hi": hi, "p": pv,
                               "mean_diff_mono": mono_d, "mean_diff_poly": poly_d,
                               "inversion_pattern": bool(poly_d >= 0 and mono_d < 0)})
    return (pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()), pd.DataFrame(models)


def seed_spread(d):
    x = d[(d.universe == "R") & (d.gt_filter == "all") & (d.source == "kept") & d.rr.notna()]
    s = x.groupby(["tech", "view", "fold", "project", "seed"]).agg(MRR=("rr", "mean"), MAP=("ap", "mean")).reset_index()
    return s.groupby(["tech", "view", "fold", "project"]).agg(
        n_seeds=("seed", "nunique"), MRR_mean=("MRR", "mean"), MRR_sd=("MRR", "std"),
        MAP_mean=("MAP", "mean"), MAP_sd=("MAP", "std")).reset_index()


def locagent_variance(d):
    """Main LocAgent run (seed 0) vs the repeats (LocAgentRep, seeds 1..k) on
    the variance subset: per-bug agreement and the spread of MAP@10."""
    x = d[(d.universe == "R") & (d.gt_filter == "all") & (d.view == "all") & d.rr.notna()]
    rep = x[x.tech == "LocAgentRep"]
    if rep.empty:
        return pd.DataFrame()
    main = x[(x.tech == "LocAgent") & x.bug_id.isin(rep.bug_id.unique())].assign(seed=0)
    both = pd.concat([main, rep])
    runs = both.groupby(["project", "seed"]).agg(MAP10=("ap10", "mean"), top10=("top10", "mean"),
                                                 n=("bug_id", "nunique")).reset_index()
    per_bug = both.pivot_table(index=["project", "bug_id"], columns="seed", values="top10")
    agree = float((per_bug.nunique(axis=1) == 1).mean())
    out = runs.groupby("project").agg(n_bugs=("n", "max"), n_runs=("seed", "nunique"),
                                      MAP10_mean=("MAP10", "mean"), MAP10_sd=("MAP10", "std"),
                                      top10_mean=("top10", "mean"), top10_sd=("top10", "std")).reset_index()
    out["top10_agreement_all_runs"] = agree
    return out


def split_composition():
    """G11: class proportions per split (temporal drift)."""
    from Scripts.bugs import chrono_split, load_kept
    k = load_kept().set_index(["repo_name", "bug_id"])
    rows = []
    for fold in (1, 2):
        for repo in P.SELECTED_REPO_NAMES:
            s = chrono_split(repo, fold)
            for part in ("train", "val", "test"):
                c = k.loc[[(repo, b) for b in s[part]], "study_class"].value_counts()
                n = int(c.sum())
                rows.append({"fold": fold, "project": repo, "split": part, "n": n,
                             "pct_mono": round(100 * c.get(MONO, 0) / max(n, 1), 1),
                             "pct_poly": round(100 * c.get(POLY, 0) / max(n, 1), 1)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
def main():
    if not os.path.exists(EVAL):
        print(f"no {EVAL} -- run Scripts/evaluate.py first"); return
    os.makedirs(OUT, exist_ok=True)
    d, b = load()
    rq3_t, rq3_m, rq4_t, rq4_m, dec = [], [], [], [], []
    for cond in CONDITIONS:
        x = condition(b, cond)
        if x.empty:
            continue
        t, m = rq3(x, cond); rq3_t.append(t); rq3_m.append(m)
        t, m = rq4(x, cond); rq4_t.append(t); rq4_m.append(m)
        dec.append(decomposition(x, cond))
    cat = lambda L: pd.concat([z for z in L if z is not None and not z.empty], ignore_index=True) if any(
        z is not None and not z.empty for z in L) else pd.DataFrame()
    tables = {
        "rq3_per_project.csv": cat(rq3_t), "rq3_models.csv": cat(rq3_m),
        "rq4_paired.csv": cat(rq4_t), "rq4_inversion.csv": cat(rq4_m),
        "decomposition.csv": cat(dec), "seed_spread.csv": seed_spread(d),
        "locagent_variance.csv": locagent_variance(d),
        "split_composition.csv": split_composition(),
    }
    for name, t in tables.items():
        t.round(4).to_csv(os.path.join(OUT, name), index=False)

    # short Markdown report: primary condition only
    L = [f"# Objective 2 statistics ({'SMOKE' if SMOKE else 'full'})", "",
         f"Input: `{EVAL}`; bugs (seed-averaged rows): {len(b)}", ""]
    m = tables["rq3_models.csv"]
    if not m.empty:
        L += ["## RQ3 — class effect (Poly-fix minus Mono-fix), pooled model, primary condition", "",
              "Primary outcome: AP (MAP); AP@10 for LocAgent.", "",
              m[m.condition == "primary"].round(4).to_markdown(index=False), ""]
    v = tables["rq4_inversion.csv"]
    if not v.empty:
        L += ["## RQ4 — inversion test (d = A - B; interaction = Poly-fix minus Mono-fix difference)", "",
              v[v.condition == "primary"].round(4).to_markdown(index=False), ""]
    dc = tables["decomposition.csv"]
    if not dc.empty:
        L += ["## Decomposition (primary condition)", "",
              dc[dc.condition == "primary"].round(3).to_markdown(index=False), ""]
    if not v.empty:
        piv = v[v.outcome.isin(["ap", "ap10"])].pivot_table(index=["pair", "outcome"], columns="condition",
                                                             values="interaction_poly")
        L += ["## Sensitivity — interaction estimate under each condition", "", piv.round(4).to_markdown(), ""]
    with open(os.path.join(OUT, "stats_report.md"), "w") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L[:40]))
    print(f"\n-> {OUT}")


if __name__ == "__main__":
    main()
