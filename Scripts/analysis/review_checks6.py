"""
Checks requested by the eighth internal review (2026-11-22), from stored outputs.

  source_only    the comparison a source-only benchmark would report: every technique
                 scored in the parseable view (only primary-language files are
                 candidates) with the ground truth restricted to the bug's
                 primary-language files, over all primary-anchored test bugs; against
                 the full evaluation (all counted files as ground truth, FLIM-strict in
                 its published parseable view, BM25 over all files), with and without
                 the no-primary bugs. Paired mean differences X - BM25 with 95%
                 bootstrap intervals.
  flim_python    FLIM-strict's adjusted class effect on the three Python projects,
                 the sample of LocAgent and SweRank
  python_test_files  Python test files in the ground truth (SweRank bugs)
  test_share     share of Mono-fix / Poly-fix test bugs with a test file in their
                 ground truth (all projects and the Python projects)
  raw_vs_adj     raw pooled Poly-fix minus Mono-fix mean against the adjusted effect

    python Scripts/analysis/review_checks6.py   # -> results/obj2/stats/review_checks6.json
"""

import json
import os
import sys
import warnings

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from Scripts import paths as P
from Scripts.analysis.obj2_stats import _fit_mixed, _coef, load, condition

warnings.filterwarnings("ignore")
ST, EV = os.path.join(P.RESULT_PATH, "stats"), os.path.join(P.RESULT_PATH, "eval")
RNG = np.random.default_rng(20261123)
PY = ["ansible/ansible", "apache/airflow", "localstack/localstack"]
KEY = ["fold", "project", "bug_id"]
OUT = {}


def ap(r, cut=None):
    r = np.asarray(r, float)
    if len(r) == 0:
        return np.nan
    if cut:
        r = np.where(r <= cut, r, np.inf)
    h = np.sort(r[np.isfinite(r)])
    return float(np.sum(np.arange(1, len(h) + 1) / h) / len(r)) if len(h) else 0.0


def boot(d, n=4000):
    d = np.asarray(d, float)
    bs = np.array([RNG.choice(d, len(d)).mean() for _ in range(n)])
    return [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]


# ------------------------------------------------------------------ source-only benchmark
G = pd.read_parquet(os.path.join(EV, "per_gt.parquet"))
G = G[G.universe == "R"]


def per_bug(tech, view, source, primary_only, cut=None):
    """Seed-averaged AP per bug from the ranks of its reachable ground-truth files.
    Primary-anchored bugs: Mono-fix and Poly-fix only (as in the main comparison).
    No-primary bugs: the parser-dependent techniques reach no ground-truth file, so
    their AP is 0 (they have no score rows for these bugs)."""
    if source == "no_primary" and tech != "BM25":
        z = per_bug("BM25", "all", source, False)
        return z.assign(ap=0.0)
    x = G[(G.tech == tech) & (G.view == view) & (G.source == source)]
    if source == "kept":
        x = x[x.study_class.isin(["Mono-fix", "Poly-fix"])]
    if primary_only:
        x = x[x.is_primary.astype(bool)]
    rows = [dict(fold=f, project=p, bug_id=b, ap=ap(h["rank"].to_numpy(float), cut))
            for (f, s, p, b), h in x.groupby(["fold", "seed", "project", "bug_id"])]
    return pd.DataFrame(rows).groupby(KEY, as_index=False).ap.mean()


def compare(spec, label):
    out = {}
    for tech, cut, projects in (("FLIM", None, None), ("SweRank", None, PY), ("LocAgent", 10, PY)):
        res = {}
        for name, (tv, bv, srcs, prim) in spec.items():
            a = pd.concat([per_bug(tech, tv, s, prim, cut) for s in srcs])
            b = pd.concat([per_bug("BM25", bv, s, prim, cut) for s in srcs])
            j = a.merge(b, on=KEY, suffixes=("_x", "_bm25"))
            if projects:
                j = j[j.project.isin(projects)]
            d = (j.ap_x - j.ap_bm25).to_numpy()
            res[name] = dict(n=int(len(j)), tech=float(j.ap_x.mean()), bm25=float(j.ap_bm25.mean()),
                             diff=float(d.mean()), ci95=boot(d))
        out[tech] = res
    OUT[label] = out


compare({
    # name: (technique view, BM25 view, sources, ground truth restricted to primary-language files)
    "source-only benchmark": ("parse", "parse", ["kept"], True),
    "full, primary-anchored": ("parse", "all", ["kept"], False),
    "full, primary-anchored + no-primary": ("parse", "all", ["kept", "no_primary"], False),
}, "source_only")

# ------------------------------------------------------------------ FLIM-strict on the Python projects
_, B = load()
x = condition(B, "primary")
g = x[(x.tech == "FLIM") & (x.view == "parse") & x.project.isin(PY)]
res, kind = _fit_mixed("ap ~ poly + n_gt_reach + log_ncand + log_report + C(fold)", g)
c, lo, hi, pv = _coef(res, "poly")
OUT["flim_python"] = dict(model=kind, class_effect=c, ci=[lo, hi], p=pv, n=int(len(g)),
                          mean_mono=float(g[g.poly == 0].ap.mean()), mean_poly=float(g[g.poly == 1].ap.mean()))

# ------------------------------------------------------------------ raw vs adjusted
rm = pd.read_csv(os.path.join(ST, "rq3_models.csv"))
raw = {}
for tech, view, o in (("BM25", "all", "ap"), ("BLAZE", "all", "ap"), ("FLIM", "parse", "ap"),
                      ("LocAgent", "all", "ap10"), ("SweRank", "all", "ap")):
    h = x[(x.tech == tech) & (x.view == view)]
    r = rm[(rm.condition == "primary") & (rm.tech == tech) & (rm.view == view) & (rm.outcome == o)].iloc[0]
    raw[tech] = dict(raw=float(h[h.poly == 1][o].mean() - h[h.poly == 0][o].mean()), adjusted=float(r.class_effect_poly))
OUT["raw_vs_adj"] = raw

# ------------------------------------------------------------------ test files in the ground truth
k = G[(G.tech == "BM25") & (G.view == "all") & (G.source == "kept")]
t = k.groupby(KEY + ["study_class"]).is_test.any().reset_index()
OUT["test_share"] = {f"{cls} {lab}": float(t[(t.study_class == cls) & t.project.isin(pr)].is_test.mean())
                     for cls in ("Mono-fix", "Poly-fix")
                     for lab, pr in (("all projects", t.project.unique()), ("Python projects", PY))}

# Python test files in the ground truth of the SweRank bugs (Python projects)
k = G[(G.tech == "SweRank") & (G.view == "all") & (G.source == "kept") & G.study_class.isin(["Mono-fix", "Poly-fix"])]
k = k.assign(pytest=k.is_test.astype(bool) & k.is_primary.astype(bool))
t = k.groupby(KEY + ["study_class"]).agg(any_=("pytest", "any"), share=("pytest", "mean")).reset_index()
OUT["python_test_files"] = {cls: dict(bugs_with_one=float(t[t.study_class == cls].any_.mean()),
                                      mean_share_of_gt=float(t[t.study_class == cls].share.mean()))
                            for cls in ("Mono-fix", "Poly-fix")}


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


with open(os.path.join(ST, "review_checks6.json"), "w") as f:
    json.dump(clean(OUT), f, indent=1)
print(json.dumps(clean(OUT), indent=1))
