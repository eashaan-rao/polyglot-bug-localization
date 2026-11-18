# Provenance of results produced before the full-run commit

Every run writes a manifest next to its score file with `git_head`, package
versions, configuration, split sizes, epochs and wall time. Runs made before
the full-run code was committed (2026-11-03) record `git_head = db2103b` (the
September commit) although they were produced by the uncommitted working tree.
This file states which code produced them and why they stay valid.

| Run (fold 1) | Produced | Code differences vs the committed full-run code | Status |
|---|---|---|---|
| localstack BM25 (seed 0) | 2026-11-03 | identical (rerun with the identifier-keeping tokenizer, D17) | valid |
| localstack FLIM (seed 13) | 2026-10-31 (pilot v2) | none affecting scores; model saving added later, so **no saved model** | valid; model not stored |
| localstack BLAZE (seed 13) | 2026-10-31 – 11-01 (pilot v2) | none affecting scores; **no saved model** | valid; model not stored |
| localstack LocAgent (seed 0) | 2026-10-31 – 11-01 (pilot v3, watchdog) | identical | valid |
| elasticsearch BM25 (seed 0) | 2026-11-03 | identical (rerun, D17) | valid |
| elasticsearch FLIM, BLAZE, BLAZE_ALL (seed 13) | 2026-11-01 – 11-03 (Java stage J1) | only the per-run GPU-memory log line was added later | valid; models stored |

Changes made after the localstack pilot and checked not to affect FLIM/BLAZE
scores: model saving (`Scripts/models.py`), the BLAZE_ALL switch (off for
BLAZE), category (c) bugs added to the loaded bug table (scored by BM25 only),
the Poly-fix split and test flags (evaluation only), GPU waiting and OOM
retries (driver only).

Superseded and archived (not used in the paper): `results/obj2/scores_archive/`
— the 2026-10-30 pilot (old learning-rate rule), BM25 before category (c),
BM25 with the split-only tokenizer. The October 2026 numbers in
`results/obj2/wp_cp_summary.csv` come from the pre-audit pipeline (wrong-repo
reports, broken FLIM) and must not be used.

Saved models reproduce stored scores (verified 2026-11-03 with
`Scripts/rescore.py --verify`): FLIM rank correlation 0.99997, BLAZE 0.99998,
BLAZE_ALL 0.99998 (differences from float16 batching only).

## Audit after step 3 of the full run (2026-11-04)

- No code change since the launch commit 37b8853 (later commits b3fa907,
  0e24325 touch docs and paper only), so the three git heads recorded by
  full-run manifests denote identical code.
- All 30 score files of steps 1–3 (BM25 folds 1–2; FLIM, BLAZE, BLAZE_ALL
  fold 1 seed 13): every manifest test bug scored, no non-finite, duplicate or
  per-bug constant scores, file counts equal universe T on sampled bugs.
- BLAZE_ALL reused BLAZE's selected LR in all six projects and trained on
  11–33 % more chunks (secondary-language fix files included).
- localstack pilot FLIM/BLAZE configs are identical to the full-run configs.
- Gaps: (1) localstack fold-1 seed-13 FLIM and BLAZE models are not stored
  (see table above) — only matters if a stratum is added later; (2) LocAgent
  score files have no JSON manifest (provenance in
  `results/obj2/locagent/<run>/args.json`); (3) `tree_sitter` version is
  recorded as `?` (pinned 0.25.2 in requirements.txt).
- LocAgent fold-1 (ansible, airflow) hung at start (both workers, 22:22) and
  was restarted by the watchdog at 22:53. The restart budget of that running
  step is 2; `run_locagent.sh` now defaults to 20 for later steps (6, 8).
  **Before the final evaluation**, check each LocAgent run's
  "instances with output" line: instances never attempted must be resumed
  (re-run `run_locagent.sh` on the same folders -- it skips finished ones --
  then `to_scores.py`), not scored as misses.
