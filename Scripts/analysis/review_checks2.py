"""
Checks requested by the second internal review (2026-11-18), from stored
evaluation outputs (results/obj2/eval) only.

  tost          TOST p-values (margins 0.05 and 0.03) for every equivalence-type claim
  sec_split     secondary-file MAP split into behaviour-bearing and test-asset files
                (other GT files removed from the ranking), with bootstrap CIs and
                paired differences against BM25
  sec_ci        bootstrap CIs for BM25 / BLAZE / FLIM-fallback on secondary files
  overall       overall MAP (both classes) of every diagnostic variant vs its original
  whole         whole-benchmark MAP with the no-primary bugs, per project and without
                dolphinscheduler's front-end (TypeScript/Vue) fixes, with a paired
                bootstrap CI and TOST for FLIM-strict - BM25
  bm25_py       BM25's adjusted class effect on the Python subset (mixed model)
  fraclogit     fractional-logit (binomial GLM, logit link) class effects and
                interactions, project and fold fixed effects, robust errors
  hyb_vs_cc     hybrid vs co-change, paired, per class

    python Scripts/analysis/review_checks2.py   # -> results/obj2/stats/review_checks2.json
"""

import json
import os
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.stats import norm, wilcoxon

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from Scripts import paths as P

warnings.filterwarnings("ignore")
ST, EV = os.path.join(P.RESULT_PATH, "stats"), os.path.join(P.RESULT_PATH, "eval")
RNG = np.random.default_rng(20261118)
PY = ["ansible/ansible", "apache/airflow", "localstack/localstack"]
KEY = ["fold", "project", "bug_id"]
OUT = {}


def tost_p(est, lo, hi, m):
    se = (hi - lo) / 3.92
    return float(max(1 - norm.cdf((est + m) / se), norm.cdf((est - m) / se)))


def boot(x, n=2000):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    b = [RNG.choice(x, len(x)).mean() for _ in range(n)]
    return [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))]


def ap(r):
    r = np.asarray(r, float)
    if len(r) == 0:
        return np.nan
    h = np.sort(r[np.isfinite(r)])
    return float(np.sum(np.arange(1, len(h) + 1) / h) / len(r)) if len(h) else 0.0


# ------------------------------------------------------------------ load
b = pd.read_parquet(os.path.join(EV, "per_bug.parquet"))
b = b[(b.universe == "R") & (b.gt_filter == "all") & b.rr.notna()]
kept = b[(b.source == "kept") & b.study_class.isin(["Mono-fix", "Poly-fix"])]


def perbug(tech, view, out, projects=None):
    x = kept[(kept.tech == tech) & (kept.view == view)]
    if projects:
        x = x[x.project.isin(projects)]
    return x.groupby(KEY + ["study_class"], as_index=False).agg(
        y=(out, "mean"), n_gt=("n_gt_reach", "first"), n_cand=("n_cand", "first"), rl=("report_len", "first"))


# ------------------------------------------------------------------ TOST
m = pd.read_csv(os.path.join(ST, "rq3_models.csv"))
pr = pd.read_csv(os.path.join(ST, "rq4_paired.csv"))
inv = pd.read_csv(os.path.join(ST, "rq4_inversion.csv"))
t = {}
for tech, view, o in [("BM25", "all", "ap"), ("BLAZE", "all", "ap"), ("SweRankAll", "all", "ap"),
                      ("SweRankEmbedAll", "all", "ap"), ("CoChangeFLIM", "all", "ap")]:
    r = m[(m.condition == "primary") & (m.tech == tech) & (m.view == view) & (m.outcome == o)]
    if len(r):
        r = r.iloc[0]
        t[f"class_effect {tech}"] = dict(est=r.class_effect_poly, ci=[r.ci_lo, r.ci_hi],
                                         p_tost_005=tost_p(r.class_effect_poly, r.ci_lo, r.ci_hi, .05),
                                         p_tost_003=tost_p(r.class_effect_poly, r.ci_lo, r.ci_hi, .03))
for pair, o in [("BM25 vs FLIM-strict", "ap"), ("BM25 vs FLIM-fallback", "ap"), ("BM25 vs LocAgent", "ap10"),
                ("BM25 vs SweRank", "ap"), ("BM25-parse vs FLIM-strict (control)", "ap")]:
    for cls in ("Mono-fix", "Poly-fix"):
        r = pr[(pr.condition == "primary") & (pr.pair == pair) & (pr.outcome == o) & (pr.project == "POOLED")
               & (pr["class"] == cls)]
        if len(r):
            r = r.iloc[0]
            t[f"{pair} {cls}"] = dict(est=r.mean_diff_A_minus_B, ci=[r.diff_ci_lo, r.diff_ci_hi],
                                      p_tost_005=tost_p(r.mean_diff_A_minus_B, r.diff_ci_lo, r.diff_ci_hi, .05),
                                      p_tost_003=tost_p(r.mean_diff_A_minus_B, r.diff_ci_lo, r.diff_ci_hi, .03))
