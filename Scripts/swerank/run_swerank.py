"""
SweRank adapter (Reddy et al., "SweRank: Software Issue Localization with Code
Ranking", ICLR 2026; third_party/SweRank @ d3df508). Runs SweRank's own code on
our Python test bugs, then hands a file ranking to Scripts/evaluate.py like
every other technique.

Environment: third_party/venv_swerank, the authors' pinned versions
(requirements.txt: torch 2.6.0, vllm 0.8.5.post1, transformers 4.51.3,
sentence-transformers 3.4.1, beir 2.1.0; Python 3.11).

Bugs: the LocAgent instance files (data/obj2/locagent/instances/fold<F>/test.jsonl),
so SweRank and LocAgent see exactly the same Python test bugs (kept + removed),
the same pre-fix commits and the same report text.

Stage `retrieve`  (CPU workers + ~2 GB GPU)
  * pre-fix snapshot materialised with a temporary git index (read-tree +
    checkout-index), as for LocAgent -- not `git archive`, which drops
    export-ignore paths;
  * SweRank's own corpus builder, unmodified:
      get_repo_structure.create_structure(<snapshot>)
      get_patch_info.find_py_or_non_dict_with_path(structure)
    -> one document per function / method in .py files whose path does not
       contain "test" (the authors' filter), text = "<path>/<Class>/<func>\\n<code>";
  * SweRankEmbed-Small exactly as src/eval_beir_sbert_canonical.py with
    run_retriever.sh: BEIR SentenceBERT, bf16, max_seq_length 1024, query prefix
    "Represent this query for searching relevant code: ", dot product.
  Engineering (no effect on the ranking): a function text already embedded
  for an earlier bug of the same project is not embedded again (cache keyed
  by sha1 of the text); dot products in fp32 from the bf16 embeddings.
  -> data/obj2/swerank/retrieval/fold<F>/<instance_id>.json.gz

Stage `rerank`  (GPU, vLLM)
  * SweRankLLM-Small loaded through SweRank's load_reranker (code reranking,
    "github_issue" prompt), run_rerank.sh defaults: top 100, window 10, step 5,
    context 32768;
  * SweRank's own sequential path, one bug at a time (Reranker.rerank,
    batched=False, as rerank_llm.process_dataset). A faster loop that sends
    the windows of many bugs to vLLM together (rerank_many, kept for the
    record; `--verify N` compares it with the sequential path) did not give
    the same order (0/6 bugs identical, top-10 identical on 2/6, 2026-11-08),
    so it is not used. `--determinism N` re-runs N bugs at the end and checks
    the sequential output is reproducible.
  * vLLM's gpu_memory_utilization (hard-coded 0.9) is lowered to the free
    share of the shared L40 (SWERANK_GPU_UTIL, default 0.55); memory only.
  -> data/obj2/swerank/rerank/fold<F>/<instance_id>.json.gz

Stage `scores`
  File ranking = files in order of first appearance in
  [reranked top-100 functions] + [retriever order for all other functions];
  score = n - i. Files SweRank cannot see (tests, non-.py, .py files without
  a function) are unscored (-inf in the evaluator). Also writes the
  retriever-only ranking as technique SweRankEmbed.
  -> results/obj2/scores/{SweRank,SweRankEmbed}/fold<F>/seed0/<project>.parquet
  plus data/obj2/swerank/coverage/fold<F>.parquet (files in SweRank's corpus).

    PY=third_party/venv_swerank/bin/python
    $PY -u Scripts/swerank/run_swerank.py retrieve --fold 1
    $PY -u Scripts/swerank/run_swerank.py rerank --fold 1 [--verify 5]
    $PY -u Scripts/swerank/run_swerank.py scores --fold 1
"""

import argparse
import copy
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from multiprocessing import Pool

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SWERANK = os.path.join(ROOT, "third_party", "SweRank", "src")
REPOS = os.path.join(ROOT, "data", "repos", "python")
DATA = os.path.join(ROOT, "data", "obj2", "swerank")
TMP = os.path.join(DATA, "tmp")
INSTANCES = os.path.join(ROOT, "data", "obj2", "locagent", "instances", "fold{fold}", "test.jsonl")
SCORES = os.path.join(ROOT, "results", "obj2", "scores")
sys.path.insert(0, SWERANK)

