# Mono-fix or Poly-fix? On the Prevalence and Localizability of Multi-Language Bug Fixes

Objective 2 of the PhD. An **exploratory, descriptive study** of what happens when a
single bug fix touches files in more than one programming language.

- **Design spec:** `obj2/Polyglot_BL_FSE_Brief.pdf` (the rebuilt design)
- **Superseded:** `obj2/BL-Polyglot.pdf` — the SANER 2026 registered report that was
  rejected; kept only as background. Reviewer responses: `docs/SANER_REVIEW_RESPONSE.md`.
- **Venue ladder:** FSE 2027 → ICPC 2027 → IST.
- **Working notes / detailed status:** `PROGRESS.md`. Rules: `docs/CLASSIFICATION_RULES.md`.

---

## Setup

### Environment

Python **3.12**. From the repo root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

`requirements.txt` pins `torch==2.8.0`; the runs were done with a CUDA 12.6 build
(`torch==2.8.0+cu126`). For a GPU install a CUDA-matched wheel from
<https://pytorch.org/get-started/locally/> **before** `pip install -r requirements.txt`
(or reinstall torch afterwards). CPU-only is fine for Steps 0–2 and the BM25
baseline; BLAZE and FLIM need a GPU (~16 GB).

All script paths resolve relative to the repo root (`Scripts/paths.py`, and
`_OBJ2_ROOT` in the `src/` modules — override with `export OBJ2_ROOT=/abs/path`
if you run the code from outside the tree).

### Data (not in the repository)

`data/` is git-ignored — a fresh clone has **no repositories, embeddings or bug
reports**. This is a within-lab reproduction: the inputs come from Objective 1.

```
data/
  processed/
    bug_reports_clean.parquet      BeetleBox bug reports (all projects; filtered at classify time)
    project_metadata.parquet       per-project language / LoC / domain
    embedding_dbs/
      <proj>_blob_embeddings32.pkl  fp32 BAAI/bge-code-v1 embedding per file blob
      <proj>_bug_metadata32.pkl     fp32 embedding + commit_sha + ground_truth_files per bug
  repos/
    java/{elastic_elasticsearch,liquibase_liquibase,apache_dolphinscheduler}
    python/{ansible_ansible,apache_airflow,localstack_localstack}   # full history, not shallow
```

- **Repos:** `git clone` each of the six at full depth into
  `data/repos/<lang>/<owner>_<name>/`.
- **Bug reports + metadata:** from the BeetleBox dataset (Chakraborty et al.,
  *BLAZE*, TSE 2025), reshaped to the parquet schema above
  (`repo_name, bug_id, bug_report_text, ground_truth_files, pre_fix_commit_sha,
  fix_commit_sha, language, source_dataset, …`).
- **Embeddings:** `Scripts/_obj1_reference/build_embed_database_pipeline.py`
  builds the `embedding_dbs/` pickles with `BAAI/bge-code-v1`
  (`CHUNK_SIZE=512`, `CHUNK_OVERLAP=50`); GPU, several hours per large project.

The six projects and their languages are declared in
`Scripts/paths.py::SELECTED_PROJECTS`.

---

## Running

```bash
source .venv/bin/activate

# --- descriptive core (CPU, minutes) ---
python Scripts/extract_fix_commits.py            # -> data/obj2/fix_files_raw.parquet
python Scripts/classify_bugs.py                  # -> results/obj2/bug_classification.csv
python Scripts/prevalence_report.py              # RQ1
python Scripts/boundary_sensitivity.py           # RQ1 sensitivity range
python Scripts/feasibility_matrix.py             # RQ2  (CPU, ~2 min)
python Scripts/retrieval_recall_by_class.py      # supplementary (CPU, ~20 min)
python Scripts/make_annotation_sample.py         # 50-bug agreement sheet

# --- experiments: full-snapshot ranking, within-project (resumable) ---
OBJ2_MODELS=BM25  python Scripts/run_obj2_experiments.py    # CPU, ~1 h all 6 projects
OBJ2_MODELS=BLAZE python Scripts/run_obj2_experiments.py    # GPU, ~half a day
OBJ2_MODELS=FLIM  python Scripts/run_obj2_experiments.py    # GPU, ~half a day; first run pulls microsoft/codebert-base

# smoke a GPU technique first (1 project = localstack, 1 epoch):
OBJ2_SMOKE=1 OBJ2_MODELS=BLAZE python Scripts/run_obj2_experiments.py

# --- analysis (CPU; re-run after each technique lands) ---
python Scripts/analysis/obj2_wp_analysis.py            # RQ3
python Scripts/analysis/obj2_classical_vs_parsing.py   # RQ4  (inversion test)
python Scripts/analysis/obj2_failure_analysis.py       # RQ4  (composition + truncation)
python Scripts/analysis/obj2_tables.py                 # results/obj2/tables/
python Scripts/analysis/obj2_figures.py                # results/obj2/figures/
```

