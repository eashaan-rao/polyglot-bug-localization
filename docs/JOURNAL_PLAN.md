# Journal plan — polyglot bug localization (Objective 2), v2

Status: 2026-10-17. Target: **ACM TOSEM**. Supersedes v1 (2026-10-13).
RQ1 (prevalence, sensitivity) is done and unaffected by anything below.

Decisions taken by Eashaan on 2026-10-17:

| # | Decision |
|---|---|
| D1 | Target journal: **TOSEM** |
| D2 | **Chronological split only** — train on older bugs, test on newer |
| D3 | Second fold only if compute allows (one L40) — see §6 |
| D4 | **No second IR baseline** (BM25 only) |
| D5 | The October tmux runs are stopped and superseded |
| D6 (2026-10-30) | Primary outcome = MAP (AP@10 when LocAgent is compared); secondary CFR@10, MRR, Top-k |
| D7 (2026-10-30) | LocAgent: 7B fine-tuned model (32B does not fit the shared L40), Python projects only |
| D8 (2026-10-30) | BeetleBox-removed bugs: separate analysis, never pooled with kept bugs |
| D9 (2026-10-30) | BL-GAN and the Objective 1 re-runs on hold; author list decided by the supervisor |
| D10 (2026-10-31) | Learning rate (only tuned hyper-parameter): grid around published values, selected by validation MAP, once per project/fold with seed 13 — BLAZE {2e-7, 2e-6, 2e-5}, FLIM {2e-5, 5e-5}; epochs still by each technique's original criterion (`Scripts/lr_select.py`) |
| D11 (2026-10-31) | Poly-fix split into behaviour-bearing (434 bugs) and test-asset-only (551) in every result |
| D12 (2026-10-31) | Three seeds for BLAZE and FLIM (training randomness is not covered by bootstrap over bugs) |
| D13 (2026-11-01) | Two folds, no new projects; folds before seeds (seeds 42/2027 on fold 1 for a subset of projects) |
| D14 (2026-11-01) | Category (c) "no-primary" fixes (984) as a third stratum: RQ1/RQ2 + BM25 scoring; never pooled |
| D15 (2026-11-01) | Save every trained BLAZE/FLIM model (`data/obj2/models/`); BLAZE-all ablation (fold 1, seed 13, BLAZE's LR); LocAgent variance repeats (2 × 100 fold-1 bugs) in the code |
| D17 (2026-11-03) | BM25 tokenizer keeps whole identifiers plus camelCase parts (BM25 rerun for localstack, elasticsearch); FLIM's TF-IDF tokenizer unchanged (split-only). Method frozen for the full run (`Scripts/run_full.sh`) |
| D16 (2026-11-01) | Techniques are evaluated as published; no adaptation to secondary languages (FLIM-fallback, BLAZE-all are labelled diagnostic variants) |
| D18 (2026-11-03) | Same split rule for every project: liquibase keeps its small validation set (10 / 8 bugs in folds 1 / 2 after purging; others 21–48) for consistency; stated as a threat, instability shown by its extra seeds. Full run launched 2026-11-03 09:21 |

---

## 1. Three paradigms — which techniques

The study needs one technique per paradigm, where the paradigms differ in
**what the architecture can ingest**:

| Paradigm | Ingests | Technique | Venue | Code |
|---|---|---|---|---|
| Classical IR | any text, as tokens | **BM25** | — | `src/bm25.py` |
| Language-agnostic neural | any text, as chunks (parser only shapes chunk boundaries) | **BLAZE** | TSE 2025 | `src/blaze/wp.py` (reported separately: BeetleBox leakage) |
| Parse-dependent | files the project-language parser accepts (functions + AST-derived features) | **FLIM** | EMSE 2022 | `src/flim/` |

Why FLIM and not the other two codebases we have:

| Candidate | What its code shows | Verdict |
|---|---|---|
| **FLIM** | Splits files into functions with the language parser, fine-tunes CodeBERT on (report, function) pairs, fuses with 19 IR features (AST-derived fields, import graph). Original code available (`Resources/flim-main`). SE venue. | **Use.** Parse-dependence is architectural, not incidental. |
| **BL-GAN** (TKDE 2023) | AST graph network (`src/blgan/ast_parsers.py`); an unparseable file becomes an empty graph, so only its path is seen. Purest parse-dependence. Scaffolded in Objective 1, never run; non-SE venue. | **Optional second parsing technique** if time allows: it would answer "one parsing technique" (threat). At minimum, a feasibility-matrix row. |
| **TRANP-CNN** (TSE 2019) | Statements = text lines (`src/tranp_cnn/data_prep.py`, no AST). Ingests any text, and its design is cross-project transfer. | **Exclude.** Same paradigm as BLAZE, not a parsing technique. Say so in the method. |

### 1.1 Literature check: should an LLM-agent paradigm be added?

The 2025–2026 localization literature is dominated by LLM agents on SWE-bench:
LocAgent (ACL 2025, code-graph tools), OrcaLoca (ICML 2025), CoSIL (2025,
call-graph search), SweRank / SweRank+ (2025, LLM retrieve-and-rerank),
SHERLOC (2026), and the ICPC 2026 CogniGent agent on Bench4BL. A TOSEM
reviewer in 2027 will ask why no LLM-era technique is evaluated.

The agent paradigm fits the paper's thesis unusually well, because the
agents themselves split along the same line:
* **Text-tool agents** (SWE-agent-style shell tools: `ls`, `grep`, `cat`)
  can open any file.
* **Structure-indexed agents** (LocAgent, CoSIL, OrcaLoca) navigate a graph
  built by parsing source. Files the indexer cannot parse are not nodes.

**Recommendation:** add a fourth arm, but keep it scoped:
1. **Feasibility only (cheap, CPU):** run the indexers of LocAgent and CoSIL
   on our snapshots and record which ground-truth file types become nodes →
   RQ2 rows. No LLM needed.
2. **One agent run (GPU, ~1–2 days):** a text-tool agent with an open-weight
   model served locally (e.g. Qwen3-Coder-30B-A3B in FP8 on the L40), output
   = ranked top-10 files. Compare to the other techniques on Top-1/5/10 and
   MRR@10 (agents give no full ranking, so MAP is not comparable).
3. **Contamination control is mandatory:** our test bugs are 2022–2024,
   before any current model's cutoff. Run a closed-book probe (report title
   only, no repository → "which files were changed?") and report its hit rate
   per class; agent results are an upper bound and stated as such.

