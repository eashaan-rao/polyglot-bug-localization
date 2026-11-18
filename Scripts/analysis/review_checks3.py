"""
Checks requested by the third internal review (2026-11-18), from stored outputs.

  noninf        non-inferiority of SweRank variants against BM25 on the secondary
                files of Poly-fix bugs (margin 0.03): paired mean difference, 90%
                bootstrap interval (its lower end is the one-sided 95% bound) and
                the bootstrap share of resamples at or below -0.03
  tost          TOST (+-0.05, +-0.03) for the reranker's interaction, the class
                effects of the partial-corpus and SweRankNonPy variants, and their
                interactions with BM25
  sec_hc        co-change against hybrid on the secondary files, paired, per technique
  rq1           13-project prevalence over all bugs with counted fix files, the
                study vs non-selected comparison pooled and as per-project medians

    python Scripts/analysis/review_checks3.py   # -> results/obj2/stats/review_checks3.json
"""

import json
import os
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.stats import norm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from Scripts import paths as P

warnings.filterwarnings("ignore")
ST, EV = os.path.join(P.RESULT_PATH, "stats"), os.path.join(P.RESULT_PATH, "eval")
RNG = np.random.default_rng(20261119)
PY = ["ansible/ansible", "apache/airflow", "localstack/localstack"]
KEY = ["fold", "project", "bug_id"]
OUT = {}


def tost_p(est, lo, hi, m):
    se = (hi - lo) / 3.92
    return float(max(1 - norm.cdf((est + m) / se), norm.cdf((est - m) / se)))


def ap(r):
    r = np.asarray(r, float)
    if len(r) == 0:
        return np.nan
    h = np.sort(r[np.isfinite(r)])
    return float(np.sum(np.arange(1, len(h) + 1) / h) / len(r)) if len(h) else 0.0


# ------------------------------------------------------------------ secondary files
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
    return pd.DataFrame(rows).groupby(KEY, as_index=False).mean(numeric_only=True) if rows else pd.DataFrame()


def paired(a, b, k, n=4000):
    j = a.merge(b, on=KEY, suffixes=("_a", "_b"))
    dd = (j[f"{k}_a"] - j[f"{k}_b"]).dropna().to_numpy()
    bs = np.array([RNG.choice(dd, len(dd)).mean() for _ in range(n)])
    return dict(n=int(len(dd)), mean=float(dd.mean()), ci90=[float(np.percentile(bs, 5)), float(np.percentile(bs, 95))],
                ci95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                p_noninf_003=float((bs <= -0.03).mean()))


techs = sorted(g.tech.unique())
bm = sec_split("BM25", "all", "ap", PY)
ni = {}
for name, tech in [("SweRank, all files", "SweRankAll"), ("SweRank retriever, all files", "SweRankEmbedAll"),
                   ("SweRank retriever, non-Python added", "SweRankEmbedNonPy"),
                   ("SweRank, non-Python added", "SweRankNonPy")]:
    if tech not in techs:
        continue
    d = sec_split(tech, "all", "ap", PY)
    ni[name] = {k: paired(d, bm, k) for k in ("sec", "sec_test", "sec_behav")}
OUT["noninf"] = ni

# co-change vs hybrid on the secondary files
hc = {}
for lab, h_, c_, o, prj in [("FLIM-strict", "HybridFLIM", "CoChangeFLIM", "ap", None),
                            ("SweRank", "HybridSweRank", "CoChangeSweRank", "ap", PY),
                            ("LocAgent", "HybridLocAgent", "CoChangeLocAgent", "ap10", PY)]:
    hc[lab] = paired(sec_split(c_, "all", o, prj), sec_split(h_, "all", o, prj), "sec")   # co-change minus hybrid
OUT["sec_cochange_minus_hybrid"] = hc