EMBED_MODEL = "Salesforce/SweRankEmbed-Small"
EMBED_REV = "745d2a06103a66d3cfa600aa52fc0d3523010daa"
# its remote code (auto_map) comes from Snowflake/snowflake-arctic-embed-m-long; resolved 2026-11-08 to
EMBED_CODE_REV = "92d97331f1f4b6a366c1f161354b9f3390cc219f"
RERANK_MODEL = "Salesforce/SweRankLLM-Small"
EMBED_QUERY_PREFIX = "Represent this query for searching relevant code"   # eval_beir_sbert_canonical.py
TOP_K, WINDOW, STEP, CONTEXT = 100, 10, 5, 32768                            # run_rerank.sh / rerank.py


def _jdump(obj, path):
    tmp = path + ".part"
    with gzip.open(tmp, "wt") as f:
        json.dump(obj, f)
    os.replace(tmp, path)


def _jload(path):
    with gzip.open(path, "rt") as f:
        return json.load(f)


def load_instances(fold):
    return [json.loads(l) for l in open(INSTANCES.format(fold=fold))]


# ---------------------------------------------------------------- retrieve
def build_corpus(inst):
    """Pre-fix snapshot -> SweRank's function corpus {doc_id: text} and the
    repo-relative file of every document.

    SweRank's create_structure files the snapshot's top-level files under
    the root name, and a sub-directory with the same name as the root
    (localstack/, airflow/) lands in the same dict. So 'localstack/x.py/f'
    can be either the top-level x.py or localstack/x.py; resolved against
    the files that exist in the snapshot (the package path wins if both)."""
    from get_repo_structure.get_repo_structure import create_structure
    from get_repo_structure.get_patch_info import find_py_or_non_dict_with_path
    clone = os.path.join(REPOS, inst["repo"].replace("/", "_"))
    root = inst["repo"].split("/")[1]
    work = tempfile.mkdtemp(dir=TMP, prefix=inst["instance_id"] + "_")
    snap = os.path.join(work, root)                     # root name = repo name, as in SWE-bench playgrounds
    try:
        os.makedirs(snap)
        env = dict(os.environ, GIT_INDEX_FILE=work + ".index")
        subprocess.run(["git", "-C", clone, "read-tree", inst["base_commit"]], env=env, check=True)
        subprocess.run(["git", "-C", clone, "--work-tree", snap, "checkout-index", "-a", "-f"],
                       env=env, check=True)
        structure = create_structure(snap)
        corpus = find_py_or_non_dict_with_path(structure, cond=False)
        paths, unresolved = {}, 0
        for d in corpus:
            p = d.split(".py/")[0] + ".py"
            if os.path.isfile(os.path.join(snap, p)):
                paths[d] = p
            elif p.startswith(root + "/") and os.path.isfile(os.path.join(snap, p[len(root) + 1:])):
                paths[d] = p[len(root) + 1:]
            else:
                paths[d] = p
                unresolved += 1
        return inst["instance_id"], corpus, paths, unresolved
    finally:
        shutil.rmtree(work, ignore_errors=True)
        if os.path.exists(work + ".index"):
            os.remove(work + ".index")