- **2026-11-05: step 4 (LocAgent fold 1, ansible + airflow) failed** with
  5/424 instances. Cause: a LocAgent bug -- `auto_search_main.py` passes each
  tool output to `eval()` and fell back to the raw text only on
  `SyntaxError`; outputs starting with a path (`lib/ansible/...`) raise
  `NameError`, the worker dies, and the parent blocks on
  `result_queue.get()` forever (no LocAgent timeout fires). The same instances
  re-hung on every restart. Fix: `Scripts/locagent/locagent_obj2.patch`
  (fallback on any exception; 60 s wait for a dead worker's result, then
  retry), applied and checked by `run_locagent.sh`. Behaviour on every output
  that did not crash is unchanged, so the localstack pilot (unpatched; its one
  hang was resolved by a restart with a fresh sample) stays valid. The 419
  placeholder rows were archived (`scores_archive/locagent_fold1_rest_incomplete_2026-11-05/`);
  `Scripts/run_followup.sh` (tmux `obj2_followup`) resumes the run after
  `run_full.sh` ends and re-runs evaluation + statistics. Steps 6 and 8 use the
  patched LocAgent.

## Localstack fold-1 seed-13 models (2026-11-08)

Decision: the pilot scores (2026-10-31) stay the reported results; the two
missing models are produced by retraining FLIM and BLAZE once with the pilot's
recorded LR and seed 13 (`Scripts/retrain_pilot_models.sh`, tmux
`obj2_retrain`, starts after the follow-up). The pilot score files are backed
up to `results/obj2/scores_archive/localstack_pilot_backup_2026-11-08/`, moved
aside while the driver trains, and restored byte-identical; the retrain's own
scores go to `results/obj2/scores_archive/localstack_model_retrain_2026-11-08/`
and are never evaluated. GPU training is not bit-reproducible, so the saved
models approximate the pilot runs; their agreement with the pilot scores is
recorded below once the retrain finishes.

Pilot validity re-checked 2026-11-08: same config, LR grid, library versions and
test bugs as the full run; the manifest's `git_head` (db2103b) predates the
Objective 2 commits and does not identify the code, so code changes after the
pilot were checked by file modification time: the 2026-11-01 changes are those
listed above as not affecting scores, and the 2026-11-03 change to
`src/flim/ir_features.py` is a docstring only. Pilot MAP lies inside the range
of seeds 42/2027 (FLIM .395 vs .398/.368; BLAZE .294 vs .288/.268).

Retrain result (2026-11-08 16:08): both models saved
(`data/obj2/models/{FLIM,BLAZE}/fold1/seed13/localstack_localstack`); pilot
score files restored byte-identical. Agreement of the retrained models' test
scores with the pilot scores (92 bugs, 184 799 file scores each): BLAZE
per-bug Spearman 1.000, MAP 0.2937 vs 0.2937 (identical); FLIM per-bug Spearman
mean 0.971 (min 0.892), MAP 0.3964 vs 0.3953 (+0.001; FLIM's learning-to-rank
stage is not bit-reproducible). Every FLIM/BLAZE/BLAZE_ALL score file now has a
stored model.

## SweRank added as a sixth technique (2026-11-08)

Decision (with the first author, 2026-11-08): add SweRank (Reddy et al., ICLR
2026; `third_party/SweRank` @ d3df508) on the three Python projects; drop
Agentless (it sees the same `.py` files as LocAgent and its paper model,
GPT-4o, cannot be run locally). SweRank+ (SweRankMulti + SweRankAgent,
arXiv 2512.20482, Dec 2025) is not released: no code in the GitHub repo and
no models on the Salesforce Hugging Face page (checked 2026-11-08). An
unofficial reranker checkpoint `jaehyeokdoo2/SweRankLLMMulti(-7B)` (Sep 2025,
a co-author's personal account, blank model card, no license, no matching
retriever) is not used.

Setup: models `Salesforce/SweRankEmbed-Small` @ 745d2a06103a and
`Salesforce/SweRankLLM-Small` @ 5f124b0dd0bb; environment
`third_party/venv_swerank` with the authors' pinned versions (Python 3.11,
torch 2.6.0, vllm 0.8.5.post1, transformers 4.51.3, sentence-transformers
3.4.1, beir 2.1.0). Adapter `Scripts/swerank/run_swerank.py`; it uses the
LocAgent instance files, so both LLM-based techniques see the same bugs,
commits and report text. SweRank's corpus builder, retriever settings
(run_retriever.sh) and reranker settings (run_rerank.sh: top 100, window 10,
step 5) are used unmodified. Engineering changes that do not change the
ranking: an embedding cache across bugs of one project; vLLM memory share
lowered for the shared GPU (0.55). Reranking uses SweRank's own sequential
path (`Reranker.rerank`, one bug at a time). A faster loop that sent the
windows of many bugs to vLLM together was tried and rejected: on 6 fold-1
bugs it matched the sequential order on 0/6 (top-10 on 2/6), most likely
because vLLM's bf16 numerics depend on batch composition and greedy decoding
amplifies near-ties over 19 windows per bug. The main run re-runs 3 bugs per
fold at the end to check the sequential output is reproducible
(`data/obj2/swerank/determinism_fold<F>.json`). Retriever remote code:
Snowflake/snowflake-arctic-embed-m-long @ 92d97331f1f4. `pyarrow` (unpinned by
the authors) set to 20.0.0, `setuptools` 76.0.0 as pinned.
Path detail: SweRank's structure builder files top-level files under the
repo name, which collides with same-named package directories (localstack/,
airflow/); document paths are resolved against the snapshot.