r = inv[(inv.condition == "primary") & (inv.pair == "BM25 vs SweRankAll") & (inv.outcome == "ap")]
if len(r):
    r = r.iloc[0]
    t["interaction BM25 vs SweRankAll"] = dict(est=r.interaction_poly, ci=[r.ci_lo, r.ci_hi],
                                               p_tost_005=tost_p(r.interaction_poly, r.ci_lo, r.ci_hi, .05))
OUT["tost"] = t

# ------------------------------------------------------------------ secondary split
g = pd.read_parquet(os.path.join(EV, "per_gt.parquet"))
g = g[(g.universe == "R") & (g.source == "kept") & (g.study_class == "Poly-fix")]


def sec_split(tech, view, o, projects=None):
    x = g[(g.tech == tech) & (g.view == view)]
    if projects:
        x = x[x.project.isin(projects)]
    rows = []
    for (f, s_, p, bug), h in x.groupby(["fold", "seed", "project", "bug_id"], sort=False):
        r = h["rank"].to_numpy(float)
        sec = ~h["is_primary"].to_numpy(bool)
        tst = h["is_test"].to_numpy(bool)
        cut = (lambda a: np.where(a <= 10, a, np.inf)) if o == "ap10" else (lambda a: a)
        rec = dict(fold=f, project=p, bug_id=bug)
        for lab, mk in (("sec", sec), ("sec_test", sec & tst), ("sec_behav", sec & ~tst)):
            if mk.any():
                own, oth = r[mk], r[~mk]
                rec[lab] = ap(cut(np.array([q - np.sum(oth < q) for q in own])))
        rows.append(rec)
    d = pd.DataFrame(rows).groupby(KEY, as_index=False).mean(numeric_only=True)
    return d


ss = {}
splits = {}
for name, tech, view, o, prj in [("BM25 (all)", "BM25", "all", "ap", None), ("BLAZE", "BLAZE", "all", "ap", None),
                                 ("FLIM-fallback", "FLIM", "all", "ap", None),
                                 ("BM25 (Python)", "BM25", "all", "ap", PY),
                                 ("SweRank retriever, all files", "SweRankEmbedAll", "all", "ap", PY),
                                 ("SweRank, all files", "SweRankAll", "all", "ap", PY),
                                 ("SweRank retriever, non-Python added", "SweRankEmbedNonPy", "all", "ap", PY),
                                 ("SweRank retriever, Python tests added", "SweRankEmbedPyTest", "all", "ap", PY),
                                 ("SweRank retriever, all files, 10 chunks", "SweRankEmbedAllCap10", "all", "ap", PY),
                                 ("Hybrid SweRank", "HybridSweRank", "all", "ap", PY),
                                 ("Co-change SweRank", "CoChangeSweRank", "all", "ap", PY)]:
    d = sec_split(tech, view, o, prj)
    if d.empty:
        continue
    splits[name] = d
    ss[name] = {k: dict(map=float(d[k].mean()), n=int(d[k].notna().sum()), ci=boot(d[k]))
                for k in ("sec", "sec_test", "sec_behav") if k in d}
# paired differences on the same Poly-fix bugs
for a_, b_ in [("SweRank, all files", "BM25 (Python)"), ("SweRank retriever, all files", "BM25 (Python)"),
               ("BM25 (all)", "BLAZE"), ("BM25 (all)", "FLIM-fallback"), ("BLAZE", "FLIM-fallback")]:
    if a_ in splits and b_ in splits:
        j = splits[a_].merge(splits[b_], on=KEY, suffixes=("_a", "_b"))
        for k in ("sec", "sec_test", "sec_behav"):
            dd = (j[f"{k}_a"] - j[f"{k}_b"]).dropna()
            if len(dd):
                ss[f"diff {a_} - {b_}"] = ss.get(f"diff {a_} - {b_}", {})
                ss[f"diff {a_} - {b_}"][k] = dict(mean=float(dd.mean()), ci=boot(dd), n=int(len(dd)),
                                                   wilcoxon_p=float(wilcoxon(dd).pvalue) if (dd != 0).any() else 1.0)
OUT["sec_split"] = ss

