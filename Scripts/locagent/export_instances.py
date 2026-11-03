"""
LocAgent adapter, step 1 (obj1 venv): export our test bugs as LocAgent
instances (SWE-bench-like JSONL), one file per fold.

LocAgent (Chen et al., ACL 2025; third_party/LocAgent @ 4935b55) indexes
Python only, so only the three Python projects are exported; the Java
projects are an RQ2 infeasibility result, not a run.

  instance_id        "<owner>__<name>-<bug_id>"   (SWE-bench convention)
  repo, base_commit  repository and pre-fix commit
  problem_statement  our bug report text (title, newline, body)
  patch              "" -- LocAgent only copies it into its output metadata;
                     left empty so no fix information is near the agent
plus our own keys (project, bug_id, fold, source) for the converter.

Output: data/obj2/locagent/instances/fold<F>/test.jsonl
    python Scripts/locagent/export_instances.py [--folds 1,2] [--smoke N]
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from Scripts import paths as P
from Scripts.bugs import chrono_split, load_all

OUT = os.path.join(P.OBJ2_DATA_DIR, "locagent", "instances")
PYTHON_PROJECTS = [r for r, l in P.SELECTED_PROJECTS if l == "python"]


def instance_id(repo, bug_id):
    owner, name = repo.split("/")
    return f"{owner}__{name}-{bug_id}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--folds", default="1")
    ap.add_argument("--projects", default=",".join(PYTHON_PROJECTS))
    ap.add_argument("--smoke", type=int, default=0, help="N kept + 1 removed bugs per project")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--subset", type=int, default=0,
                    help="random subset of N instances (variance repeats); 0 = all")
    ap.add_argument("--subset-seed", type=int, default=2026)
    a = ap.parse_args()
    k = load_all().set_index(["repo_name", "bug_id"])
    for fold in [int(x) for x in a.folds.split(",")]:
        rows = []
        for repo in a.projects.split(","):
            s = chrono_split(repo, fold)
            kept, rem = s["test"], s["test_removed"]
            if a.smoke:
                kept, rem = kept[:a.smoke], rem[:1]
            for bid in kept + rem:
                m = k.loc[(repo, bid)]
                rows.append({"instance_id": instance_id(repo, bid), "repo": repo,
                             "base_commit": m["pre_fix_commit_sha"],
                             "problem_statement": m["bug_report_text"], "patch": "",
                             "project": repo, "bug_id": bid, "fold": fold, "source": m["source"]})
        if a.subset and a.subset < len(rows):
            import random
            rows = sorted(random.Random(a.subset_seed).sample(rows, a.subset), key=lambda r: r["instance_id"])
        d = os.path.join(a.out, f"fold{fold}")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "test.jsonl"), "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        print(f"fold {fold}: {len(rows)} instances -> {d}/test.jsonl")


if __name__ == "__main__":
    main()
