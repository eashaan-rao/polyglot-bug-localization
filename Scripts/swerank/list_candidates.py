"""
For the extended-corpus SweRank run (review item P1-7): write, per LocAgent/
SweRank instance, the candidate files of its pre-fix snapshot as the
evaluator defines them (text files in universe R), so the GPU job embeds
exactly the files that can be ranked. obj1 venv.

    python Scripts/swerank/list_candidates.py --fold 1
-> data/obj2/swerank/candidates/fold<F>/<instance_id>.json
"""

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from Scripts.universe import snapshot

INST = os.path.join(ROOT, "data", "obj2", "locagent", "instances", "fold{f}", "test.jsonl")
OUT = os.path.join(ROOT, "data", "obj2", "swerank", "candidates", "fold{f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fold", type=int, required=True)
    a = ap.parse_args()
    out = OUT.format(f=a.fold)
    os.makedirs(out, exist_ok=True)
    insts = [json.loads(l) for l in open(INST.format(f=a.fold))]
    for i, inst in enumerate(insts, 1):
        fp = os.path.join(out, inst["instance_id"] + ".json")
        if os.path.exists(fp):
            continue
        s = snapshot(inst["repo"], inst["base_commit"])
        s = s[s["is_text"] & s["in_ruleset"]]
        json.dump({"instance_id": inst["instance_id"], "paths": s["path"].tolist()}, open(fp, "w"))
        if i % 100 == 0:
            print(f"fold {a.fold}: {i}/{len(insts)}", flush=True)
    print(f"fold {a.fold}: done, {len(insts)} instances -> {out}")


if __name__ == "__main__":
    main()