def retrieve(a):
    import torch
    from beir.retrieval import models
    from sentence_transformers import SentenceTransformer
    out = os.path.join(DATA, "retrieval", f"fold{a.fold}")
    os.makedirs(out, exist_ok=True)
    os.makedirs(TMP, exist_ok=True)
    insts = [i for i in load_instances(a.fold)
             if not os.path.exists(os.path.join(out, i["instance_id"] + ".json.gz"))]
    insts.sort(key=lambda i: i["repo"])                  # one project's cache at a time
    if a.per_project:                                    # smoke test: first N bugs of each project
        from itertools import groupby
        insts = [x for _, g in groupby(insts, key=lambda i: i["repo"]) for x in list(g)[:a.per_project]]
    print(f"fold {a.fold}: {len(insts)} instances to retrieve", flush=True)
    if not insts:
        return
    enc = models.SentenceBERT()
    enc.q_model = SentenceTransformer(EMBED_MODEL, revision=EMBED_REV, trust_remote_code=True).to(torch.bfloat16)
    enc.doc_model = enc.q_model                          # the authors load the same checkpoint twice
    enc.q_model.max_seq_length = 1024
    by_id = {i["instance_id"]: i for i in insts}
    cache, cache_repo = {}, None
    t0 = time.time()
    with Pool(a.workers) as pool:
        for n, (iid, corpus, paths, unresolved) in enumerate(pool.imap(build_corpus, insts), 1):
            inst = by_id[iid]
            if inst["repo"] != cache_repo:
                cache, cache_repo = {}, inst["repo"]
            ids = list(corpus)
            keys = [hashlib.sha1(corpus[d].encode("utf-8", "surrogatepass")).hexdigest() for d in ids]
            new = list({k: d for k, d in zip(keys, ids) if k not in cache}.items())
            if new:
                docs = [{"title": "", "text": corpus[d]} for _, d in new]   # BEIR GenericDataLoader shape
                emb = enc.encode_corpus(docs, batch_size=128, show_progress_bar=False, convert_to_tensor=True)
                for (k, _), e in zip(new, emb.cpu()):
                    cache[k] = e
            q = f"{EMBED_QUERY_PREFIX}: {inst['problem_statement']}"
            qe = enc.encode_queries([q], batch_size=128, show_progress_bar=False, convert_to_tensor=True)
            D = torch.stack([cache[k] for k in keys]).float().cuda()
            s = (D @ qe.float().T.cuda()).squeeze(1).cpu()
            order = torch.argsort(s, descending=True, stable=True).tolist()
            files, seen = [], set()
            for j in order:
                f = paths[ids[j]]
                if f not in seen:
                    seen.add(f)
                    files.append(f)
            top = order[:TOP_K]
            _jdump({"instance_id": iid, "project": inst["project"], "bug_id": inst["bug_id"],
                    "n_functions": len(ids), "n_files": len(files), "n_new_embedded": len(new),
                    "n_unresolved_paths": unresolved,
                    "top": [{"docid": ids[j], "path": paths[ids[j]], "score": float(s[j]),
                             "content": corpus[ids[j]]} for j in top],
                    "top1000": [[ids[j], float(s[j])] for j in order[:1000]],
                    "file_order": files},
                   os.path.join(out, iid + ".json.gz"))
            if n % 10 == 0 or n == len(insts):
                el = time.time() - t0
                print(f"[{n}/{len(insts)}] {iid}: {len(ids)} functions ({len(new)} new), "
                      f"{len(files)} files; {el / n:.1f}s/bug, ~{el / n * (len(insts) - n) / 60:.0f} min left",
                      flush=True)


# ------------------------------------------------------------------ rerank
def load_agent():
    import torch
    from reranker.utils import rank_listwise_os_llm as R
    from reranker.utils.llm_util import load_reranker
    util = float(os.environ.get("SWERANK_GPU_UTIL", "0.55"))
    real_llm = R.LLM

    def llm(**kw):                                       # memory share only
        kw["gpu_memory_utilization"] = util
        kw.setdefault("seed", 0)
        return real_llm(**kw)

    R.LLM = llm
    rr = load_reranker(RERANK_MODEL, use_logits=0, use_alpha=0, window_size=WINDOW, batched=0,
                       context_size=CONTEXT, rerank_type="code", code_prompt_type="github_issue")
    return rr


def to_result(rec, query):
    from reranker.utils.result import Result
    hits = [{"qid": rec["instance_id"], "docid": h["docid"], "score": h["score"], "content": h["content"]}
            for h in rec["top"]]
    return Result(query=query, hits=sorted(hits, reverse=True, key=lambda x: x["score"])[:TOP_K])


def rerank_many(agent, results):
    """SweRank's sliding_windows + permutation_pipeline + run_llm, with the
    prompts of all bugs at one window position decoded in one vLLM call."""
    from vllm import SamplingParams
    results = [copy.deepcopy(r) for r in results]
    log = [[] for _ in results]
    groups = {}                                          # rank_end differs only if a bug has < 100 functions
    for i, r in enumerate(results):
        groups.setdefault(min(TOP_K, len(r.hits)), []).append(i)
    for rank_end, idx in groups.items():
        end_pos, start_pos = rank_end, rank_end - WINDOW
        while end_pos > 0 and start_pos + STEP != 0:
            start_pos = max(start_pos, 0)
            prompts = [agent.create_prompt(results[i], False, start_pos, end_pos) for i in idx]
            params = SamplingParams(temperature=0.,
                                    max_tokens=agent.get_total_output_tokens(False, end_pos - start_pos))
            outs = agent._llm.generate([p for p, _ in prompts], sampling_params=params, use_tqdm=False)
            for i, (p, ntok), o in zip(idx, prompts, outs):
                text = o.outputs[0].text.replace(agent._tokenizer.eos_token, "")
                results[i] = agent.receive_permutation(results[i], text, start_pos, end_pos, False)
                log[i].append([start_pos, end_pos, ntok, text])
            end_pos, start_pos = end_pos - STEP, start_pos - STEP
    return results, log


