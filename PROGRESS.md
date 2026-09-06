# Objective 2 — progress

RULESET_VERSION `0.2.0-draft` (freeze with advisor before writing).

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
| 3 experiments | `Scripts/run_obj2_experiments.py` | **BM25 WP arm: running (CPU).** BLAZE/FLIM (WP) + BLAZE/COOBA (CP): GPU, ~2.5–3 days. Resumable. `OBJ2_SMOKE=1` for a 1-project check. `OBJ2_MODELS=BM25 OBJ2_ARMS=WP` etc. to select. |
| 3 analysis | `Scripts/analysis/obj2_wp_analysis.py` | runs once `results/obj2/diagnostics/*.csv` exist |
| 4 analysis | `Scripts/analysis/obj2_classical_vs_parsing.py` | same |

## Not started

- `Scripts/analysis/obj2_tables.py`, `obj2_figures.py` — paper artifacts, after results.
- COOBA needs GloVe: `cp -r ../Objective1/data/glove PhD/Objective2/data/` before the CP arm.
- FLIM adapter: `run_flim_experiment` already has the right signature; smoke-test it
  (`OBJ2_SMOKE`) once GPU time is available — first FLIM run downloads `microsoft/codebert-base`.
- 50-bug two-person classification agreement check (needs a second annotator).
- GitHub repo: `gh repo create polyglot-bug-localization --private` then `git remote add origin … && git push -u origin master`.

## Finding — retrieval recall is low and project-dependent

The FAISS + BGE-code retriever (cached embeddings, 89–98 % snapshot coverage,
100 % on code files) surfaces a ground-truth file in the Top-500 for:

| project | Mono bug-recall@500 | Poly bug-recall@500 |
|---|---|---|
| localstack/localstack | 0.90 | 0.83 |
| liquibase/liquibase | 0.30 | 0.48 |
| ansible/ansible | 0.30 | 0.56 |
| apache/dolphinscheduler | 0.19 | 0.47 |
| apache/airflow | 0.15 | 0.24 |
| elastic/elasticsearch | 0.11 | 0.24 |
| **POOLED** | **0.26** | **0.47** |

- Not a data bug — genuine retrieval difficulty on large snapshots (elasticsearch
  ≈ 27 k files/snapshot; Top-500 ≈ 1.8 %).
- Poly-fix **bug-level** recall > Mono-fix because Poly-fix bugs have more
  ground-truth files (more chances of ≥ 1 hit); **file-level** recall is similar
  or lower for Poly (pooled 0.186 vs 0.166; ES 0.054 vs 0.038), partly because
  Poly-fix fixes more often **add** new files absent from the buggy snapshot.
- Reported as a **property of the setup**. The reranker comparison is meaningful
  mainly on **localstack** (and partially **liquibase**); for the other four the
  reranker is evaluated on the retriever-surfaced subset and read as
  retrieval-limited. This is itself consistent with the study's thesis: the
  pipeline, retriever included, is tuned for single-language code search.
- Advisor decision needed: (a) proceed and report this prominently; (b) raise K;
  (c) restricted evaluation on the retrievable subset (recommended, matches
  Objective 1); (d) add a BM25-union retrieval stage (scope creep — the brief
  says retrieval is not a research question).