Every step writes to `results/obj2/` (and `data/obj2/` for the two derived
parquets). Experiment runs are **resumable** — each finished project is appended
to `results/obj2/wp_cp_summary.csv` and skipped on rerun. Select a subset with
`OBJ2_MODELS=BM25,BLAZE` or `OBJ2_SMOKE_PROJECT=liquibase/liquibase`.

---

## 1. What the study is about

Bug-localization research is evaluated on the assumption that a fix lives in the
source files of a project's main language. Real fixes often do not — correcting a
defect can mean changing the source, updating a test, and revising a schema or a
configuration file that encodes the expected behaviour.

Two things can go wrong when a fix crosses file types, and they differ in kind:

1. **Architectural limit** — a technique that parses source into a structured
   representation (AST, program graph) has *no parser* for a YAML / JSON / SQL
   file, so it cannot represent that file at all.
2. **Semantic limit** — a technique can read the file but ranks it poorly because
   its vocabulary and structure differ from what it was trained on.

No existing evaluation separates them. Classical information retrieval processes
any file as a bag of tokens, so it is the condition under which the parsing
techniques' advantage can be tested. If parsing techniques fail where classical
retrieval holds, reported progress over classical baselines may hold only on the
part of the task that parses.

The study **does not** claim a tool *ought* to rank a `.yml`/`.json` file
(mainstream benchmarks are source-only; see `docs/PREMISE_NOTE.md`). The claim is
narrower: a class of fix exists whose ground truth, as recorded by the dataset's
own authors, crosses file types — the gap is between *what a fix contains* and
*what an evaluation reaches*.

---

## 2. Research questions

The unit of analysis is the **fix**, decided mechanically from the fix commit's
file extensions — not the project's language composition.

- **RQ1 — Prevalence.** What proportion of fixes in the six projects are Poly-fix
  (span ≥ 2 languages), and what file types do the additional files belong to?
- **RQ2 — Architectural feasibility.** For each technique, which Poly-fix file
  types can it ingest at all? Binary per technique per file type, with the
  failure mode, attributed to the *technique* or to the *available implementation*.
- **RQ3 — Within-project performance.** Among techniques that can ingest the
  files, how does localization performance differ between Mono-fix and Poly-fix
  bugs, controlling for project by comparing within the same project?
- **RQ4 — Classical baseline.** On Poly-fix bugs, does classical retrieval hold
  where the parsing technique fails or degrades? An *inversion* — classical ≥
  parsing on Poly-fix while trailing on Mono-fix — is the strongest possible
  finding and gates the venue (FSE vs ICPC/IST).

**Not research questions:** retrieval recall (the design has **no retrieval
stage** — every technique ranks the whole snapshot).

---

## 3. Design decisions (locked with the advisor, 2026-09-06)