# ------------------------------------------------------------------ overall MAP of variants
ov = {}
for var, orig, o in [("HybridFLIM", ("FLIM", "parse"), "ap"), ("CoChangeFLIM", ("FLIM", "parse"), "ap"),
                     ("HybridSweRank", ("SweRank", "all"), "ap"), ("CoChangeSweRank", ("SweRank", "all"), "ap"),
                     ("SweRankAll", ("SweRank", "all"), "ap"), ("SweRankEmbedAll", ("SweRankEmbed", "all"), "ap"),
                     ("HybridLocAgent", ("LocAgent", "all"), "ap10"), ("CoChangeLocAgent", ("LocAgent", "all"), "ap10")]:
    a_ = perbug(var, "all", o)
    b_ = perbug(orig[0], orig[1], o)
    j = a_.merge(b_, on=KEY + ["study_class"], suffixes=("_v", "_o"))
    if j.empty:
        continue
    dd = j.y_v - j.y_o
    ov[f"{var} vs {orig[0]}-{orig[1]}"] = dict(n=int(len(j)), map_variant=float(j.y_v.mean()), map_orig=float(j.y_o.mean()),
                                               diff=float(dd.mean()), ci=boot(dd), wilcoxon_p=float(wilcoxon(dd).pvalue))
# hybrid vs co-change
hc = {}
for h_, c_, o in [("HybridFLIM", "CoChangeFLIM", "ap"), ("HybridSweRank", "CoChangeSweRank", "ap"),
                  ("HybridLocAgent", "CoChangeLocAgent", "ap10")]:
    j = perbug(h_, "all", o).merge(perbug(c_, "all", o), on=KEY + ["study_class"], suffixes=("_h", "_c"))
    for cls in ("Mono-fix", "Poly-fix", "all"):
        jj = j if cls == "all" else j[j.study_class == cls]
        dd = jj.y_h - jj.y_c
        hc[f"{h_} - {c_} {cls}"] = dict(n=int(len(jj)), diff=float(dd.mean()), ci=boot(dd),
                                        wilcoxon_p=float(wilcoxon(dd).pvalue) if (dd != 0).any() else 1.0)
OUT["overall"] = ov
OUT["hyb_vs_cc"] = hc

# ------------------------------------------------------------------ whole benchmark
cls = pd.read_parquet(P.BUG_CLASSIFICATION_PARQUET)[["repo_name", "bug_id", "languages"]]
cls["bug_id"] = cls.bug_id.astype(str)
npb = b[(b.source == "no_primary")]
dolph_fe = set()
for r in cls[cls.repo_name == "apache/dolphinscheduler"].itertuples():
    langs = set(json.loads(r.languages)) if r.languages else set()
    if langs and langs <= {"TypeScript", "JavaScript", "Vue", "CSS", "SCSS", "Less", "HTML"}:
        dolph_fe.add(r.bug_id)
wb = {}
for scope, drop_fe in (("all projects", False), ("without dolphinscheduler front-end", True)):
    res = {}
    for tech, view, nptech in (("BM25", "all", "BM25"), ("FLIM", "parse", None), ("BLAZE", "all", "BLAZE_NP")):
        k_ = perbug(tech, view, "ap")[KEY + ["y"]]
        if nptech:
            n_ = npb[(npb.tech == nptech) & (npb.view == "all")].groupby(KEY, as_index=False).agg(y=("ap", "mean"))
        else:
            n_ = npb[(npb.tech == "BM25") & (npb.view == "all")].groupby(KEY, as_index=False).agg(y=("ap", "mean"))
            n_["y"] = 0.0
        if drop_fe:
            n_ = n_[~((n_.project == "apache/dolphinscheduler") & n_.bug_id.astype(str).isin(dolph_fe))]
        res[f"{tech}-{view}"] = pd.concat([k_.assign(np_=False), n_.assign(np_=True)], ignore_index=True)
    out = {}
    for k_, d in res.items():
        out[k_] = dict(n_kept=int((~d.np_).sum()), n_noprimary=int(d.np_.sum()), map_kept=float(d[~d.np_].y.mean()),
                       map_whole=float(d.y.mean()),
                       per_project={p: dict(kept=float(h[~h.np_].y.mean()), whole=float(h.y.mean()),
                                            n_np=int(h.np_.sum())) for p, h in d.groupby("project")})
    j = res["FLIM-parse"].merge(res["BM25-all"], on=KEY, suffixes=("_f", "_b"))
    dd = j.y_f - j.y_b
    ci = boot(dd)
    out["FLIM-strict - BM25 (whole)"] = dict(diff=float(dd.mean()), ci=ci, p_tost_005=tost_p(dd.mean(), ci[0], ci[1], .05),
                                            p_tost_003=tost_p(dd.mean(), ci[0], ci[1], .03))
    if "BLAZE-all" in res and res["BLAZE-all"].np_.any():
        j = res["BLAZE-all"].merge(res["BM25-all"], on=KEY, suffixes=("_z", "_b"))
        jn = j[j.np__z]
        out["BLAZE - BM25 on no-primary"] = dict(n=int(len(jn)), blaze=float(jn.y_z.mean()), bm25=float(jn.y_b.mean()),
                                                 diff=float((jn.y_z - jn.y_b).mean()), ci=boot(jn.y_z - jn.y_b))
    wb[scope] = out
