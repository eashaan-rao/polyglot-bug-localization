"""
LocAgent adapter, step 2 (LocAgent venv): build LocAgent's own indexes for
every exported instance from our local clones, so LocAgent never clones
anything itself and sees exactly the pre-fix snapshot our other techniques see.

For each instance:
  * the full tree of <base_commit> materialised into a temporary directory via
    a temporary git index (read-tree + checkout-index). Not `git archive`: it
    honours `export-ignore` in .gitattributes, and airflow marks tests/,
    scripts/, dev/ ... export-ignore -- the first version of this adapter lost
    those files from LocAgent's indexes.
  * LocAgent's dependency_graph.build_graph.build_graph(repo_dir, global_import=True)
      -> $GRAPH_INDEX_DIR/<instance_id>.pkl
  * LocAgent's build_code_retriever_from_repo(repo_dir, persist_path=...)
      -> $BM25_INDEX_DIR/<instance_id>/
  * coverage record for RQ2: the files that are graph nodes and the files in
    the BM25 corpus -> <coverage_dir>/<instance_id>.json
Both builders are called unmodified (LocAgent commit 4935b55).

Run with the LocAgent venv, from anywhere:
    third_party/venv_locagent/bin/python Scripts/locagent/build_indexes.py \
        --instances data/obj2/locagent/instances/fold1/test.jsonl --workers 16
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from multiprocessing import Pool

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOCAGENT = os.path.join(ROOT, "third_party", "LocAgent")
INDEX = os.path.join(ROOT, "data", "obj2", "locagent", "index")
os.environ.setdefault("GRAPH_INDEX_DIR", os.path.join(INDEX, "graph_index"))
os.environ.setdefault("BM25_INDEX_DIR", os.path.join(INDEX, "BM25_index"))
COVERAGE = os.path.join(INDEX, "coverage")
TMP = os.path.join(ROOT, "data", "obj2", "locagent", "tmp")
REPOS = os.path.join(ROOT, "data", "repos", "python")
sys.path.insert(0, LOCAGENT)


def _one(inst):
    iid = inst["instance_id"]
    g_out = os.path.join(os.environ["GRAPH_INDEX_DIR"], f"{iid}.pkl")
    b_out = os.path.join(os.environ["BM25_INDEX_DIR"], iid)
    c_out = os.path.join(COVERAGE, f"{iid}.json")
    if os.path.exists(g_out) and os.path.exists(os.path.join(b_out, "corpus.jsonl")) and os.path.exists(c_out):
        return iid, "cached"
    import pickle
    from dependency_graph.build_graph import build_graph, NODE_TYPE_FILE
    from plugins.location_tools.retriever.bm25_retriever import build_code_retriever_from_repo
    clone = os.path.join(REPOS, inst["repo"].replace("/", "_"))
    work = tempfile.mkdtemp(dir=TMP, prefix=iid + "_")
    try:
        env = dict(os.environ, GIT_INDEX_FILE=os.path.join(work + ".index"))
        subprocess.run(["git", "-C", clone, "read-tree", inst["base_commit"]], env=env, check=True)
        subprocess.run(["git", "-C", clone, "--work-tree", work, "checkout-index", "-a", "-f"],
                       env=env, check=True)
        os.remove(env["GIT_INDEX_FILE"])
        G = build_graph(work, global_import=True)
        with open(g_out, "wb") as f:
            pickle.dump(G, f)
        build_code_retriever_from_repo(work, persist_path=b_out, similarity_top_k=10)
        graph_files = sorted(n for n, d in G.nodes(data=True) if d.get("type") == NODE_TYPE_FILE)
        bm25_files = set()
        with open(os.path.join(b_out, "corpus.jsonl")) as f:
            for line in f:
                rec = json.loads(line)
                fp = rec.get("file_path") or rec.get("metadata", {}).get("file_path")
                if fp:
                    bm25_files.add(fp)
        with open(c_out, "w") as f:
            json.dump({"instance_id": iid, "graph_files": graph_files, "bm25_files": sorted(bm25_files)}, f)
        return iid, "built"
    except Exception as e:
        return iid, f"ERROR {type(e).__name__}: {e}"
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instances", required=True)
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    for d in (os.environ["GRAPH_INDEX_DIR"], os.environ["BM25_INDEX_DIR"], COVERAGE, TMP):
        os.makedirs(d, exist_ok=True)
    insts = [json.loads(l) for l in open(a.instances)]
    n_err = 0
    with Pool(a.workers) as pool:
        for i, (iid, status) in enumerate(pool.imap_unordered(_one, insts), 1):
            if status.startswith("ERROR"):
                n_err += 1
                print(f"[{i}/{len(insts)}] {iid}: {status}", flush=True)
            elif i % 25 == 0 or i == len(insts):
                print(f"[{i}/{len(insts)}] ... ({n_err} errors)", flush=True)
    print(f"done: {len(insts)} instances, {n_err} errors -> {INDEX}")


if __name__ == "__main__":
    main()