Decision needed: **E1 — add the agent arm (feasibility + one run)?**

---

## 2. What was fixed before any run (loopholes found in the audit)

Each item was found by reading or running the code, and is fixed in the
working tree (not yet committed).

### 2.1 Data and evaluation

| # | Loophole | Effect | Fix |
|---|---|---|---|
| L1 | `bug_id` is not unique across repos (57 214 rows, 53 604 ids). All three pipelines looked up report text by `bug_id` only. | **749 / 3 594 kept bugs (20.8 %) were queried with another project's report** (svelte, quarkus, electron, …). Every earlier WP number is invalid, BM25 included. RQ1 scripts were not affected (they key on `(repo_name, bug_id)`). | `Scripts/bugs.py`: everything keyed by `(repo_name, bug_id)`; asserts one-to-one. **Objective 1 has the same lookup** (TRANP-CNN, BLAZE, COOBA, sweep scripts) — needs its own check. |
| L2 | Three different file universes (BM25/FLIM: blobs with a BGE embedding; BLAZE: every blob incl. images, jars). | Techniques ranked different candidate sets. | `Scripts/universe.py`: one table per snapshot; universe R (ruleset files, primary) and T (all text, sensitivity). |
| L3 | Three ground-truth matchers; FLIM's `p.endswith(g)` also matched `barfoo.py` for `foo.py`. BeetleBox GT includes changelog fragments and docs that the class definition excludes. | Inconsistent, partly wrong GT; class and target disagreed. | GT = fix-commit files the frozen ruleset counts, exact pre-fix path (`eval_ground_truth`). Added files → *unreachable*, reported separately. |
| L4 | Random 80/20 split. | Temporal leakage. | Chronological split + **purging**: a training bug fixed after the validation period started (or a validation bug fixed after the test period started) is dropped. |
| L5 | Experiments sliced by `class` (1 033 Poly) instead of the locked broad grain (985). | 48 tier-3-only bugs counted as Poly-fix. | `study_class`: Mono / Poly (broad grain) / Poly-tier3 (ranked, excluded from comparisons). |
| L6 | Ties broken by sort order (BM25 gives many files score 0). | A technique could gain from ties. | Expected rank under random tie-breaking. |
| L7 | Each technique computed its own metrics. | Three metric implementations. | `Scripts/evaluate.py` is the only evaluator: per-bug and per-GT-file tables, random-ranking baseline per bug, primary-only / secondary-only metrics. |
| L8 | BLAZE and FLIM ran concurrently on the L40. | BLAZE lost airflow and localstack to OOM. | Driver runs GPU techniques sequentially. |

