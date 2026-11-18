"""
Hybrid baseline from stored score files (review item P1-8): a parser-dependent
technique ranks the files it can represent, BM25 ranks every other file, and
the two lists are merged by reciprocal rank fusion (RRF, k = 60;
Cormack et al. 2009): score = 1 / (60 + rank in its own list).

  HybridFLIM     FLIM's scores for parseable files (FLIM-strict's candidates),
                 BM25 for unparseable files; every FLIM seed
  HybridSweRank  SweRank's ranking for the files it scored, BM25 for the rest
  HybridLocAgent LocAgent's (<= 10) files, BM25 for the rest

The new techniques are evaluated with the single evaluator and appended to
results/obj2/eval/per_bug.parquet and per_gt.parquet (rows of these three
techniques are replaced; nothing else changes).

    python Scripts/analysis/hybrid_fusion.py
"""

import glob
import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from Scripts import evaluate as E
from Scripts import paths as P
from Scripts.bugs import load_all
from Scripts.universe import snapshot

SC = os.path.join(P.RESULT_PATH, "scores")
K = 60
SOURCES = {"HybridFLIM": "FLIM", "HybridSweRank": "SweRank", "HybridLocAgent": "LocAgent"}


def fuse(own: pd.Series, bm25: pd.Series) -> pd.DataFrame:
    own = own.sort_values(ascending=False)
    rest = bm25[~bm25.index.isin(own.index)].sort_values(ascending=False)
    s = pd.concat([pd.Series(1.0 / (K + np.arange(1, len(own) + 1)), index=own.index),
                   pd.Series(1.0 / (K + np.arange(1, len(rest) + 1)), index=rest.index)])
    return s.rename_axis("path").reset_index(name="score")


def build():
    meta = load_all().set_index(["repo_name", "bug_id"])
    written = []
    for hyb, src in SOURCES.items():
        for fp in sorted(glob.glob(os.path.join(SC, src, "fold*", "seed*", "*.parquet"))):
            m = re.search(r"/fold(\d+)/seed(\d+)/([^/]+)\.parquet$", fp)
            fold, seed, stub = int(m.group(1)), int(m.group(2)), m.group(3)
            repo = next(r for r in P.SELECTED_REPO_NAMES if r.replace("/", "_") == stub)
            bfp = os.path.join(SC, "BM25", f"fold{fold}", "seed0", stub + ".parquet")
            t, b = pd.read_parquet(fp), pd.read_parquet(bfp)
            t["bug_id"], b["bug_id"] = t.bug_id.astype(str), b.bug_id.astype(str)
            bg = dict(tuple(b.groupby("bug_id")))
            rows = []
            for bug, g in t.groupby("bug_id", sort=False):
                g = g[g.path != "__no_output__"]
                own = pd.Series(g.score.values, index=g.path.values)
                own = own[~own.index.duplicated()]
                if src == "FLIM":
                    snap = snapshot(repo, meta.loc[(repo, bug), "pre_fix_commit_sha"]).set_index("path")
                    keep = snap.index[snap["parseable"].values]
                    own = own[own.index.isin(keep)]
                bm = bg.get(bug)
                bm = pd.Series(bm.score.values, index=bm.path.values) if bm is not None else pd.Series(dtype=float)
                bm = bm[~bm.index.duplicated()]
                f = fuse(own, bm)
                f.insert(0, "bug_id", bug)
                rows.append(f)
            out = os.path.join(SC, hyb, f"fold{fold}", f"seed{seed}")
            os.makedirs(out, exist_ok=True)
            pd.concat(rows, ignore_index=True)[["bug_id", "path", "score"]].to_parquet(
                os.path.join(out, stub + ".parquet"), index=False)
            written.append((hyb, fold, seed, repo))
            print("wrote", hyb, fold, seed, repo, flush=True)
    return written


def evaluate(written):
    pb, pg = [], []
    for hyb, fold, seed, repo in written:
        b, g = E.evaluate_scores(hyb, fold, seed, repo)
        pb.append(b)
        pg.append(g)
        print("evaluated", hyb, fold, seed, repo, flush=True)
    nb, ng = pd.concat(pb, ignore_index=True), pd.concat(pg, ignore_index=True)
    for name, new in (("per_bug", nb), ("per_gt", ng)):
        fp = os.path.join(E.EVAL_DIR, name + ".parquet")
        old = pd.read_parquet(fp)
        old = old[~old.tech.isin(list(SOURCES))]
        pd.concat([old, new], ignore_index=True).to_parquet(fp, index=False)
    E.summarise(pd.read_parquet(os.path.join(E.EVAL_DIR, "per_bug.parquet"))).to_csv(
        os.path.join(E.EVAL_DIR, "summary.csv"), index=False)


if __name__ == "__main__":
    evaluate(build())