SweRank run result (2026-11-08 21:04 -> 2026-11-09 05:55): fold 1 516 bugs,
fold 2 531 bugs, no errors, no empty outputs; 30 s/bug (sequential path).
Score files `results/obj2/scores/{SweRank,SweRankEmbed}/fold{1,2}/seed0/`.
Evaluation and statistics re-run 2026-11-09 06:22 (`Scripts/swerank/after_swerank.sh`;
previous eval/stats backed up to
`results/obj2/scores_archive/eval_stats_before_swerank_2026-11-09/`); all 680
earlier RQ3 model rows reproduced exactly. Reranker replies: 4.5% of windows
(first 26 bugs) repeat an identifier; SweRank's own parser drops repeats and
appends missing items in retriever order.
Run-to-run variation: the end-of-run check in the same process reproduced the
function order for 5/6 bugs; a re-run in a new process (2026-11-09,
`--rerun 20`, 21 bugs incl. ansible-77049) reproduced it for 1/21 (file order
5/21, top-10 files 9/21) -- greedy vLLM decoding is not bit-identical across
processes -- but per-bug AP changed by 0.002 on average (max 0.042), the Top-10
outcome was identical for 21/21 and MAP was 0.569 vs 0.567
(`Scripts/swerank/rerun_compare.py`, `results/obj2/stats/swerank_rerun.csv`).
Training-data overlap: SweLoc excludes SWE-bench and LocBench repositories;
ansible is in LocBench (1 of 560 instances), airflow and localstack are not, and
SweLoc is not released.

## Diagnostic variants: reach or understanding (2026-11-16 to 2026-11-18)

Requested by the internal review (P1): what do the parser-dependent techniques
do with the files they cannot represent? Not proposed as techniques; untuned.
- Hybrids (`Scripts/analysis/hybrid_fusion.py`): the technique's ranking for
  the files it represents, BM25 for the rest, reciprocal rank fusion, k = 60.
  HybridFLIM (every FLIM seed), HybridSweRank, HybridLocAgent. Evaluated with
  `Scripts/analysis/append_eval.py`-style appending (only these rows replaced).
- SweRank on all text files (`Scripts/swerank/extend_corpus.py`): SweRank's
  own function documents + 50-line chunks of every other candidate file
  (universe R text files, `list_candidates.py`), at most 40 chunks per file.
  Retriever only (SweRankEmbedAll) and with SweRank's reranker on the top 100
  documents (SweRankAll; sequential path, same settings as the main run).
  Embedding batch 8-16 on the shared GPU (padding only).
- Reranker run: first attempt (2026-11-17 00:15) failed at vLLM start-up
  because vLLM 0.8.5 counts other processes' GPU memory against
  gpu_memory_utilization; the placeholder scores it left were removed from the
  evaluation (6,282 per-bug rows). Restart with share = (others + 20 GiB)/total;
  fold 1 done, fold 2 restarted once by the watchdog after the GPU was full for
  ~1.5 h; finished 2026-11-17 23:21 (1,047 bugs).
- Contamination probe extended to all Python test bugs (LocAgent model,
  closed-book, issue title only): hit@10 Mono-fix 7.1% / 6.6%, Poly-fix
  3.3% / 0.8% (folds 1 / 2); `results/obj2/locagent/contamination_probe_all_fold*.csv`.
- Co-change baseline (`Scripts/analysis/cochange.py`, 2026-11-18): history before
  each report (no merges, no fix commit, commits <= 30 files); the technique's
  top five files propose co-changed files that it does not rank itself; merged
  by RRF (k = 60). A first version merged overlapping lists, which let files in
  both lists overtake the technique's best files (SweRank MAP .478 -> .065);
  its outputs were deleted before any use and the run repeated with disjoint
  lists.
