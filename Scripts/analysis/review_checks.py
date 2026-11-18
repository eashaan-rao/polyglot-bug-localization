"""
Checks requested by the internal review (2026-11-16), computed from stored
evaluation outputs only (results/obj2/eval, results/obj2/stats).

  1. Equivalence (TOST, margin 0.05 AP) for the "no drop" (BM25, BLAZE) and
     "matches" (BM25 vs FLIM-strict on Poly-fix) claims, from the model CIs.
  2. Decomposition recomputed with the *other* ground-truth files removed from
     the ranking (the stored ap_primary counts them as non-relevant), with
     bootstrap CIs for Poly-fix primary-file AP minus Mono-fix AP.
  3. Benjamini-Hochberg FDR over every class-effect and every interaction test.
  4. Class effect stratified by the number of reachable GT files.
  5. Whole-benchmark MAP including the no-primary bugs of the test periods.
  6. Prevalence denominators; share of unparseable fix files over all kept
     Poly-fix bugs (RQ1 population); parse status of unparseable GT, both folds.
  7. How often the HC3 fallback replaced the mixed model.

    python Scripts/analysis/review_checks.py   # -> results/obj2/stats/review_checks.json
"""

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from Scripts import paths as P
from Scripts.bugs import eval_ground_truth, load_all

ST = os.path.join(P.RESULT_PATH, "stats")
EV = os.path.join(P.RESULT_PATH, "eval")
RNG = np.random.default_rng(20261116)
MARGIN = 0.05
TECHS = [("BM25", "all", "ap"), ("BLAZE", "all", "ap"), ("FLIM", "all", "ap"), ("FLIM", "parse", "ap"),
         ("LocAgent", "all", "ap10"), ("SweRank", "all", "ap")]
# diagnostic variants (2026-11-17/18): decomposition only
VARIANTS = [("SweRankEmbed", "all", "ap"), ("SweRankEmbedAll", "all", "ap"), ("SweRankAll", "all", "ap"),
            ("HybridFLIM", "all", "ap"), ("HybridSweRank", "all", "ap"), ("HybridLocAgent", "all", "ap10"),
            ("BM25", "all", "ap10"), ("CoChangeFLIM", "all", "ap"), ("CoChangeSweRank", "all", "ap"),
            ("CoChangeLocAgent", "all", "ap10")]
OUT = {}


def bh(p):
    p = np.asarray(p, float)
    n = np.isfinite(p).sum()
    order = np.argsort(np.where(np.isfinite(p), p, np.inf))
    q = np.full_like(p, np.nan)
    prev = 1.0
    for rank, i in reversed(list(enumerate(order[:n], 1))):
        prev = min(prev, p[i] * n / rank)
        q[i] = prev
    return q


def ap(ranks):
    ranks = np.asarray(ranks, float)
    if len(ranks) == 0:
        return np.nan
    hit = np.sort(ranks[np.isfinite(ranks)])
    return float(np.sum(np.arange(1, len(hit) + 1) / hit) / len(ranks)) if len(hit) else 0.0


def boot_diff(a, b, n=2000):
    a, b = np.asarray(a), np.asarray(b)
    d = [RNG.choice(a, len(a)).mean() - RNG.choice(b, len(b)).mean() for _ in range(n)]
    return float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


# 1 ------------------------------------------------------------- equivalence
m = pd.read_csv(os.path.join(ST, "rq3_models.csv"))
pr = pd.read_csv(os.path.join(ST, "rq4_paired.csv"))
eq = {}
for t, v, o in [("BM25", "all", "ap"), ("BLAZE", "all", "ap"), ("BM25", "parse", "ap")]:
    r = m[(m.condition == "primary") & (m.tech == t) & (m.view == v) & (m.outcome == o)].iloc[0]
    se = (r.ci_hi - r.ci_lo) / 3.92
    lo90, hi90 = r.class_effect_poly - 1.645 * se, r.class_effect_poly + 1.645 * se
    eq[f"class_effect {t}-{v}"] = dict(est=r.class_effect_poly, ci90=[lo90, hi90],
                                       equivalent=bool(lo90 > -MARGIN and hi90 < MARGIN),
                                       smallest_margin_shown=float(max(abs(lo90), abs(hi90))))
for pair in ["BM25 vs FLIM-strict", "BM25 vs FLIM-fallback", "BM25 vs LocAgent", "BM25 vs SweRank"]:
    out = "ap10" if "LocAgent" in pair else "ap"
    r = pr[(pr.condition == "primary") & (pr.pair == pair) & (pr.outcome == out) & (pr.project == "POOLED")
           & (pr["class"] == "Poly-fix")].iloc[0]
    se = (r.diff_ci_hi - r.diff_ci_lo) / 3.92
    lo90, hi90 = r.mean_diff_A_minus_B - 1.645 * se, r.mean_diff_A_minus_B + 1.645 * se
    eq[f"poly_diff {pair}"] = dict(est=r.mean_diff_A_minus_B, ci95=[r.diff_ci_lo, r.diff_ci_hi], ci90=[lo90, hi90],
                                   equivalent=bool(lo90 > -MARGIN and hi90 < MARGIN))
