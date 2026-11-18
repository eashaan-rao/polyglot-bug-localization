"""
SweRank's retriever with its corpus extended to every candidate file (review
item P1-7: "what happens when the parser-dependent technique can see the
files it misses?"). venv_swerank.

Corpus per bug = SweRank's own function documents (unchanged, as in
run_swerank.py) + line-window chunks of every other candidate file
(data/obj2/swerank/candidates, i.e. text files of universe R that hold no
SweRank function: non-Python files, test files, Python files without a
function). A chunk is 50 lines, written in SweRank's document format
("<path>\\n<lines>"); at most 40 chunks per file (2,000 lines), so a few huge
recorded fixtures do not dominate the cost. Same SweRankEmbed-Small settings
(bf16, 1,024 tokens, query prefix, dot product). A file's score is the best
score of its documents; every candidate file is ranked.

    PY=third_party/venv_swerank/bin/python
    $PY -u Scripts/swerank/extend_corpus.py --fold 1
-> data/obj2/swerank/retrieval_all/fold<F>/<instance_id>.json.gz
   results/obj2/scores/SweRankEmbedAll/fold<F>/seed0/<project>.parquet  (--scores)
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_swerank as S  # noqa: E402

CAND = os.path.join(S.DATA, "candidates", "fold{f}")
OUT = os.path.join(S.DATA, "retrieval_all", "fold{f}")
OUT_TOP = os.path.join(S.DATA, "retrieval_all_top", "fold{f}")      # same run + top-100 documents for the reranker
RERANK_ALL = os.path.join(S.DATA, "rerank_all", "fold{f}")
LINES, MAX_CHUNKS = 50, 40
BATCH = int(os.environ.get("SWERANK_EMBED_BATCH", "32"))   # shared GPU; padding only, not the ranking


def build(inst_fold):
    inst, fold = inst_fold
    iid, corpus, paths, _ = S.build_corpus(inst)
    docs = {d: (paths[d], corpus[d]) for d in corpus}
    covered = set(paths.values())
    cand = json.load(open(os.path.join(CAND.format(f=fold), iid + ".json")))["paths"]
    clone = os.path.join(S.REPOS, inst["repo"].replace("/", "_"))
    todo = [p for p in cand if p not in covered]
    if todo:
        # read blobs straight from git (same snapshot as the evaluator)
        proc = subprocess.run(["git", "-C", clone, "ls-tree", "-r", "-z", inst["base_commit"]],
                              capture_output=True, check=True)
        sha = {}
        for rec in proc.stdout.decode("utf-8", "surrogateescape").split("\0"):
            if "\t" in rec:
                meta, path = rec.split("\t", 1)
                if meta.split()[1] == "blob":
                    sha[path] = meta.split()[2]
        want = [p for p in todo if p in sha]
        batch = subprocess.run(["git", "-C", clone, "cat-file", "--batch"], input=("\n".join(sha[p] for p in want) + "\n").encode(),
                               capture_output=True, check=True).stdout
        pos = 0
        for p in want:
            head_end = batch.index(b"\n", pos)
            size = int(batch[pos:head_end].split()[2])
            body = batch[head_end + 1: head_end + 1 + size]
            pos = head_end + 1 + size + 1
            lines = body.decode("utf-8", "replace").splitlines()
            for c in range(min(MAX_CHUNKS, max(1, (len(lines) + LINES - 1) // LINES))):
                docs[f"{p}#chunk{c}"] = (p, p + "\n" + "\n".join(lines[c * LINES:(c + 1) * LINES]))
    return iid, docs, len(cand), len(todo)


def retrieve(a):
    import torch
    from beir.retrieval import models
    from sentence_transformers import SentenceTransformer
    out = (OUT_TOP if a.with_top else OUT).format(f=a.fold)
    os.makedirs(out, exist_ok=True)
    os.makedirs(S.TMP, exist_ok=True)
    insts = [i for i in S.load_instances(a.fold) if not os.path.exists(os.path.join(out, i["instance_id"] + ".json.gz"))]
    insts.sort(key=lambda i: i["repo"])
    print(f"fold {a.fold}: {len(insts)} instances", flush=True)
    if not insts:
        return
    enc = models.SentenceBERT()
    enc.q_model = SentenceTransformer(S.EMBED_MODEL, revision=S.EMBED_REV, trust_remote_code=True).to(torch.bfloat16)
    enc.doc_model = enc.q_model
    enc.q_model.max_seq_length = 1024
    by = {i["instance_id"]: i for i in insts}
    cache, cache_repo, t0 = {}, None, time.time()
    with Pool(a.workers) as pool:
        for n, (iid, docs, n_cand, n_extra) in enumerate(pool.imap(build, [(i, a.fold) for i in insts]), 1):
            inst = by[iid]
            if inst["repo"] != cache_repo:
                cache, cache_repo = {}, inst["repo"]
            ids = list(docs)
            keys = [hashlib.sha1(docs[d][1].encode("utf-8", "surrogatepass")).hexdigest() for d in ids]
            new = list({k: d for k, d in zip(keys, ids) if k not in cache}.items())
            for s0 in range(0, len(new), 4096):
                part = new[s0:s0 + 4096]
                emb = enc.encode_corpus([{"title": "", "text": docs[d][1]} for _, d in part], batch_size=BATCH,
                                        show_progress_bar=False, convert_to_tensor=True).cpu()
                for (k, _), e in zip(part, emb):
                    cache[k] = e
            qe = enc.encode_queries([f"{S.EMBED_QUERY_PREFIX}: {inst['problem_statement']}"], batch_size=1,
                                    show_progress_bar=False, convert_to_tensor=True).float().cuda()
            sc = []
            for s0 in range(0, len(keys), 50000):
                D = torch.stack([cache[k] for k in keys[s0:s0 + 50000]]).float().cuda()
                sc.append((D @ qe.T).squeeze(1).cpu())
            sc = torch.cat(sc).tolist()
            best = {}
            for d, v in zip(ids, sc):
                p = docs[d][0]
                if v > best.get(p, -1e30):
                    best[p] = v
            order = sorted(best, key=lambda p: -best[p])
            rec = {"instance_id": iid, "project": inst["project"], "bug_id": inst["bug_id"],
                   "n_docs": len(ids), "n_candidates": n_cand, "n_extra_files": n_extra,
                   "file_order": order, "file_score": [best[p] for p in order]}
            if a.with_top:      # documents for SweRank's reranker, in run_swerank.py's format
                top = sorted(range(len(ids)), key=lambda j: -sc[j])[:S.TOP_K]
                rec["top"] = [{"docid": ids[j], "path": docs[ids[j]][0], "score": float(sc[j]),
                               "content": docs[ids[j]][1]} for j in top]
            S._jdump(rec, os.path.join(out, iid + ".json.gz"))
            if n % 10 == 0 or n == len(insts):
                el = time.time() - t0
                print(f"[{n}/{len(insts)}] {iid}: {len(ids)} docs ({len(new)} new), {n_extra} extra files; "
                      f"{el / n:.1f}s/bug, ~{el / n * (len(insts) - n) / 60:.0f} min left", flush=True)


def rerank_scores(a):
    """SweRankAll: files by first appearance in the reranked top-100 documents,
    then the extended retriever's order for every other file."""
    import pandas as pd
    src, rer = OUT_TOP.format(f=a.fold), RERANK_ALL.format(f=a.fold)
    rows, miss = [], 0
    for inst in S.load_instances(a.fold):
        rp, kp = os.path.join(src, inst["instance_id"] + ".json.gz"), os.path.join(rer, inst["instance_id"] + ".json.gz")
        if not (os.path.exists(rp) and os.path.exists(kp)):
            miss += 1
            rows.append({"project": inst["project"], "bug_id": inst["bug_id"], "path": "__no_output__", "score": 0.0})
            continue
        ret, rk = S._jload(rp), S._jload(kp)
        path = {h["docid"]: h["path"] for h in ret["top"]}
        files = list(dict.fromkeys(path[d] for d in rk["ranked"]))
        files += [f for f in ret["file_order"] if f not in set(files)]
        n = len(files)
        rows += [{"project": inst["project"], "bug_id": inst["bug_id"], "path": f, "score": float(n - i)}
                 for i, f in enumerate(files)]
    df = pd.DataFrame(rows)
    base = os.path.join(S.SCORES, "SweRankAll", f"fold{a.fold}", "seed0")
    os.makedirs(base, exist_ok=True)
    for proj, g in df.groupby("project"):
        g[["bug_id", "path", "score"]].to_parquet(os.path.join(base, proj.replace("/", "_") + ".parquet"), index=False)
    print(f"SweRankAll fold {a.fold}: {df.bug_id.nunique()} bugs, {miss} missing -> {base}")


