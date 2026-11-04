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