OUT["equivalence_margin_0.05"] = eq

# 2 ------------------------------------------------------------- decomposition
g = pd.read_parquet(os.path.join(EV, "per_gt.parquet"))
g = g[(g.universe == "R") & (g.source == "kept") & g.study_class.isin(["Mono-fix", "Poly-fix"])]
dec = {}
for t, v, o in TECHS + VARIANTS:
    x = g[(g.tech == t) & (g.view == v)]
    rows = []
    for (fold, seed, proj, bug), h in x.groupby(["fold", "seed", "project", "bug_id"], sort=False):
        r = h["rank"].to_numpy(float)
        prim = h["is_primary"].to_numpy(bool)
        cls = h["study_class"].iat[0]
        if o == "ap10":
            cut = lambda a: np.where(a <= 10, a, np.inf)
        else:
            cut = lambda a: a
        rec = dict(fold=fold, seed=seed, project=proj, bug_id=bug, cls=cls, ap_all=ap(cut(r)))
        if cls == "Poly-fix":
            for lab, mk in (("prim", prim), ("sec", ~prim)):
                if mk.any():
                    own, other = r[mk], r[~mk]
                    adj = np.array([q - np.sum(other < q) for q in own])      # other GT files removed
                    rec[f"ap_{lab}_removed"] = ap(cut(adj))
                    rec[f"ap_{lab}_nonrel"] = ap(cut(own))                    # as stored
        rows.append(rec)
    d = pd.DataFrame(rows).groupby(["fold", "project", "bug_id", "cls"], as_index=False).mean(numeric_only=True)
    mono = d[d.cls == "Mono-fix"].ap_all.dropna().values
    res = dict(mono=float(mono.mean()))
    for k in ("prim_removed", "prim_nonrel", "sec_removed", "sec_nonrel"):
        vals = d[d.cls == "Poly-fix"][f"ap_{k}"].dropna().values
        res[f"poly_{k}"] = float(vals.mean())
        if k.startswith("prim"):
            res[f"poly_{k}_minus_mono_ci"] = boot_diff(vals, mono)
    dec[f"{t}-{v}-{o}"] = res
    if t == "BM25":   # Python projects only, for the LLM-based techniques and their variants
        dp = d[d.project.isin(["ansible/ansible", "apache/airflow", "localstack/localstack"])]
        dec[f"{t}-{v}-{o}-py"] = dict(
            mono=float(dp[dp.cls == "Mono-fix"].ap_all.mean()),
            poly_prim_removed=float(dp[dp.cls == "Poly-fix"].ap_prim_removed.mean()),
            poly_sec_removed=float(dp[dp.cls == "Poly-fix"].ap_sec_removed.mean()))
OUT["decomposition"] = dec

# 3 ------------------------------------------------------------- FDR
inv = pd.read_csv(os.path.join(ST, "rq4_inversion.csv"))
mm = m[m.model != "logit_project_fe"].copy()
mm["q"] = bh(mm.p.values)
inv = inv.copy()
inv["q"] = bh(inv.p.values)
pr2 = pr[pr.project == "POOLED"].copy()
pr2["q"] = bh(pr2.wilcoxon_p.values)
keyc = mm[(mm.condition == "primary") & (mm.outcome.isin(["ap", "ap10"]))][["tech", "view", "outcome", "class_effect_poly", "p", "q"]]
keyi = inv[(inv.condition == "primary") & (inv.outcome.isin(["ap", "ap10"]))][["pair", "outcome", "interaction_poly", "p", "q"]]
keyp = pr2[(pr2.condition == "primary") & (pr2.outcome.isin(["ap", "ap10"]))][["pair", "class", "outcome", "mean_diff_A_minus_B", "wilcoxon_p", "q"]]
OUT["fdr"] = dict(n_class_tests=int(len(mm)), n_interaction_tests=int(len(inv)), n_pooled_paired_tests=int(len(pr2)),
                  class_effects=keyc.round(4).to_dict("records"), interactions=keyi.round(4).to_dict("records"),
                  pooled_paired=keyp.round(4).to_dict("records"))

# 4 ------------------------------------------------------------- n_gt strata
b = pd.read_parquet(os.path.join(EV, "per_bug.parquet"))
b = b[(b.universe == "R") & (b.gt_filter == "all") & (b.source == "kept") & b.study_class.isin(["Mono-fix", "Poly-fix"])
      & b.rr.notna()]
