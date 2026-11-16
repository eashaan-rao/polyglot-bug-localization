"""
SweRank run-to-run check (obj1 venv): compare the re-run of a random subset
of fold-1 bugs (data/obj2/swerank/rerun/fold1/, written by
`run_swerank.py rerank --fold 1 --rerun 20`) with the main run, using the
single evaluator (Scripts/evaluate.py) on both rankings.

Output: results/obj2/stats/swerank_rerun.csv (one row per bug) and a summary line.

    python Scripts/swerank/rerun_compare.py
"""

import glob
import gzip
import json
import os
import sys
import tempfile

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from Scripts import evaluate as E

DATA = os.path.join(ROOT, "data", "obj2", "swerank")


def jl(p):
    with gzip.open(p, "rt") as f:
        return json.load(f)


def file_order(ranked, ret):
    path = {h["docid"]: h["path"] for h in ret["top"]}
    files = list(dict.fromkeys(path[d] for d in ranked))
    return files + [f for f in ret["file_order"] if f not in set(files)]


def main():
    inst = {json.loads(l)["instance_id"]: json.loads(l)
            for l in open(os.path.join(ROOT, "data/obj2/locagent/instances/fold1/test.jsonl"))}
    rows, recs = [], []
    for fp in sorted(glob.glob(os.path.join(DATA, "rerun", "fold1", "*.json.gz"))):
        iid = os.path.basename(fp)[:-8]
        ret = jl(os.path.join(DATA, "retrieval", "fold1", iid + ".json.gz"))
        main_ = jl(os.path.join(DATA, "rerank", "fold1", iid + ".json.gz"))["ranked"]
        rep = jl(fp)["ranked"]
        fo_m, fo_r = file_order(main_, ret), file_order(rep, ret)
        recs.append(dict(instance_id=iid, project=inst[iid]["project"], bug_id=str(inst[iid]["bug_id"]),
                         same_functions=main_ == rep, same_files=fo_m == fo_r, same_top10=fo_m[:10] == fo_r[:10]))
        for run, fo in (("main", fo_m), ("rerun", fo_r)):
            n = len(fo)
            rows += [dict(run=run, project=inst[iid]["project"], bug_id=str(inst[iid]["bug_id"]), path=f,
                          score=float(n - i)) for i, f in enumerate(fo)]
    R = pd.DataFrame(recs)
    S = pd.DataFrame(rows)
    tmp = tempfile.mkdtemp()
    E.SCORES_DIR = tmp
    out = []
    for run in ("main", "rerun"):
        for proj, g in S[S.run == run].groupby("project"):
            p = E.score_path("SweRankRerun_" + run, 1, 0, proj)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            g[["bug_id", "path", "score"]].to_parquet(p, index=False)
            b, _ = E.evaluate_scores("SweRankRerun_" + run, 1, 0, proj)
            b = b[(b.view == "all") & (b.universe == "R") & (b.gt_filter == "all")]
            out.append(b[["bug_id", "ap", "ap10", "rr", "top10"]].assign(run=run, project=proj))
    M = pd.concat(out).pivot_table(index=["project", "bug_id"], columns="run", values=["ap", "ap10", "rr", "top10"])
    M.columns = [f"{a}_{b}" for a, b in M.columns]
    R = R.merge(M.reset_index(), on=["project", "bug_id"], how="left")
    for m in ("ap", "ap10", "rr", "top10"):
        R[f"abs_diff_{m}"] = (R[f"{m}_main"] - R[f"{m}_rerun"]).abs()
    R.to_csv(os.path.join(ROOT, "results", "obj2", "stats", "swerank_rerun.csv"), index=False)
    print(f"{len(R)} bugs: identical function order {R.same_functions.sum()}, identical file order "
          f"{R.same_files.sum()}, identical top-10 files {R.same_top10.sum()}; "
          f"|AP diff| max {R.abs_diff_ap.max():.4f} mean {R.abs_diff_ap.mean():.4f}; "
          f"Top-10 outcome identical {int((R.abs_diff_top10 == 0).sum())}; "
          f"MAP main {R.ap_main.mean():.4f} rerun {R.ap_rerun.mean():.4f}")


if __name__ == "__main__":
    main()