def rerank(a):
    src = os.path.join(DATA, a.src_name, f"fold{a.fold}")
    out = os.path.join(DATA, a.out_name, f"fold{a.fold}")
    os.makedirs(out, exist_ok=True)
    insts = {i["instance_id"]: i for i in load_instances(a.fold)}
    todo = [iid for iid in insts if os.path.exists(os.path.join(src, iid + ".json.gz"))
            and not os.path.exists(os.path.join(out, iid + ".json.gz"))]
    missing = [iid for iid in insts if not os.path.exists(os.path.join(src, iid + ".json.gz"))]
    print(f"fold {a.fold}: {len(todo)} to rerank, {len(missing)} without retrieval output", flush=True)
    if not todo and not a.verify and not a.rerun:
        return
    rr = load_agent()
    agent = rr._agent
    if a.verify:
        ids = sorted(i for i in insts if os.path.exists(os.path.join(src, i + ".json.gz")))[:a.verify]
        res = [to_result(_jload(os.path.join(src, i + ".json.gz")), insts[i]["problem_statement"]) for i in ids]
        ours, _ = rerank_many(agent, res)
        theirs, _ = rr.rerank(retrieved_results=res, use_logits=False, use_alpha=False, rank_start=0,
                           rank_end=TOP_K, window_size=WINDOW, step=STEP, logging=False, batched=False)
        same = [[h["docid"] for h in x.hits] == [h["docid"] for h in y.hits] for x, y in zip(ours, theirs)]
        top10 = [[h["docid"] for h in x.hits[:10]] == [h["docid"] for h in y.hits[:10]] for x, y in zip(ours, theirs)]
        print(f"VERIFY {len(ids)} bugs: identical full order {sum(same)}/{len(ids)}, "
              f"identical top-10 {sum(top10)}/{len(ids)}", flush=True)
        with open(os.path.join(DATA, f"verify_fold{a.fold}.json"), "w") as f:
            json.dump({"ids": ids, "identical_order": same, "identical_top10": top10}, f)
        if a.verify_only:
            return
    # Main run: SweRank's own sequential path, one bug at a time
    # (Reranker.rerank, batched=False), exactly as rerank_llm.process_dataset.
    # The cross-bug batching above (rerank_many) is NOT used: on 2026-11-08 it
    # matched the sequential order on 0/6 bugs (top-10 on 2/6), so it is not
    # the authors' method.
    def one(iid):
        rec = _jload(os.path.join(src, iid + ".json.gz"))
        agent._history = []
        ranked, _ = rr.rerank(retrieved_results=[to_result(rec, insts[iid]["problem_statement"])],
                              use_logits=False, use_alpha=False, rank_start=0, rank_end=TOP_K,
                              window_size=WINDOW, step=STEP, logging=False, batched=False)
        return [h["docid"] for h in ranked[0].hits], [h["response"] for h in agent._history]

    if a.rerun:
        # run-to-run check: re-rank a random sample of finished bugs (plus the
        # bug that differed in the end-of-run determinism check) into rerun/
        import random
        done_ids = sorted(i for i in insts if os.path.exists(os.path.join(out, i + ".json.gz")))
        ids = sorted(random.Random(2026).sample(done_ids, a.rerun))
        if a.fold == 1 and "ansible__ansible-77049" not in ids:
            ids.append("ansible__ansible-77049")
        rdir = os.path.join(DATA, "rerun", f"fold{a.fold}")
        os.makedirs(rdir, exist_ok=True)
        for iid in ids:
            ranked, responses = one(iid)
            _jdump({"instance_id": iid, "ranked": ranked, "responses": responses},
                   os.path.join(rdir, iid + ".json.gz"))
        same = sum(_jload(os.path.join(rdir, i + ".json.gz"))["ranked"] ==
                   _jload(os.path.join(out, i + ".json.gz"))["ranked"] for i in ids)
        print(f"RERUN {len(ids)} bugs: identical function order {same}/{len(ids)} -> {rdir}", flush=True)
        return
    t0 = time.time()
    for n, iid in enumerate(todo, 1):
        ranked, responses = one(iid)
        _jdump({"instance_id": iid, "ranked": ranked, "responses": responses},
               os.path.join(out, iid + ".json.gz"))
        if n % 10 == 0 or n == len(todo):
            el = time.time() - t0
            print(f"[{n}/{len(todo)}] {el / n:.1f}s/bug, ~{el / n * (len(todo) - n) / 60:.0f} min left",
                  flush=True)
    if a.determinism and todo:
        ids = todo[:a.determinism]
        same = [one(i)[0] == _jload(os.path.join(out, i + ".json.gz"))["ranked"] for i in ids]
        print(f"DETERMINISM {len(ids)} bugs re-run: identical order {sum(same)}/{len(ids)}", flush=True)
        with open(os.path.join(DATA, f"determinism_fold{a.fold}.json"), "w") as f:
            json.dump({"ids": ids, "identical_order": same}, f)