wb["n_dolphinscheduler_frontend_noprimary_test"] = int(npb[(npb.tech == "BM25") & (npb.project == "apache/dolphinscheduler")
                                                       & npb.bug_id.astype(str).isin(dolph_fe)].groupby(KEY).ngroups)
OUT["whole"] = wb

# ------------------------------------------------------------------ BM25 on the Python subset
import statsmodels.formula.api as smf  # noqa: E402

bp = {}
for o in ("ap", "ap10"):
    d = perbug("BM25", "all", o, PY)
    d["poly"] = (d.study_class == "Poly-fix").astype(int)
    d["log_ncand"], d["log_report"] = np.log(d.n_cand.clip(lower=1)), np.log1p(d.rl)
    try:
        r = smf.mixedlm("y ~ poly + n_gt + log_ncand + log_report + C(fold)", d, groups=d["project"]).fit(reml=True, method="powell")
        model = "mixedlm"
    except Exception:
        r = smf.ols("y ~ poly + n_gt + log_ncand + log_report + C(fold) + C(project)", d).fit(cov_type="HC3")
        model = "ols_fe_hc3"
    ci = r.conf_int().loc["poly"].tolist()
    bp[o] = dict(model=model, est=float(r.params["poly"]), ci=ci, p=float(r.pvalues["poly"]), n=int(len(d)))
OUT["bm25_python_class_effect"] = bp

# ------------------------------------------------------------------ fractional logit
import statsmodels.api as sm  # noqa: E402

fl = {}
for tech, view, o, prj in [("BM25", "all", "ap", None), ("BLAZE", "all", "ap", None), ("FLIM", "parse", "ap", None),
                           ("FLIM", "all", "ap", None), ("LocAgent", "all", "ap10", None), ("SweRank", "all", "ap", None),
                           ("SweRankAll", "all", "ap", None), ("BM25", "all", "ap", PY)]:
    d = perbug(tech, view, o, prj)
    if d.empty:
        continue
    d["poly"] = (d.study_class == "Poly-fix").astype(int)
    d["log_ncand"], d["log_report"] = np.log(d.n_cand.clip(lower=1)), np.log1p(d.rl)
    f = "y ~ poly + n_gt + log_ncand + log_report + C(fold)" + (" + C(project)" if d.project.nunique() > 1 else "")
    r = smf.glm(f, d, family=sm.families.Binomial()).fit(cov_type="HC1")
    d1, d0 = d.assign(poly=1), d.assign(poly=0)
    ame = float((r.predict(d1) - r.predict(d0)).mean())
    fl[f"{tech}-{view}-{o}{'-py' if prj else ''}"] = dict(coef=float(r.params["poly"]), p=float(r.pvalues["poly"]),
                                                          ci=r.conf_int().loc["poly"].tolist(), ame=ame, n=int(len(d)))
for lab, (ta, va), (tb, vb), o in [("BM25 vs FLIM-strict", ("BM25", "all"), ("FLIM", "parse"), "ap"),
                                   ("BM25-parse vs FLIM-strict (control)", ("BM25", "parse"), ("FLIM", "parse"), "ap"),
                                   ("BM25 vs LocAgent", ("BM25", "all"), ("LocAgent", "all"), "ap10"),
                                   ("BM25 vs SweRank", ("BM25", "all"), ("SweRank", "all"), "ap"),
                                   ("BM25 vs SweRankAll", ("BM25", "all"), ("SweRankAll", "all"), "ap")]:
    A, B = perbug(ta, va, o), perbug(tb, vb, o)
    common = A.merge(B[KEY], on=KEY)
    L = pd.concat([common.assign(tech=0), B.merge(common[KEY], on=KEY).assign(tech=1)], ignore_index=True)
    L["poly"] = (L.study_class == "Poly-fix").astype(int)
    L["log_ncand"], L["log_report"] = np.log(L.n_cand.clip(lower=1)), np.log1p(L.rl)
    f = ("y ~ tech * (poly + n_gt + log_ncand + log_report + C(fold))" +
         (" + C(project)" if L.project.nunique() > 1 else ""))
    r = smf.glm(f, L, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(
        L.project.astype(str) + "/" + L.bug_id.astype(str) + "/" + L.fold.astype(str))[0]})
    k_ = "tech:poly"
    fl[f"interaction {lab}"] = dict(coef=float(-r.params[k_]), p=float(r.pvalues[k_]),
                                    note="sign flipped: positive = BM25 gains more on Poly-fix")
OUT["fraclogit"] = fl

with open(os.path.join(ST, "review_checks2.json"), "w") as fh:
    json.dump(OUT, fh, indent=1, default=float)
print(json.dumps(OUT, indent=1, default=lambda x: round(float(x), 4))[:6000])