### 2.2 FLIM

| # | Loophole | Fix |
|---|---|---|
| L9 | Loss was `BCEWithLogitsLoss(cosine, label)`: sigmoid of a cosine is confined to [0.27, 0.73], the loss floors near 0.5, embeddings collapsed (top elasticsearch scores ≈ 0.996). Old FLIM MRR on elasticsearch: **0.001**. | Original FLIM fine-tuning (`flim-main/CodeBERT-finetune/run.py`): pooler output, NL 128 / code 256 tokens, in-batch softmax CE, AdamW 2e-5, **10 epochs**, keep best validation MRR (+ patience 3). |
| L10 | Only the 4 semantic features; the paper fuses **19 IR features** (Eq. 5). Ours was the paper's weaker "FLIMs" ablation. | 18 of 19 added (`src/flim/ir_features.py`): lexical, collaborative filtering, class-name, recency, frequency, AST-field similarities, import-graph PageRank/HITS/degree. f2 (JDK API docs) dropped — no Python counterpart. |
| L11 | The LTR stage was a simplified re-write whose CV used a stable sort on rows that listed GT files first: **a constant predictor scored MAP 1.0, won selection, and FLIM output one score for every file** (smoke MRR 0.0007, below random 0.007). | Ported the original AdaptiveBL `Adaptive_Process` (13 weighting methods, 16 SGD regressors × 6 cut rules, 2-fold CV) with tie-aware MAP and seeded within-bug shuffling (`src/flim/adaptive.py`). Smoke MRR now 0.33. |
| L12 | Java "AST" was a regex; whole-file fallback for anything unparseable was silent; first 20 functions only. | Shared parser `src/parsing.py` (Python `ast`, tree-sitter-java). FLIM-strict (paper-faithful) vs FLIM-fallback are two evaluation views of one trained model. No function cap. |
| L13 | No features normalisation; no seeds. | Min-max on training rows (AdaptiveBL); seeded sampling and training. |

### 2.3 BLAZE

| # | Loophole | Fix |
|---|---|---|
| L14 | **Dynamic chunking never ran** — `tree_sitter_languages` 1.10 is incompatible with `tree_sitter` 0.25, the splitter swallowed the TypeError and always used fixed 60-line chunks. True in Objective 1 too. | Installed `tree-sitter-java` / `tree-sitter-python` wheels; splitter uses them. Original constants (general_cost 50, window 30). |
| L15 | Backbone BGE-code-v1 (1.5 B) **frozen**, adapters only, LR 1e-4, batch 8, report 512 tokens. | Original config (`main-sage.yaml`): **CodeSage-small, full fine-tuning**, 2 residual layers, mean pooling, report 1 024 / code 512, batch 20, warm-up 100, AdamW wd 0.01; paper's 15 epochs, selection on val loss, patience 3. Revision pinned. ~10× cheaper to score a snapshot. |
| L16 | Trained on every GT file; the original trains only on chunks of source-language files (`convert_to_chunks.py`). | Faithful filter (.py / .java GT files only). Scoring still covers every file. |
| L17 | Validation batches unshuffled → each batch ≈ one bug, almost all pairs positive, val loss 0.21 vs train 2.35 — useless for selection. | Fixed-seed shuffled validation batches (val loss now 1.66 → 1.61, tracks training). |
| L18 | Val loss not logged; O(n²) path lookup per snapshot. | Per-epoch history in the run manifest; new runner. |