# ------------------------------------------------------------------ scores
def scores(a):
    import pandas as pd
    src = os.path.join(DATA, "retrieval", f"fold{a.fold}")
    rer = os.path.join(DATA, "rerank", f"fold{a.fold}")
    rows = {"SweRank": [], "SweRankEmbed": []}
    cov, missing = [], {"SweRank": 0, "SweRankEmbed": 0}
    for inst in load_instances(a.fold):
        iid, proj, bid = inst["instance_id"], inst["project"], inst["bug_id"]
        rp, kp = os.path.join(src, iid + ".json.gz"), os.path.join(rer, iid + ".json.gz")
        ret = _jload(rp) if os.path.exists(rp) else None
        orders = {"SweRankEmbed": ret["file_order"] if ret else []}
        if ret and os.path.exists(kp):
            path = {h["docid"]: h["path"] for h in ret["top"]}
            files, seen = [], set()
            for d in _jload(kp)["ranked"]:
                f = path[d]
                if f not in seen:
                    seen.add(f)
                    files.append(f)
            orders["SweRank"] = files + [f for f in ret["file_order"] if f not in seen]
        else:
            orders["SweRank"] = []
        for tech, files in orders.items():
            if not files:
                missing[tech] += 1
                rows[tech].append({"project": proj, "bug_id": bid, "path": "__no_output__", "score": 0.0})
            n = len(files)
            rows[tech] += [{"project": proj, "bug_id": bid, "path": f, "score": float(n - i)}
                           for i, f in enumerate(files)]
        if ret:
            cov += [{"project": proj, "bug_id": bid, "path": f} for f in ret["file_order"]]
    for tech, r in rows.items():
        df = pd.DataFrame(r)
        base = os.path.join(SCORES, tech, f"fold{a.fold}", "seed0")
        os.makedirs(base, exist_ok=True)
        for proj, g in df.groupby("project"):
            g[["bug_id", "path", "score"]].to_parquet(os.path.join(base, proj.replace("/", "_") + ".parquet"),
                                                      index=False)
        print(f"{tech} fold {a.fold}: {df.bug_id.nunique()} bugs, {missing[tech]} without output -> {base}")
    os.makedirs(os.path.join(DATA, "coverage"), exist_ok=True)
    pd.DataFrame(cov).to_parquet(os.path.join(DATA, "coverage", f"fold{a.fold}.parquet"), index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["retrieve", "rerank", "scores"])
    ap.add_argument("--fold", type=int, required=True)
    ap.add_argument("--workers", type=int, default=24)
    ap.add_argument("--chunk", type=int, default=64, help="bugs per vLLM batch (rerank)")
    ap.add_argument("--verify", type=int, default=0)
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--determinism", type=int, default=3, help="rerank: re-run the first N bugs and compare")
    ap.add_argument("--rerun", type=int, default=0, help="rerank: re-run N random finished bugs into rerun/")
    ap.add_argument("--src-name", default="retrieval", help="rerank: retrieval output folder under data/obj2/swerank")
    ap.add_argument("--out-name", default="rerank", help="rerank: output folder under data/obj2/swerank")
    ap.add_argument("--per-project", type=int, default=0, help="retrieve: only the first N bugs per project")
    a = ap.parse_args()
    {"retrieve": retrieve, "rerank": rerank, "scores": scores}[a.stage](a)


if __name__ == "__main__":
    main()
