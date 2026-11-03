"""
Step 3 — within-project runs: BM25, BLAZE, FLIM on the six projects.

Design (docs/JOURNAL_PLAN.md):
  * chronological split per project (Scripts/bugs.py: train / val / test,
    purged), fold 1 = newest 20 % test, fold 2 = rolling origin
  * every technique scores every file of universe T of each test bug's
    pre-fix snapshot (Scripts/universe.py); no retrieval stage
  * no technique computes metrics: Scripts/evaluate.py ranks the score files
    under universe R/T x view all/parse
  * seeds for the trained techniques; BM25 is deterministic (seed 0)

Outputs
  results/obj2/scores/<TECH>/fold<F>/seed<S>/<project>.parquet   (bug_id, path, score)
  results/obj2/scores/<TECH>/fold<F>/seed<S>/<project>.json      (manifest)
  results/obj2/logs/<TECH>_fold<F>_seed<S>_<project>.log
Resumable: a run whose score file exists is skipped.

Env
  OBJ2_TECHS     BM25,BLAZE,FLIM      (default; BLAZE_ALL = ablation trained on all
                 fix files, fold 1 / seed 13, after BLAZE)
  OBJ2_FOLDS     1 | 1,2              (default 1)
  OBJ2_SEEDS     13,42,2027           (default; BM25 always seed 0)
  OBJ2_PROJECTS  comma list of repo names (default all six)
  OBJ2_SMOKE=1   tiny run: <=40 train / 10 val / 8 test bugs, results under scores_smoke/

GPU techniques must run one at a time on the shared L40 (the October run
lost BLAZE airflow + localstack to OOM because BLAZE and FLIM ran together).

Run:   python Scripts/run_obj2_experiments.py && python Scripts/evaluate.py
"""

import json
import os
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Scripts import paths as P
from Scripts import evaluate as EV
from Scripts.bugs import chrono_split, load_all
from Scripts.repro import set_seed, wait_for_gpu, write_manifest

SMOKE = os.environ.get("OBJ2_SMOKE") == "1"
# Score the BeetleBox-removed bugs of the test window with the same trained
# model (they are never used for training). Scripts/removed_bugs.py first.
WITH_REMOVED = os.environ.get("OBJ2_WITH_REMOVED", "1") == "1"
# Category (c), bugs whose fix changes no Java/Python file: scored by these
# techniques only (parser-dependent ones reach none of their files by
# construction). Trained models are saved, so others can score them later.
NOPRIMARY_TECHS = set(os.environ.get("OBJ2_NOPRIMARY_TECHS", "BM25").split(",")) - {""}
TECHS = [t for t in os.environ.get("OBJ2_TECHS", "BM25,BLAZE,FLIM").split(",") if t]
FOLDS = [int(x) for x in os.environ.get("OBJ2_FOLDS", "1").split(",") if x]
SEEDS = [int(x) for x in os.environ.get("OBJ2_SEEDS", "13,42,2027").split(",") if x]
PROJECTS = [p for p in os.environ.get("OBJ2_PROJECTS", ",".join(P.SELECTED_REPO_NAMES)).split(",") if p]
LOG_DIR = os.path.join(P.RESULT_PATH, "logs_smoke" if SMOKE else "logs")
# The L40 is shared with other users: wait for this much free memory before a
# GPU run, and retry a run that dies of CUDA OOM (after waiting again).
# Measured peaks: BLAZE (CodeSage-small, full fine-tuning, batch 20, 1024-token
# reports) > 23 GiB -- OOM'd at 23.0 GiB on 2026-10-31; CodeSage does not
# support gradient checkpointing. FLIM (CodeBERT, batch 32) fits in ~8 GiB.
GPU_TECHS = {"BLAZE", "BLAZE_ALL", "FLIM"}
GPU_MIN_FREE_GIB = {"BLAZE": float(os.environ.get("OBJ2_GPU_MIN_FREE_GIB_BLAZE", "30")),
                    "BLAZE_ALL": float(os.environ.get("OBJ2_GPU_MIN_FREE_GIB_BLAZE", "30")),
                    "FLIM": float(os.environ.get("OBJ2_GPU_MIN_FREE_GIB_FLIM", "12"))}
OOM_RETRIES = int(os.environ.get("OBJ2_OOM_RETRIES", "3"))


def _module(tech):
    if tech == "BM25":
        import src.bm25 as m
    elif tech in ("BLAZE", "BLAZE_ALL"):
        import src.blaze.wp as m
    elif tech == "FLIM":
        import src.flim.pipeline as m
    else:
        raise ValueError(tech)
    return m