### 2.4 Reproducibility

Seeds 13 / 42 / 2027 for the trained techniques (`Scripts/repro.py`); every
score file has a JSON manifest (git head, package versions, GPU, split sizes,
purge counts, hyper-parameters, epochs run, best epoch, LTR choice, wall
time); model revisions pinned (CodeSage-small `4d2a4f3`, CodeBERT `3b0952f`).

---

## 3. Loopholes in the design that remain open (to settle before the full run)

| # | Issue | Proposed handling |
|---|---|---|
| O1 | **BeetleBox removed reports that name the fixed file** (`BeetleBoxRemoved`): 1 226 reports from our six projects (elasticsearch 363, airflow 383, ansible 295, dolphinscheduler 83, localstack 63, liquibase 39). This filter removes the bugs where classical IR is strongest, so it biases RQ4 against BM25 — and may do so differently for Poly-fix. | **Sensitivity stratum (recommended):** classify the removed bugs with the frozen ruleset and evaluate BM25 + FLIM (+ BLAZE if budget) on the ones in our test windows. Report as "with the dataset's own filter undone". Decision **E2**. |
| O2 | The parseable-only view has **two opposite effects**: fewer distractors (smoke: BM25 bug 4512, rank 2 → 1) and unreachable GT (bug 4460, rank 4 → 129). A single 2 × 2 difference mixes them. | Report separately: (a) *reach@parse* = share of bugs with ≥1 parseable GT (the architectural ceiling); (b) primary-only metrics (distractor effect alone); (c) secondary-only GT ranks (semantic effect where reachable). |
| O3 | Poly-fix bugs have more GT files, so Top-k is easier by chance. | Covariate `n_gt_reach` in every model; per-bug random baseline; primary-only metrics. |
| O4 | Small per-project test sets: Poly-fix test bugs per project 17–63 (fold 1), 213 in total; liquibase validation only 10 bugs after purging. | Pooled mixed-effects models are the primary inference; per-project results descriptive. Fold 2 adds 206 Poly-fix test bugs (§6). |
| O5 | Model-selection criteria differ: FLIM on validation MRR (its `run.py`), BLAZE on validation loss (its Lightning checkpoint). | Keep each technique's *own original* criterion, with the same split, cap rule (paper epochs) and patience; state it. |
| O6 | BLAZE's 2e-7 LR was set for ~11 K training bugs; our projects have 100–600. | Smoke sweep (liquibase, 40 train bugs): 2e-7 still improving after 15 epochs (best val loss 1.608); 2e-6 over-fits by epoch 3 (1.631); **2e-5 best (1.438, epoch 9)**. Select LR per project on validation from {2e-7, 2e-6, 2e-5} with seed 13, then fix it for the other seeds. **Open check for the pilot:** on the 8 smoke test bugs 2e-5 scored MRR 0.13 vs 0.23 for 2e-7 — far too few bugs to mean anything, but it raises whether validation *loss* tracks ranking quality. The pilot computes validation MRR for each LR; if loss and MRR disagree, select on validation MRR (≈ +20 % BLAZE scoring cost). |
| O7 | Remaining FLIM deviations: positives = changed functions (diff overlap) instead of all functions; no CodeSearchNet "MIX" data; f2 dropped; same-report positives masked in the in-batch loss. | State all four. Optional ablation: MIX on one project. |
| O8 | Pre-trained encoders (CodeSage, CodeBERT) saw public GitHub code, possibly these repositories. | Threat (pre-training only, no fix links). Separate from O9. |
| O9 | Agent arm contamination (if E1). | Closed-book probe, §1.1. |
| O10 | Temporal drift: the class mix differs between train and test windows. | Report class proportions per split; class is a covariate anyway. |

---

## 4. Experimental design (as now implemented)

**Units.** 3 594 kept bugs; study class from the broad grain (Mono 2 561 / Poly 985 / tier-3 48).

**Split** (`Scripts/bugs.py`). Per project by `creation_date`: fold 1 = oldest 80 % → newest 20 %; validation = newest 10 % of the pool (≥ 20 before purging); purged. Fold 1 test: 719 bugs (Mono 483, Poly 213).