| Decision | Choice |
|---|---|
| Poly-fix headline figure | **broad grain — 27.4 %** (secondary is any language with a grammar). Also reported: headline 21.0 % (YAML/JSON/XML/SQL only), strict 8.2 % (≥ 2 programming languages). Sensitivity range **[8.2 % – 41.9 %]**. |
| Retrieval stage | **Removed.** Every technique (BM25, BLAZE, FLIM) ranks the entire pre-fix snapshot. No FAISS/BGE top-K filter. |
| Experiment scope | **Within-project only.** No cross-project arm (COOBA dropped). |
| Techniques | **BM25** (classical, `bm25s`) · **BLAZE** (fine-tuned language-agnostic) · **FLIM** (parsing, AST → function graph). All full-snapshot. |
| Ruleset | `RULESET_VERSION = 0.2.0` — **frozen 2026-09-06**. Bump to 0.2.1 only if the 50-bug agreement check finds a rule error. |
| Languages | Java and Python (the two the AST parsers support). Design choice + technical note in `docs/PROJECT_SELECTION.md`. |

---

## 4. Dataset

BeetleBox, six projects; a bug is *kept* only if its fix touches the project's
AST-parseable primary language.

| Project | Lang | Kept bugs | Mono-fix | Poly-fix | Poly % (broad) |
|---|---|---|---|---|---|
| elastic/elasticsearch | Java | 721 | 564 | 157 | 17.8 % |
| liquibase/liquibase | Java | 199 | 99 | 100 | 49.7 % |
| apache/dolphinscheduler | Java | 698 | 523 | 175 | 23.6 % |
| ansible/ansible | Python | 626 | 352 | 274 | 43.5 % |
| apache/airflow | Python | 917 | 739 | 178 | 18.8 % |
| localstack/localstack | Python | 433 | 284 | 149 | 34.4 % |
| **TOTAL** | | **3594** | **2561** | **1033** | **27.4 %** |

