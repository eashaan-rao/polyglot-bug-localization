"""
LocAgent adapter, step 4 (obj1 venv): convert LocAgent's merged output
(merged_loc_outputs_mrr.jsonl, one ranked `found_files` list per instance)
into our score files, so Scripts/evaluate.py treats LocAgent like every other
technique.

A listed file at position i (0-based) of n gets score n - i; every other file
is unscored (-inf in the evaluator). An instance with no output gets a single
placeholder row, so the bug is still evaluated (as a miss) instead of silently
dropped. LocAgent returns at most ten files, so only Top-k and RR@10 are
meaningful for it.

    python Scripts/locagent/to_scores.py --instances <dir>/test.jsonl \
        --outputs <out>/merged_loc_outputs_mrr.jsonl --fold 1 [--smoke]
"""

import argparse
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from Scripts import paths as P


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instances", required=True)
    ap.add_argument("--outputs", required=True)
    ap.add_argument("--fold", type=int, required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--tech", default="LocAgent",
                    help="LocAgentRep for the variance repeats (kept apart from the main run)")
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    inst = {json.loads(l)["instance_id"]: json.loads(l) for l in open(a.instances)}
    found = {}
    if os.path.exists(a.outputs):
        for l in open(a.outputs):
            r = json.loads(l)
            ff = r.get("found_files") or []
            if ff and isinstance(ff[0], list):          # unmerged: first sample
                ff = ff[0]
            found[r["instance_id"]] = [f for f in ff if isinstance(f, str)]
    rows, missing = [], 0
    for iid, m in inst.items():
        ff = list(dict.fromkeys(found.get(iid, [])))
        if not ff:
            missing += 1
            rows.append({"project": m["project"], "bug_id": m["bug_id"], "path": "__no_output__", "score": 0.0})
        for i, p in enumerate(ff):
            rows.append({"project": m["project"], "bug_id": m["bug_id"], "path": p, "score": float(len(ff) - i)})
    df = pd.DataFrame(rows)
    base = os.path.join(P.RESULT_PATH, "scores_smoke" if a.smoke else "scores", a.tech,
                        f"fold{a.fold}", f"seed{a.seed}")
    os.makedirs(base, exist_ok=True)
    for proj, g in df.groupby("project"):
        g[["bug_id", "path", "score"]].to_parquet(os.path.join(base, proj.replace("/", "_") + ".parquet"), index=False)
    print(f"{len(inst)} instances, {len(inst) - missing} with output, {missing} empty -> {base}")


if __name__ == "__main__":
    main()
