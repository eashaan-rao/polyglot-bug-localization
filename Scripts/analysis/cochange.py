"""
Co-change baseline (review item P1-8; change coupling, Zimmermann et al. 2004),
a diagnostic variant -- not a proposed technique. obj1 venv, CPU only.

For each test bug, only the history before its report is used:
  * commits on the clone's HEAD history, merges excluded, committed strictly
    before the report's creation time, the bug's own fix commit excluded;
    commits touching more than MAX_FILES files are skipped (bulk changes such
    as renames and formatting create spurious coupling);
  * n(a)    = number of such commits that changed file a,
    c(a, b) = number that changed both a and b;
    confidence(a -> b) = c(a, b) / n(a).
For a technique X, the top TOP_K files of its own ranking (the files it can
represent: FLIM-strict's parseable files, SweRank's scored files, LocAgent's
returned files) propose every co-changed file b with
    score(b) = sum over top files a at rank r of confidence(a -> b) / r.
Like the hybrid, the co-change list supplies only files X does not rank
itself; X's ranking and this list are merged by reciprocal rank fusion
(k = 60), as in hybrid_fusion.py. Files in neither list stay unscored.
(A first version that merged overlapping lists let files present in both
lists overtake X's best files, 2026-11-18; replaced.)

  CoChangeFLIM, CoChangeSweRank, CoChangeLocAgent  (score files, then
  Scripts/analysis/append_eval.py evaluates them)

    python Scripts/analysis/cochange.py
"""

import glob
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from Scripts import paths as P
from Scripts.bugs import load_all
from Scripts.universe import snapshot

SC = os.path.join(P.RESULT_PATH, "scores")
REPOS = os.path.join(P.DATA_DIR, "repos")
K, TOP_K, MAX_FILES = 60, 5, 30
SOURCES = {"CoChangeFLIM": "FLIM", "CoChangeSweRank": "SweRank", "CoChangeLocAgent": "LocAgent"}
LANG = dict(P.SELECTED_PROJECTS)


def history(repo):
    clone = os.path.join(REPOS, LANG[repo], repo.replace("/", "_"))
    out = subprocess.run(["git", "-C", clone, "log", "HEAD", "--no-merges", "--no-renames", "--name-only",
                          "--format=@@%H %ct"], capture_output=True, check=True).stdout.decode("utf-8", "replace")
    commits = []
    for block in out.split("@@")[1:]:
        lines = [l for l in block.splitlines() if l.strip()]
        sha, ts = lines[0].split()
        files = sorted(set(lines[1:]))
        if 0 < len(files) <= MAX_FILES:
            commits.append((int(ts), sha, files))
    commits.sort()
    return commits


def rrf(own_order, cc_order):
    s = defaultdict(float)
    for r, f in enumerate(own_order, 1):
        s[f] += 1.0 / (K + r)
    for r, f in enumerate(cc_order, 1):
        s[f] += 1.0 / (K + r)
    return s


def main():
    meta = load_all().set_index(["repo_name", "bug_id"])
    # queries: (cochange tech, fold, seed, repo) -> {bug: own ranking (list of paths)}
    queries = defaultdict(dict)
    for cc, src in SOURCES.items():
        for fp in sorted(glob.glob(os.path.join(SC, src, "fold*", "seed*", "*.parquet"))):
            m = re.search(r"/fold(\d+)/seed(\d+)/([^/]+)\.parquet$", fp)
            fold, seed, stub = int(m.group(1)), int(m.group(2)), m.group(3)
            repo = next(r for r in P.SELECTED_REPO_NAMES if r.replace("/", "_") == stub)
            t = pd.read_parquet(fp)
            t["bug_id"] = t.bug_id.astype(str)
            for bug, g in t.groupby("bug_id", sort=False):
                g = g[g.path != "__no_output__"].drop_duplicates("path")
                if src == "FLIM":
                    snap = snapshot(repo, meta.loc[(repo, bug), "pre_fix_commit_sha"])
                    ok = set(snap.loc[snap["parseable"].values, "path"])
                    g = g[g.path.isin(ok)]
                queries[(cc, fold, seed, repo)][bug] = g.sort_values("score", ascending=False).path.tolist()
    for repo in P.SELECTED_REPO_NAMES:
        keys = [k for k in queries if k[3] == repo]
        if not keys:
            continue
        commits = history(repo)
        bugs = sorted({b for k in keys for b in queries[k]},
                      key=lambda b: meta.loc[(repo, b), "creation_date"].timestamp())
        print(f"{repo}: {len(commits)} commits (<= {MAX_FILES} files), {len(bugs)} bugs", flush=True)
        n, co = Counter(), defaultdict(Counter)
        ci = 0
        out = defaultdict(list)
        for bug in bugs:
            t0 = meta.loc[(repo, bug), "creation_date"].timestamp()
            fix = meta.loc[(repo, bug), "fix_commit_sha"]
            while ci < len(commits) and commits[ci][0] < t0:
                ts, sha, files = commits[ci]
                ci += 1
                if sha == fix:
                    continue
                for a in files:
                    n[a] += 1
                    ca = co[a]
                    for b in files:
                        if b != a:
                            ca[b] += 1
            for k in keys:
                own = queries[k].get(bug)
                if own is None:
                    continue
                top = own[:TOP_K]
                score = defaultdict(float)
                for r, a in enumerate(top, 1):
                    if n[a]:
                        for b, c in co[a].items():
                            if b not in top:
                                score[b] += c / n[a] / r
                own_set = set(own)
                # like the hybrid: the co-change list supplies only files the technique does not rank
                # (merging overlapping lists would let files present in both overtake its best files)
                cc_order = [f for f in sorted(score, key=lambda f: -score[f]) if f not in own_set]
                s = rrf(own, cc_order)
                out[k] += [(bug, f, v) for f, v in s.items()] or [(bug, "__no_output__", 0.0)]
        for (cc, fold, seed, rp), rows in out.items():
            d = os.path.join(SC, cc, f"fold{fold}", f"seed{seed}")
            os.makedirs(d, exist_ok=True)
            pd.DataFrame(rows, columns=["bug_id", "path", "score"]).to_parquet(
                os.path.join(d, rp.replace("/", "_") + ".parquet"), index=False)
            print("wrote", cc, fold, seed, rp, flush=True)


if __name__ == "__main__":
    main()