**Universe** (`Scripts/universe.py`). Per pre-fix snapshot: path, sha, is_text (≤ 1 MB, no NUL), in_ruleset, language, parse_status (`ok` / `partial` / `ok_nofunc` / `parse_error` / `no_parser`). R = text ∩ ruleset (primary), T = text (sensitivity). Built once on CPU (cached under `data/obj2/universe/`).

**Scores.** Every technique scores every T file of every test bug: `results/obj2/scores/<TECH>/fold<F>/seed<S>/<project>.parquet`.

**Evaluation** (`Scripts/evaluate.py`). 2 universes × 2 views (all / parse); expected ranks; Top-1/5/10, AP, RR, complete-fix recall@10, primary/secondary splits, random baseline; per-GT ranks with file type and parse status → RQ2 feasibility from the real parsers.

**Statistics** (Phase 4, to write). RQ3: per project Mann–Whitney + Cliff's δ + bootstrap CI; pooled mixed model `RR ~ class + n_gt_reach + log(n_cand) + report_len + (1|project)`. RQ4: `RR ~ technique × class + covariates + (1|project) + (1|bug)` — the inversion is the interaction; per-class paired Wilcoxon BM25 vs FLIM-strict, Holm. Seeds averaged per bug; seed SD reported. BLAZE in separate tables, never pooled.

---

## 5. Order of work

| Step | What | Where | Status |
|---|---|---|---|
| 1 | Universe for all split bugs (folds 1–2) | CPU | ✅ 3 521 snapshots (1.8 GB, gitignored) |
| 2 | BLAZE LR sweep on the smoke split | GPU | ✅ (O6); same seed reproduced the same best val loss to 4 decimals |
| 3 | **Pilot: liquibase, full split, 1 seed, all three techniques** — gates: loss curves flatten before the cap; FLIM-strict vs fallback differ only on unparseable files; a re-run with the same seed reproduces scores | GPU ~1–2 h | next |
| 4 | Decisions E1–E4 (§7) | you / advisor | — |
| 5 | Full fold 1: BM25 (CPU, parallel) + FLIM × 3 seeds + BLAZE × 3 seeds | GPU, sequential | — |
| 6 | Fold 2 (1 seed) if §6 budget holds | GPU | — |
| 7 | Phase 4 statistics script; update `analysis/*` to read `results/obj2/eval/` | CPU | — |
| 8 | Qualitative coding of 40–50 Poly-fix bugs FLIM-strict misses and BM25 hits; the 50-bug ruleset check | human | — |
| 9 | Manuscript (TOSEM), replication package | — | — |

---

## 6. Compute on one L40 (estimates from smoke runs; refined after the pilot)

Training chunks (BLAZE, fold 1): liquibase 3.2 K, ansible 16.7 K, localstack 21.2 K, dolphinscheduler 21.9 K, airflow 43.9 K, elasticsearch ≈ 40 K. Test chunks to score: ≈ 1.2 M in total (airflow 417 K).

| Run | Estimate |
|---|---|
| BM25, all projects | ~1 h CPU (parallel with GPU work) |
| FLIM, one seed, six projects | ~6 h |
| BLAZE, one seed, six projects (≈ 0.55 s / batch of 20, ~12 epochs) | ~14 h |
| BLAZE LR selection (two extra LRs, seed 13 only) | ~+25 h |
| **Fold 1, 3 seeds** | **≈ 4 days** |
| Fold 2, 1 seed, LR fixed | ≈ +1 day |
| Agent arm (E1) | ≈ +1–2 days |

So fold 2 with one seed is affordable (+25 % compute for +97 % Poly-fix test bugs).

---

## 7. Decisions still needed

* **E1** — Add the agent arm (feasibility rows for LocAgent/CoSIL + one text-tool agent run with a local open-weight model + contamination probe)? Recommended: yes.
* **E2** — Evaluate the BeetleBox-removed bugs as a sensitivity stratum (O1)? Recommended: yes, BM25 + FLIM at least.
* **E3** — BL-GAN as a second parsing technique (adds ~1–2 weeks of implementation risk)? Recommended: feasibility row only, full run only if time remains.
* **E4** — Fold 2: one seed (recommended) or three.