Every project has ≥ 99 bugs in its smaller class → balanced within-project
comparison is viable for all six. Secondary-language mix per project: ES = YAML
test specs + `build.gradle`; liquibase = Java+Groovy + XML/SQL; dolphinscheduler
= XML + TS/Vue frontend + SQL; ansible = YAML playbooks; airflow = mixed config;
localstack = JSON snapshots (the brief's motivating example).

Data lives under `data/` (git-ignored): the 6 repos, fp32 BGE embeddings, and the
bug-report parquet. A fresh clone does not contain them — see **Setup → Data** for how to
obtain / rebuild each part. Paths: `Scripts/paths.py`.

---

## 5. Repository layout

```
obj2/            the two source PDFs
docs/            CLASSIFICATION_RULES · GLOSSARY · PREMISE_NOTE · SANER_REVIEW_RESPONSE
                 PROJECT_SELECTION · THREATS_TO_VALIDITY · REGISTER_RULES
src/             real copy of Objective1/src: blaze/ flim/ cooba/ blgan/ (paths rewritten,
                 FLIM patched: _FUNC_EMB_CACHE + FLIM_DIAG_CSV dump)
Scripts/
  paths.py                     central path config + the 6 project list
  _obj1_reference/             unmodified Objective 1 scripts the obj2 ones derive from
  extract_fix_commits.py       Step 0  fix commit -> complete changed-file list
  classification_rules.py      Step 0  frozen rule catalog (RULESET_VERSION, C1-C4, 3 grains)
  classify_bugs.py             Step 0  -> data/obj2/bug_classification.parquet + results CSV
  prevalence_report.py         Step 1  prevalence + secondary-language distribution
  boundary_sensitivity.py      Step 1  prevalence under each toggle -> range
  feasibility_matrix.py        Step 2  technique x file-type ingestion outcome
  retrieval_recall_by_class.py  supplementary  "what a retrieval stage would have cost"
  run_obj2_experiments.py      Step 3  WP, full-snapshot: BM25 + BLAZE + FLIM
  make_annotation_sample.py    50-bug two-person agreement sheet
  analysis/
    obj2_wp_analysis.py            Step 3  paired Mono-vs-Poly, Cliff's delta, bootstrap CIs
    obj2_classical_vs_parsing.py   Step 4  BM25 vs FLIM on Poly-fix, the inversion test
    obj2_failure_analysis.py       Step 4  failure-set composition + truncation check
    obj2_tables.py                 Tables 1-4 (Markdown + CSV)
    obj2_figures.py                4 PNGs
data/obj2/       derived: fix_files_raw.parquet, bug_classification.parquet
results/obj2/    all outputs (tables/ figures/ analysis/ diagnostics/ prevalence/ annotation/)
```

---

## 6. Status

### 6a. Implementation-wise

| Component | State |
|---|---|
| Scaffold, self-contained data copy, own git repo | **done** |
| `extract_fix_commits.py`, `classification_rules.py`, `classify_bugs.py` | **done** |
| `prevalence_report.py`, `boundary_sensitivity.py` | **done** |
| `feasibility_matrix.py` | **done** |
| `retrieval_recall_by_class.py` (supplementary) | **done** |
| `run_obj2_experiments.py` — BM25 path | **done** |
| `run_obj2_experiments.py` — BLAZE path (full-snapshot, class diagnostics) | **done**, first real run in validation (see 6b) |
| `run_obj2_experiments.py` — FLIM path (`run_flim`, `TOP_K_CANDIDATES` patch, `FLIM_DIAG_CSV`) | **done**, not yet run |
| `analysis/obj2_wp_analysis.py` | **done** (runs when BLAZE/FLIM diagnostics exist) |
| `analysis/obj2_classical_vs_parsing.py` | **done** (needs FLIM diagnostics for the inversion test) |
| `analysis/obj2_failure_analysis.py` | **done** (composition + truncation; extends automatically to new techniques) |
| `analysis/obj2_tables.py`, `obj2_figures.py` | **done** (regenerate as results land) |
| `make_annotation_sample.py` | **done** |
| Docs (`CLASSIFICATION_RULES`, `GLOSSARY`, `PREMISE_NOTE`, `PROJECT_SELECTION`, `THREATS_TO_VALIDITY`, `REGISTER_RULES`, `SANER_REVIEW_RESPONSE`) | **drafted**; need a final prose pass before writing |
| Cross-project arm / COOBA | **dropped** by decision (code dormant in `run_obj2_experiments` history) |

Nothing is left to *build*. Remaining implementation risk is that the FLIM
full-snapshot path (`run_flim` monkey-patch + `FLIMRanker` over a 27 k-candidate
list per bug) has never executed — first run may need a fix.

### 6b. Running-wise

| Step | Run? | Output | Notes |
|---|---|---|---|
| 0 extract | ✅ | `data/obj2/fix_files_raw.parquet` | 100 % commit recovery, 4995 bugs |
| 0 classify | ✅ | `results/obj2/bug_classification.csv` | 3594 kept, RULESET 0.2.0 |
| 1 prevalence | ✅ | `results/obj2/prevalence/` | 27.4 % broad / 21.0 % / 8.2 % |
| 1 sensitivity | ✅ | `results/obj2/boundary_sensitivity.csv` | range [8.2 % – 41.9 %] |
| 2 feasibility | ✅ | `results/obj2/feasibility_matrix.csv` | BM25/BLAZE succeed; FLIM `degraded_wholefile`; COOBA `trivial_graph` |
| supplementary retrieval recall | ✅ | `results/obj2/retrieval_recall*.csv` | 0.11–0.90 by project (why we drop retrieval) |
| 3 BM25 (all 6 projects) | ✅ | `results/obj2/wp_cp_summary.csv` + 6 diagnostics | ~25 min ES, minutes for the rest |
| 3 BLAZE | **in validation** | — | smoke on localstack: training done (`train_loss=1.31`), full-snapshot eval running |
| 3 FLIM | **pending** | — | needs GPU; first run downloads `microsoft/codebert-base` |
| 50-bug agreement check | **pending** | sheet ready at `results/obj2/annotation/` | needs a second annotator |

**Compute still to spend:** BLAZE + FLIM, all 6 projects, full-snapshot,
~1–1.5 GPU-days total (elasticsearch ≈ 27 k files/snapshot is the long pole;
per-snapshot embedding caching makes bugs 2..N cheap). Both resumable — each
finished project is appended to `wp_cp_summary.csv` and skipped on rerun.

```bash
source /home/cs21d002_eashaan/PhD/Objective1/obj1/bin/activate
OBJ2_MODELS=BLAZE python Scripts/run_obj2_experiments.py     # then
OBJ2_MODELS=FLIM  python Scripts/run_obj2_experiments.py
```

### 6c. Analysis-wise

| Analysis | Run? | Blocked on |
|---|---|---|
| Prevalence + per-project + secondary-language distribution (RQ1) | ✅ complete | — |
| Boundary-rule sensitivity range (RQ1) | ✅ complete | — |
| Feasibility matrix (RQ2) | ✅ complete | — |
| WP performance table, BM25 only (RQ3) | ✅ partial | BLAZE + FLIM runs |
| Paired Mono-vs-Poly, Cliff's δ, bootstrap CIs (RQ3) | ⏳ code ready | BLAZE + FLIM diagnostics |
| Per-extension MRR on secondary GT files (RQ3) | ⏳ code ready (BM25 slice runs) | BLAZE + FLIM diagnostics |
| Classical-vs-parsing inversion test (RQ4) | ⏳ code ready | FLIM diagnostics |
| Failure-set composition + chi-sq (RQ4) | ✅ partial (BM25) | recompute with all techniques |
| Truncation check (RQ4 mechanism) | ✅ partial (BM25): 19.5 % beyond a 512-token window | recompute with all techniques |
| Semantic-link coding of the failure set (RQ4) | ❌ manual | annotator time |
| Tables 1–4, Figures 1–4 | ✅ generated (BM25 data) | regenerate after BLAZE/FLIM |

After the BLAZE + FLIM runs, one command refreshes everything:

```bash
python Scripts/analysis/obj2_wp_analysis.py
python Scripts/analysis/obj2_classical_vs_parsing.py
python Scripts/analysis/obj2_failure_analysis.py
python Scripts/analysis/obj2_tables.py
python Scripts/analysis/obj2_figures.py
```

---

## 7. Preliminary findings (from the completed steps)

- **Prevalence holds.** 27.4 % of kept fixes are Poly-fix (broad); robust to how
  documentation and data-config sub-types are treated; sensitive to test code
  (→ 11.6 %) and changelog fragments (→ 41.9 %).
- **The architectural limit is real and clean (RQ2).** BM25 and BLAZE ingest every
  file type. FLIM extracts zero functions from YAML/XML/SQL/JSON and falls back to
  whole-file text (`degraded_wholefile`); COOBA's parser returns a 1-node graph
  (`trivial_graph`). Two edge cases: a bare JSON object parses as a Python literal
  (COOBA succeeds only in Python projects); `.gradle` matches the Java method regex.
- **Classical retrieval does not struggle more on Poly-fix (RQ4, baseline only).**
  BM25 macro-average MRR: Poly-fix **0.219** ≥ Mono-fix **0.181**; Poly ≥ Mono in
  4 of 6 projects (localstack 0.39 vs 0.21, ansible 0.35 vs 0.28). This is the
  "classical retrieval holds" half of the inversion, visible before the neural
  runs.
- **Truncation is a plausible mechanism.** 19.5 % of BM25 failure-set secondary
  files have their first changed line beyond a 512-token window.

---

## 8. Open items needing a human

1. **GPU time** for the BLAZE + FLIM runs (~1–1.5 days).
2. **Second annotator** for the 50-bug agreement check (`results/obj2/annotation/README.md`
   has the scoring recipe; target Cohen's κ ≥ 0.8).
3. **Prose pass** on `docs/` before drafting (register rules in `docs/REGISTER_RULES.md`).
4. **GitHub repo:** `gh repo create polyglot-bug-localization --private` then
   `git remote add origin … && git push -u origin master`.
5. **Advisor gates:** the prevalence figure (done — bring 27.4 % [8.2–41.9 %]) and
   the venue decision (after RQ2 + RQ4: architectural failure + inversion → FSE;
   mere degradation → ICPC/IST).

## Artifact

`results/obj2/bug_classification.csv` — the labelled Mono-fix/Poly-fix
classification for every bug in the six projects, with per-bug boundary flags and
grain membership. Released independently of the model results; no prior dataset
records which bugs have fixes that cross file types.
