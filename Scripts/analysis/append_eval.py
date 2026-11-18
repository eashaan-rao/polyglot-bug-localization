"""
Evaluate only the named techniques' score files and replace their rows in
results/obj2/eval/per_bug.parquet / per_gt.parquet (other techniques untouched).

    python Scripts/analysis/append_eval.py SweRankEmbedAll [TECH ...]
"""
import glob
import os
import re
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from Scripts import evaluate as E
from Scripts import paths as P

techs = sys.argv[1:]
pb, pg = [], []
for t in techs:
    for fp in sorted(glob.glob(os.path.join(E.SCORES_DIR, t, "fold*", "seed*", "*.parquet"))):
        m = re.search(r"/fold(\d+)/seed(\d+)/([^/]+)\.parquet$", fp)
        repo = next(r for r in P.SELECTED_REPO_NAMES if r.replace("/", "_") == m.group(3))
        b, g = E.evaluate_scores(t, int(m.group(1)), int(m.group(2)), repo)
        pb.append(b); pg.append(g)
        print("evaluated", t, m.group(1), m.group(2), repo, flush=True)
for name, new in (("per_bug", pd.concat(pb, ignore_index=True)), ("per_gt", pd.concat(pg, ignore_index=True))):
    fp = os.path.join(E.EVAL_DIR, name + ".parquet")
    old = pd.read_parquet(fp)
    pd.concat([old[~old.tech.isin(techs)], new], ignore_index=True).to_parquet(fp, index=False)
E.summarise(pd.read_parquet(os.path.join(E.EVAL_DIR, "per_bug.parquet"))).to_csv(os.path.join(E.EVAL_DIR, "summary.csv"), index=False)
print("done:", techs)