def scores(a):
    import pandas as pd
    src = OUT.format(f=a.fold)
    rows, miss = [], 0
    for inst in S.load_instances(a.fold):
        fp = os.path.join(src, inst["instance_id"] + ".json.gz")
        if not os.path.exists(fp):
            miss += 1
            rows.append({"project": inst["project"], "bug_id": inst["bug_id"], "path": "__no_output__", "score": 0.0})
            continue
        r = S._jload(fp)
        n = len(r["file_order"])
        rows += [{"project": inst["project"], "bug_id": inst["bug_id"], "path": p, "score": float(n - i)}
                 for i, p in enumerate(r["file_order"])]
    df = pd.DataFrame(rows)
    base = os.path.join(S.SCORES, "SweRankEmbedAll", f"fold{a.fold}", "seed0")
    os.makedirs(base, exist_ok=True)
    for proj, g in df.groupby("project"):
        g[["bug_id", "path", "score"]].to_parquet(os.path.join(base, proj.replace("/", "_") + ".parquet"), index=False)
    print(f"SweRankEmbedAll fold {a.fold}: {df.bug_id.nunique()} bugs, {miss} missing -> {base}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fold", type=int, required=True)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--scores", action="store_true")
    ap.add_argument("--with-top", action="store_true", help="also store the top-100 documents (for reranking)")
    ap.add_argument("--rerank-scores", action="store_true")
    a = ap.parse_args()
    rerank_scores(a) if a.rerank_scores else scores(a) if a.scores else retrieve(a)
