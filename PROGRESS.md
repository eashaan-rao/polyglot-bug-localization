# Objective 2 — progress

RULESET_VERSION **`0.2.0` — FROZEN 2026-09-06** (bump to 0.2.1 only if the 50-bug
two-person check finds a rule error; re-running `classify_bugs.py` +
`prevalence_report.py` then takes seconds).

## Decisions locked with the advisor (2026-09-06)

| Decision | Choice |
|---|---|
| Headline Poly-fix number | **broad / operational grain — 27.4 %** (985 bugs); headline 21.0 % and strict 8.2 % also reported. Range [8.2 % – 41.9 %]. |
| Retrieval component | **Removed.** No FAISS/BGE top-K stage. Every technique (BM25, BLAZE, FLIM) ranks the **whole pre-fix snapshot**. Retrieval recall is 100 % by construction; "retrieval bounds the reranker" no longer applies. `retrieval_recall_by_class.py` output is kept only as a supplementary "why we don't use a retrieval stage" figure. |
| GPU scope | **WP arm only** — BM25 + BLAZE + FLIM × the 6 projects. No cross-project arm (COOBA dropped for now). |
| Ruleset freeze | **0.2.0 frozen now**; 50-bug two-person agreement check runs in parallel. |
| Techniques | **BM25** (classical, CPU) + **BLAZE** (fine-tuned language-agnostic, GPU) + **FLIM** (parsing, GPU), all full-snapshot. |

Compute note: full-snapshot ranking is heavier than a top-K reranker. Per-snapshot
caching (`blob_cache` in BLAZE, `_FUNC_EMB_CACHE` added to `src/flim/pipeline.py`)
means only the first bug of each project pays the full encode; elasticsearch
(~27 k files/snapshot) is the long pole. `bm25s` (not `rank_bm25`) is used for a
tractable classical baseline.

## Done and run

| Phase | Script | Output | Status |
|---|---|---|---|
| A scaffold | — | self-contained tree, own git repo, 6 projects copied | ✅ |
| 0 extract | `Scripts/extract_fix_commits.py` | `data/obj2/fix_files_raw.parquet`, `fix_files_long.csv` | ✅ 100% commit recovery, 4995 bugs, 96 extensions |
| 0 rules | `Scripts/classification_rules.py` | — | ✅ C1–C4 secondary admission, 3 grains, `keep_bug` |
| 0 classify | `Scripts/classify_bugs.py` | `data/obj2/bug_classification.parquet`, `results/obj2/bug_classification.csv` | ✅ 3594/4995 kept; Mono 2561 / Poly 1033 / Other 0 |
| 1 prevalence | `Scripts/prevalence_report.py` | `results/obj2/prevalence/*` | ✅ headline 21.0 %, broad 27.4 %, strict 8.2 % |
| 1 sensitivity | `Scripts/boundary_sensitivity.py` | `results/obj2/boundary_sensitivity.csv` | ✅ range [8.2 % – 41.9 %] |
| 2 feasibility | `Scripts/feasibility_matrix.py` | `results/obj2/feasibility_matrix.csv` | ✅ BM25/BLAZE succeed on all; FLIM `degraded_wholefile`; COOBA `trivial_graph` |
| 3 retrieval recall | `Scripts/retrieval_recall_by_class.py` | `results/obj2/retrieval_recall_by_*.csv`, `retrieval_recall.md` | ✅ **see finding below** |

## Code-complete, pending GPU run

| Phase | Script | Needs |
|---|---|---|
| 3 experiments | `Scripts/run_obj2_experiments.py` | **WP only, full-snapshot.** BM25 (CPU, `bm25s`) — running. BLAZE + FLIM — GPU, ~1–1.5 days, resumable. `OBJ2_SMOKE=1` for a 1-project check; `OBJ2_MODELS=BM25` to select. First FLIM run downloads `microsoft/codebert-base`. |
| 3 analysis | `Scripts/analysis/obj2_wp_analysis.py` | runs once `results/obj2/diagnostics/*.csv` exist |
| 4 analysis | `Scripts/analysis/obj2_classical_vs_parsing.py` | same (parsing technique = FLIM; CP/COOBA references are dormant) |

## Done since (analysis + artifacts)

- `analysis/obj2_tables.py` — Tables 1–4 (Markdown + CSV), run on BM25 data.
- `analysis/obj2_figures.py` — 4 PNGs (`results/obj2/figures/`), run.
- `analysis/obj2_failure_analysis.py` — failure-set composition + chi-sq, truncation
  check. On BM25: 329 failure pairs, 19.5 % first-changed-line beyond a 512-token window.
- `make_annotation_sample.py` — `results/obj2/annotation/` (50-bug blank sheet + key + README).
- `docs/PREMISE_NOTE.md` — resolved: mainstream IRBL benchmarks (Bench4BL) are
  source-only; the data-quality literature treats non-source/test ground truth as
  noise to remove. BeetleBox is the exception. Framing narrows to "what fixes
  contain vs what evaluations reach".

## Remaining

- **BLAZE + FLIM GPU runs** — smoke test in progress (GPU shared with another job).
  After: rerun `obj2_wp_analysis.py`, `obj2_classical_vs_parsing.py`,
  `obj2_failure_analysis.py`, `obj2_tables.py`, `obj2_figures.py` (all pick up the
  new diagnostics automatically).
- 50-bug two-person agreement check — sheet is ready, needs a second annotator.
- `docs/SANER_REVIEW_RESPONSE.md`, `GLOSSARY.md` — drafted, final prose pass.
- GitHub repo: `gh repo create polyglot-bug-localization --private` then push.

## Supplementary — what a retrieval stage would have cost (not used)

The design **has no retrieval stage** (advisor decision). For context, a FAISS +
BGE-code top-K retriever (cached embeddings, 89–98 % snapshot coverage, 100 % on
code files) would surface a ground-truth file in the Top-500 for:

| project | Mono bug-recall@500 | Poly bug-recall@500 |
|---|---|---|
| localstack/localstack | 0.90 | 0.83 |
| liquibase/liquibase | 0.30 | 0.48 |
| ansible/ansible | 0.30 | 0.56 |
| apache/dolphinscheduler | 0.19 | 0.47 |
| apache/airflow | 0.15 | 0.24 |
| elastic/elasticsearch | 0.11 | 0.24 |
| **POOLED** | **0.26** | **0.47** |

- Genuine retrieval difficulty on large snapshots (elasticsearch ≈ 27 k
  files/snapshot; Top-500 ≈ 1.8 %). This is one of the reasons the design drops
  the retrieval stage — full-corpus ranking removes the ceiling entirely.
- Poly-fix **bug-level** recall > Mono-fix because Poly-fix bugs have more
  ground-truth files; **file-level** recall is similar or lower for Poly, partly
  because Poly-fix fixes more often **add** files absent from the buggy snapshot.
- Kept only as a supplementary figure: it is itself consistent with the thesis —
  a BGE-code retriever is tuned for single-language code search.