# ------------------------------------------------------------------ TOST
m = pd.read_csv(os.path.join(ST, "rq3_models.csv"))
inv = pd.read_csv(os.path.join(ST, "rq4_inversion.csv"))
t = {}
for tech in ("SweRankEmbedNonPy", "SweRankNonPy", "SweRankAll", "SweRankEmbedAll"):
    r = m[(m.condition == "primary") & (m.tech == tech) & (m.view == "all") & (m.outcome == "ap")]
    if len(r):
        r = r.iloc[0]
        t[f"class_effect {tech}"] = dict(est=r.class_effect_poly, ci=[r.ci_lo, r.ci_hi],
                                         p_tost_005=tost_p(r.class_effect_poly, r.ci_lo, r.ci_hi, .05),
                                         p_tost_003=tost_p(r.class_effect_poly, r.ci_lo, r.ci_hi, .03))
for pair in ("SweRankEmbed vs SweRank (reranker effect)", "BM25 vs SweRankEmbedNonPy", "BM25 vs SweRankNonPy",
             "BM25 vs SweRankAll", "SweRankNonPy vs SweRank (non-Python files added)",
             "SweRankAll vs SweRank (corpus extension)", "SweRank vs SweRankAll (corpus extension)"):
    r = inv[(inv.condition == "primary") & (inv.pair == pair) & (inv.outcome == "ap")]
    if len(r):
        r = r.iloc[0]
        t[f"interaction {pair}"] = dict(est=r.interaction_poly, ci=[r.ci_lo, r.ci_hi],
                                        mean_diff_mono=r.mean_diff_mono, mean_diff_poly=r.mean_diff_poly,
                                        p_tost_005=tost_p(r.interaction_poly, r.ci_lo, r.ci_hi, .05),
                                        p_tost_003=tost_p(r.interaction_poly, r.ci_lo, r.ci_hi, .03))
OUT["tost"] = t

# ------------------------------------------------------------------ RQ1 over 13 projects
bugs = pd.read_csv(os.path.join(P.RESULT_PATH, "rq1_all13_bugs.csv"))
labels = sorted(bugs.cls.unique())
rq = {"class_labels": labels}
# "Excluded" = no counted fix file; a bug counts as Poly-fix only if it is primary-anchored
# (as in the paper's 21.5% over the 4,578 bugs with counted files)
nocount = ["Excluded"]
bugs["pb"], bugs["ph"], bugs["ps"] = bugs.broad & bugs.keep, bugs.headline & bugs.keep, bugs.strict & bugs.keep
per = []
for (repo, sel), x in bugs.groupby(["repo_name", "selected"]):
    c = x[~x.cls.isin(nocount)]
    k = x[x.keep]
    per.append(dict(repo=repo, selected=bool(sel), bugs=len(x), counted=len(c), kept=len(k),
                    kept_share=len(k) / len(x), broad_kept=float(k.broad.mean()) if len(k) else np.nan,
                    broad_counted=float(c.pb.sum() / len(c)) if len(c) else np.nan))
per = pd.DataFrame(per)
rq["per_project"] = per.to_dict("records")
for sel, lab in ((True, "study"), (False, "non_selected"), (None, "all13")):
    x = bugs if sel is None else bugs[bugs.selected == sel]
    k, c = x[x.keep], x[~x.cls.isin(nocount)]
    pp = per if sel is None else per[per.selected == sel]
    rq[lab] = dict(bugs=len(x), counted=len(c), kept=len(k),
                   broad_kept=float(k.broad.mean()), headline_kept=float(k.headline.mean()),
                   strict_kept=float(k.strict.mean()),
                   broad_counted=float(c.pb.sum() / len(c)), headline_counted=float(c.ph.sum() / len(c)),
                   strict_counted=float(c.ps.sum() / len(c)),
                   median_broad_kept=float(pp.broad_kept.median()), median_broad_counted=float(pp.broad_counted.median()))
OUT["rq1"] = rq


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list):
        return [clean(v) for v in o]
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    return o


json.dump(clean(OUT), open(os.path.join(ST, "review_checks3.json"), "w"), indent=1)
print(json.dumps(clean(OUT), indent=1)[:6000])
