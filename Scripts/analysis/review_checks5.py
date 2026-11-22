"""
Checks requested by the sixth internal review (2026-11-22), from stored outputs.

  tost_control   TOST (+-0.05, +-0.03) for the parseable-view control interaction
                 (BM25-parse vs FLIM-strict) under every condition
  tost_poly      TOST for the Poly-fix paired differences BM25 - LocAgent (AP@10)
                 and BM25 - SweRank (AP), and BM25 - FLIM-strict for reference
  blaze_all_sec  MAP on the secondary-language files of fold-1 Poly-fix bugs:
                 BLAZE-all against BLAZE (seed 13 and seed-averaged) and BM25,
                 paired bootstrap, TOST
  acc_at_k       share of Python test bugs whose every (non-test) ground-truth
                 file is in the first 5 / 10, the Acc@k of LocAgent and SweRank papers
  example        per-file ranks for localstack 8030 (worked example)

    python Scripts/analysis/review_checks5.py   # -> results/obj2/stats/review_checks5.json
"""

import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import norm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from Scripts import paths as P

ST, EV = os.path.join(P.RESULT_PATH, "stats"), os.path.join(P.RESULT_PATH, "eval")
RNG = np.random.default_rng(20261122)
PY = ["ansible/ansible", "apache/airflow", "localstack/localstack"]
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


# ------------------------------------------------------------------ TOST
inv = pd.read_csv(os.path.join(ST, "rq4_inversion.csv"))
c = inv[(inv.pair == "BM25-parse vs FLIM-strict (control)") & (inv.outcome == "ap")]
OUT["tost_control"] = {r.condition: dict(est=r.interaction_poly, ci=[r.ci_lo, r.ci_hi],
                                         p_tost_005=tost_p(r.interaction_poly, r.ci_lo, r.ci_hi, .05),
                                         p_tost_003=tost_p(r.interaction_poly, r.ci_lo, r.ci_hi, .03))
                       for r in c.itertuples()}

pr = pd.read_csv(os.path.join(ST, "rq4_paired.csv"))
t = {}
for pair, o in [("BM25 vs FLIM-strict", "ap"), ("BM25 vs LocAgent", "ap10"), ("BM25 vs SweRank", "ap")]:
    r = pr[(pr.condition == "primary") & (pr.pair == pair) & (pr.outcome == o) & (pr.project == "POOLED")
           & (pr["class"] == "Poly-fix")].iloc[0]
    t[pair] = dict(diff=r.mean_diff_A_minus_B, ci=[r.diff_ci_lo, r.diff_ci_hi], q_or_p=r.wilcoxon_p,
                   p_tost_005=tost_p(r.mean_diff_A_minus_B, r.diff_ci_lo, r.diff_ci_hi, .05),
                   p_tost_003=tost_p(r.mean_diff_A_minus_B, r.diff_ci_lo, r.diff_ci_hi, .03))
OUT["tost_poly"] = t

# ------------------------------------------------------------------ BLAZE-all on secondary files
G = pd.read_parquet(os.path.join(EV, "per_gt.parquet"))
g = G[(G.universe == "R") & (G.source == "kept") & (G.study_class == "Poly-fix") & (G.view == "all") & (G.fold == 1)]


def sec(tech, seed=None):
    x = g[g.tech == tech]
    if seed is not None:
        x = x[x.seed == seed]
    rows = []
    for (s, p, b), h in x.groupby(["seed", "project", "bug_id"]):
        r = h["rank"].to_numpy(float)
        m = ~h.is_primary.to_numpy(bool)
        if m.any():
            own, oth = r[m], r[~m]
            rows.append(dict(project=p, bug_id=b, sec=ap([q - np.sum(oth < q) for q in own])))
    return pd.DataFrame(rows).groupby(["project", "bug_id"], as_index=False).sec.mean()


a = sec("BLAZE_ALL")
res = {}
for lab, b in (("BLAZE seed 13", sec("BLAZE", 13)), ("BLAZE seed-averaged", sec("BLAZE")), ("BM25", sec("BM25"))):
    j = a.merge(b, on=["project", "bug_id"])
    d = (j.sec_x - j.sec_y).to_numpy()
    bs = np.array([RNG.choice(d, len(d)).mean() for _ in range(4000)])
    lo, hi = float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))
    res[lab] = dict(n=int(len(j)), blaze_all=float(j.sec_x.mean()), other=float(j.sec_y.mean()),
                    diff=float(d.mean()), ci95=[lo, hi], p_tost_005=tost_p(d.mean(), lo, hi, .05),
                    p_tost_003=tost_p(d.mean(), lo, hi, .03))
OUT["blaze_all_sec"] = res

# ------------------------------------------------------------------ Acc@k as in LocAgent / SweRank
h = G[(G.universe == "R") & (G.source == "kept") & (G.view == "all") & G.project.isin(PY)]
acc = {}
for tech in ["LocAgent", "SweRank", "SweRankEmbed", "BM25"]:
    for cls in ["Mono-fix", "Poly-fix"]:
        y = h[(h.tech == tech) & (h.study_class == cls)]
        for lab, sel in (("all_gt", y), ("non_test_gt", y[~y.is_test])):
            m = sel.groupby(["fold", "project", "bug_id"])["rank"].max()
            acc[f"{tech} {cls} {lab}"] = dict(n=int(len(m)), acc5=float((m <= 5).mean()), acc10=float((m <= 10).mean()))
OUT["acc_at_k"] = acc

# ------------------------------------------------------------------ worked example
e = G[(G.project == "localstack/localstack") & (G.bug_id == "8030") & (G.universe == "R") & (G.fold == 1)
      & (G.view == "all") & G.seed.isin([0, 13])]
OUT["example_localstack_8030"] = {f"{r.tech}|{r.path}": r.rank for r in e.itertuples()
                                  if r.tech in ("BM25", "BLAZE", "FLIM", "LocAgent", "SweRank", "SweRankAll", "SweRankNonPy")}


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list):
        return [clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else round(float(o), 4)
    if isinstance(o, np.integer):
        return int(o)
    return o


with open(os.path.join(ST, "review_checks5.json"), "w") as f:
    json.dump(clean(OUT), f, indent=1)
print(json.dumps(clean({k: OUT[k] for k in ("tost_poly", "blaze_all_sec")}), indent=1))
print("control (primary):", clean(OUT["tost_control"]["primary"]))