def _smoke(split):
    s = dict(split)
    s["train"], s["val"] = split["train"][-40:], split["val"][:10]
    s["test"], s["test_removed"] = split["test"][:6], split["test_removed"][:2]
    s["test_noprimary"] = split["test_noprimary"][:2]
    return s


def main():
    kept = load_all()            # kept + removed rows; techniques train on split["train"] only
    os.makedirs(LOG_DIR, exist_ok=True)
    jobs = [(f, repo, t, (0 if t == "BM25" else s))
            for f in FOLDS for repo in PROJECTS for t in TECHS
            for s in (SEEDS[:1] if t == "BM25" else SEEDS)]
    jobs = list(dict.fromkeys(jobs))
    print(f"{len(jobs)} runs  techs={TECHS} folds={FOLDS} seeds={SEEDS} smoke={SMOKE}", flush=True)

    for i, (fold, repo, tech, seed) in enumerate(jobs, 1):
        out = EV.score_path(tech, fold, seed, repo)
        if os.path.exists(out):
            print(f"[{i}/{len(jobs)}] {tech} fold{fold} seed{seed} {repo} — done, skip", flush=True)
            continue
        split = chrono_split(repo, fold)
        if SMOKE:
            split = _smoke(split)
        n_kept_test = len(split["test"])
        if WITH_REMOVED:
            split["test"] = split["test"] + split["test_removed"]
        if tech in NOPRIMARY_TECHS:
            split["test"] = split["test"] + split["test_noprimary"]
        logf = open(os.path.join(LOG_DIR, f"{tech}_fold{fold}_seed{seed}_{repo.replace('/', '_')}.log"), "a")

        def log(msg):
            print(msg, flush=True)
            logf.write(msg + "\n"); logf.flush()

        log(f"\n[{i}/{len(jobs)}] {tech} fold{fold} seed{seed} {repo}: "
            f"train={len(split['train'])} val={len(split['val'])} test={n_kept_test} "
            f"+ removed/no-primary {len(split['test']) - n_kept_test} "
            f"(purged train {split['purged_train']}, val {split['purged_val']})")
        t0 = time.time()
        res = None
        for attempt in range(1, OOM_RETRIES + 2):
            if tech in GPU_TECHS:
                wait_for_gpu(GPU_MIN_FREE_GIB[tech], log)
            set_seed(seed)
            os.environ["OBJ2_CURRENT_TECH"] = tech
            os.environ["BLAZE_TRAIN_ALL_FILES"] = "1" if tech == "BLAZE_ALL" else "0"
            try:
                if tech in GPU_TECHS:
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.reset_peak_memory_stats()
                m = _module(tech)
                res = m.run_wp(repo, split, kept, seed, log=log)
                break
            except Exception as e:
                traceback.print_exc(file=logf); traceback.print_exc()
                oom = "out of memory" in str(e).lower() or type(e).__name__ == "OutOfMemoryError"
                log(f"  ERROR (attempt {attempt}): {type(e).__name__}: {e}")
                if not (oom and tech in GPU_TECHS and attempt <= OOM_RETRIES):
                    break
                try:
                    import gc, torch
                    gc.collect()
                    torch.cuda.empty_cache()
                except Exception:
                    pass
                log("  CUDA OOM on the shared GPU -- waiting and retrying")
        if res is None:
            logf.close()
            continue
        scores, info = res if isinstance(res, tuple) else (res, {})
        gpu_peak_gib = None
        if tech in GPU_TECHS:
            try:
                import torch
                gpu_peak_gib = round(torch.cuda.max_memory_allocated() / 2**30, 2)
            except Exception:
                pass
        os.makedirs(os.path.dirname(out), exist_ok=True)
        scores.to_parquet(out + ".tmp", index=False)
        os.replace(out + ".tmp", out)
        wall = time.time() - t0
        write_manifest(out[:-8] + ".json", technique=tech, project=repo, fold=fold, seed=seed,
                       smoke=SMOKE, wall_time_sec=round(wall, 1), gpu_peak_allocated_gib=gpu_peak_gib,
                       split={k: (v if not isinstance(v, list) else len(v)) for k, v in split.items()},
                       test_bug_ids=split["test"], config=getattr(m, "CONFIG", {}), run_info=info)
        log(f"  done in {wall / 60:.1f} min" + (f", GPU peak {gpu_peak_gib} GiB" if gpu_peak_gib else "")
            + f" -> {out}")
        logf.close()

    print("\nnext: python Scripts/evaluate.py", flush=True)


if __name__ == "__main__":
    main()
