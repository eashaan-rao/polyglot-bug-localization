"""
Closed-book contamination probe for the LocAgent model (obj1 venv).

The test bugs (2020-2024) predate the model's training cut-off, so the model
may have seen the fixes. The probe gives the served model ONLY the repository
name and the issue title -- no repository access, no tools -- and asks which
files were changed. If it names ground-truth files at a high rate, the agent
results are an upper bound and are reported as such.

  hit@10        a ground-truth file (exact pre-fix path) is among the <= 10 named paths
  gt_recall@10  share of the bug's ground-truth files named

Greedy decoding (temperature 0). Requires the vLLM server of
run_locagent.sh to be up.

    python Scripts/locagent/contamination_probe.py --instances <dir>/test.jsonl \
        --out <out>/contamination_probe.csv [--port 8011]
"""

import argparse
import json
import os
import re
import sys
import urllib.request

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from Scripts.bugs import eval_ground_truth, load_all

PROMPT = ("The following is the title of a GitHub issue in the repository {repo}.\n"
          "You do not have access to the repository. From memory only, list the file paths "
          "(relative to the repository root) that were most likely modified to fix this issue. "
          "Answer with at most 10 paths, one per line, and nothing else.\n\nIssue title: {title}")


def ask(port, model, text):
    body = json.dumps({"model": model, "temperature": 0.0, "max_tokens": 400,
                       "messages": [{"role": "user", "content": text}]}).encode()
    req = urllib.request.Request(f"http://localhost:{port}/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instances", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--port", default=os.environ.get("LOCAGENT_PORT", "8011"))
    ap.add_argument("--model", default="ft-qwen-7B-128k")
    a = ap.parse_args()
    k = load_all().set_index(["repo_name", "bug_id"])
    rows = []
    for line in open(a.instances):
        inst = json.loads(line)
        repo, bid = inst["project"], inst["bug_id"]
        title = inst["problem_statement"].strip().split("\n", 1)[0]
        ans = ask(a.port, a.model, PROMPT.format(repo=repo, title=title))
        named = [re.sub(r"^[\s\-*`\d.)]+|[`\s]+$", "", x) for x in ans.splitlines()]
        named = [x for x in named if "/" in x or x.endswith(".py")][:10]
        gt = {g["pre_path"] or g["path"] for g in eval_ground_truth(repo, bid)}
        hits = gt & set(named)
        rows.append({"project": repo, "bug_id": bid, "source": inst["source"],
                     "study_class": k.loc[(repo, bid), "study_class"], "n_named": len(named),
                     "n_gt": len(gt), "hit10": int(bool(hits)),
                     "gt_recall10": len(hits) / max(len(gt), 1), "named": json.dumps(named)})
    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    df.to_csv(a.out, index=False)
    print(df.groupby(["source", "study_class"])[["hit10", "gt_recall10"]].mean().round(3))


if __name__ == "__main__":
    main()