strata = {}
for t, v, o in TECHS:
    x = b[(b.tech == t) & (b.view == v)].groupby(["fold", "project", "bug_id", "study_class"], as_index=False).agg(
        y=(o, "mean"), n=("n_gt_reach", "first"))
    x["s"] = x.n.clip(upper=5)
    num = den = 0.0
    per = {}
    for s_, h in x.groupby("s"):
        a_, c_ = h[h.study_class == "Poly-fix"].y, h[h.study_class == "Mono-fix"].y
        if len(a_) >= 5 and len(c_) >= 5:
            w = 1 / (1 / len(a_) + 1 / len(c_))
            num += w * (a_.mean() - c_.mean())
            den += w
            per[int(s_)] = dict(n_poly=int(len(a_)), n_mono=int(len(c_)), diff=round(float(a_.mean() - c_.mean()), 4))
    boots = []
    for _ in range(1000):
        nn = dd = 0.0
        for s_, h in x.groupby("s"):
            a_, c_ = h[h.study_class == "Poly-fix"].y.values, h[h.study_class == "Mono-fix"].y.values
            if len(a_) >= 5 and len(c_) >= 5:
                w = 1 / (1 / len(a_) + 1 / len(c_))
                nn += w * (RNG.choice(a_, len(a_)).mean() - RNG.choice(c_, len(c_)).mean())
                dd += w
        boots.append(nn / dd)
    strata[f"{t}-{v}-{o}"] = dict(stratified_diff=num / den, ci=[float(np.percentile(boots, 2.5)),
                                  float(np.percentile(boots, 97.5))], unadjusted=float(
        x[x.study_class == "Poly-fix"].y.mean() - x[x.study_class == "Mono-fix"].y.mean()), per_stratum=per)
OUT["ngt_stratified"] = strata

# 5 ------------------------------------------------------------- whole benchmark
ball = pd.read_parquet(os.path.join(EV, "per_bug.parquet"))
ball = ball[(ball.universe == "R") & (ball.gt_filter == "all") & ball.rr.notna()]
npb = ball[(ball.source == "no_primary") & (ball.tech == "BM25") & (ball.view == "all")]
wb = {}
py = {"ansible/ansible", "apache/airflow", "localstack/localstack"}
for t, v, o in TECHS:
    k = b[(b.tech == t) & (b.view == v)].groupby(["fold", "project", "bug_id"], as_index=False)[o].mean()
    proj = set(k.project)
    nb = npb[npb.project.isin(proj)]
    no_primary_ap = nb[o].values if t == "BM25" else np.zeros(len(nb))
    if t == "BLAZE":
        continue            # BLAZE could read these files but was not run on them
    wb[f"{t}-{v}-{o}"] = dict(kept_only=float(k[o].mean()), n_kept=int(len(k)), n_no_primary=int(len(nb)),
                              with_no_primary=float((k[o].sum() + no_primary_ap.sum()) / (len(k) + len(nb))))
kpy = b[(b.tech == "BM25") & (b.view == "all") & b.project.isin(py)].groupby(["fold", "project", "bug_id"])[["ap", "ap10"]].mean()
nbpy = npb[npb.project.isin(py)]
wb["BM25-all (Python)"] = dict(ap_kept=float(kpy.ap.mean()), ap10_kept=float(kpy.ap10.mean()), n_no_primary=int(len(nbpy)),
                               ap_with=float((kpy.ap.sum() + nbpy.ap.sum()) / (len(kpy) + len(nbpy))),
                               ap10_with=float((kpy.ap10.sum() + nbpy.ap10.sum()) / (len(kpy) + len(nbpy))))
OUT["whole_benchmark"] = wb

# 6 ------------------------------------------------------------- prevalence, parse status
k = load_all()
k = k[k["source"] == "kept"] if "source" in k.columns else k
lang = dict(P.SELECTED_PROJECTS)
pol = k[k.study_class == "Poly-fix"]
n_files = n_sec = 0
for repo, bug in zip(pol.repo_name, pol.bug_id):
    prim = {"java": "Java", "python": "Python"}[lang[repo]]
    gts = eval_ground_truth(repo, bug)
    n_files += len(gts)
    n_sec += sum(x["language"] != prim for x in gts)
gp = g[(g.tech == "BM25") & (g.view == "all") & (g.study_class == "Poly-fix")]
OUT["prevalence"] = dict(poly=int(len(pol)), kept=int(len(k)), share_kept=len(pol) / len(k),
                         share_all_4995=len(pol) / 4995, share_with_counted_files_4578=len(pol) / 4578,
                         rq1_poly_fix_files=n_files, rq1_poly_secondary_files=n_sec,
                         rq1_secondary_share=n_sec / n_files,
                         parse_status_unparseable_gt_by_fold={str(f): h[~h.parse_status.isin(["ok", "ok_nofunc"])]
                                                              .parse_status.value_counts().to_dict()
                                                              for f, h in gp.groupby("fold")})
# 7 ------------------------------------------------------------- fallback use
OUT["hc3_fallback"] = dict(class_models=int((m.model == "ols_project_fe_hc3").sum()),
                           class_models_total=int((m.model != "logit_project_fe").sum()),
                           interaction_models=int((inv.model == "ols_project_fe_hc3").sum()),
                           interaction_total=int(len(inv)),
                           primary_ap_class=m[(m.condition == "primary") & m.outcome.isin(["ap", "ap10"])]
                           [["tech", "view", "model"]].to_dict("records"),
                           primary_ap_inter=inv[(inv.condition == "primary") & inv.outcome.isin(["ap", "ap10"])]
                           [["pair", "model"]].to_dict("records"))

with open(os.path.join(ST, "review_checks.json"), "w") as f:
    json.dump(OUT, f, indent=1, default=float)
print(json.dumps(OUT, indent=1, default=lambda x: round(float(x), 4)))
