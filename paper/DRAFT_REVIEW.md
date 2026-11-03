# Draft review — what the first full draft shows is missing or extra

Draft: `paper/main.tex` (JSS / Elsevier CAS template, 9 pages; convert to ACM
acmart for TOSEM later). Coloured markers in the PDF: red = result pending,
orange = citation missing, blue = gap in the study.

## Findings from writing the draft

**F1. The architectural limit is almost invisible in MRR / Top-k.** Computed
from the universe tables, before any technique runs (fold 1 test bugs):
98.1 % of Poly-fix bugs have at least one parseable fixed file (the keep
filter guarantees a primary-language file), but only 10.8 % have *only*
parseable fixed files, and 37.2 % of Poly-fix fixed files are unparseable
(Mono-fix: 0.1 %). A parser-dependent technique almost always can find *a*
file of a Poly-fix bug; what it cannot reach is a third of the fix. RR rewards
the first hit only, so RQ4 must use AP and complete-fix recall@10 as the
primary outcome, with RR/Top-k secondary. → decision G1.

**F2. Every parse failure in the ground truth is `no_parser`, none is
`parse_error`.** All 291 unparseable Poly-fix ground-truth files are YAML,
JSON, TypeScript, Shell, XML, Groovy, SQL, …; none is a Java/Python file the
parser rejected. RQ2's "technique vs implementation" attribution is therefore
clean: it is the technique.

**F3. RQ2 is mostly answerable without any model** (Table "Reachability" in the
draft). The model runs add the LocAgent coverage and the per-technique matrix.

## Missing — study level

| # | Item | Phase | Effort |
|---|---|---|---|
| G1 | **Decided 2026-10-30:** MAP (AP per bug) is the primary outcome; complete-fix recall@10, MRR, Top-k secondary; AP@10 whenever LocAgent is compared. In the draft, `evaluate.py` (ap10) and `obj2_stats.py`. | settled |
| G2 | ~~Boundary-sensitivity table on the label instead of the broad grain.~~ **Done** — recomputed (`boundary_sensitivity.csv` has grain columns); range now 8.2–41.3 %. | A | done |
| G3 | Two-person agreement on the 50-bug sample (Cohen's κ). | human | 1 day |
| G4 | Citations to find/verify: multi-hunk fix characterisation; xLoc; polyglot regression-test selection; that the ICPC 2026 "ground-truth documents" paper is CogniGent; Fejzer et al. volume/pages. | writing | ½ day |
| G5 | Study-design figure. | writing | ½ day |
| G6 | **Decided 2026-10-30:** LocAgent runs on the Python projects only, with the 7B fine-tuned model; Java is reported as infeasible (no port). In the draft. | settled |
| G7 | Author list: the brief's header reads "Eashaan Rao and Raghavendra"; the draft uses Rao and Chimalakonda as in Objective 1. Confirm. | you | — |
| G8 | ~~RQ1 on the removed bugs.~~ **Done; decided 2026-10-30: separate analysis, never pooled with the kept bugs.** — 15.9 % Poly-fix among removed vs 27.4 % kept; 24.8 % pooled (`results/obj2/removed/`). In the draft. | A | done |
| G9 | Tangling: `tangled_flag` currently marks merge commits only (82 kept bugs; 120 before the keep filter). S4 needs a real definition (e.g. merge commits + a manual audit of ~30 Poly-fix commits) or should be dropped. | A + human | ½ day + audit |
| G10 | Exhaustive literature pass and sheet (brief, research task 9). | writing | 2–3 days |
| G11 | ~~Class proportions per split.~~ **Done** — `results/obj2/stats/split_composition.csv` (written by `obj2_stats.py`). | A | done |
| G12 | Cost table per technique (training time, scoring time, GPU-hours) — TOSEM reviewers ask for it; the manifests already record it. | after runs | — |
| G13 | Older docs (PROGRESS.md, CLASSIFICATION_RULES.md, results/obj2/tables) still show the label count (1 033) in the "Poly" column; the paper now uses the broad grain. Align. | A | 30 min |

## Extra — candidates to cut or move to an appendix

| # | Item | Suggestion |
|---|---|---|
| X1 | Text universe T (sensitivity S3). | Appendix only. |
| X2 | BLAZE in the parseable view. BLAZE ingests everything; restricting it to parseable files answers nothing new. BM25-parseable is the useful control (it isolates the "fewer candidates" effect). | Drop BLAZE-parseable from the paper. |
| X3 | FLIM-fallback (our extension). | Keep, but only in RQ4 as "what representing unparseable files as text recovers". |
| X4 | The retrieval-recall supplementary figure (FAISS top-K) from the September design. | Drop: there is no retrieval stage. |
| X5 | COOBA references in older docs. | Already out of the paper; remove from docs. |

## Added after Phase A/B work (2026-10-30)

| # | Item | Status |
|---|---|---|
| G14 | LocAgent's BM25 index also **excludes test files** (`**/test/**`, `**/tests/**`, `test_*.py`); Python test GT files are reachable only through its graph tools. In the draft; it interacts with S1 (no-tests ground truth). | noted |
| G15 | **Settled by the trial (2026-10-30):** the 32B model does not fit (OOM while loading with FP8: 39.5 GiB + 4.9 GiB of another user's processes on the 44.4 GiB card). The 7B model (bf16, 14.4 GiB, 128k context) runs: 3 trial bugs in 9.3 min with one process, all three with a ground-truth file at rank 1. | settled: 7B |
| G16 | LocAgent samples at temperature 1.0 (its default): runs are not deterministic. Report one run; repeat on a subset to show spread. | decision |
| G17 | Language justification strengthened (field's benchmarks are Java/Python; parser-dependent techniques built for them; static + dynamic). Note: in BeetleBox C++ (5 268 bugs) and JavaScript (3 783) are *not* smaller than Java (3 707) / Python (3 759) — exclusion is by design, not for lack of data. | done |
| G18 | Pilot finding (localstack): 93 % of Poly-fix secondary files are test snapshots; the BM25-vs-FLIM inversion disappears without tests (S1). → Poly-fix split behaviour-bearing / test-asset-only added (D11); 55.9 % of Poly-fix bugs are test-asset-only. In the draft. | done |
| G19 | LR selection: one rule for both neural techniques, validation MAP (D10). In the draft and code; pilot rerun needed for BLAZE/FLIM (old pilot scores archived in `results/obj2/scores_archive/pilot_v1_2026-10-30/`). | done |
| G20 | Shared GPU: BLAZE needs > 23 GiB (waits for 30 GiB), FLIM 12, LocAgent-7B 24; the driver and LocAgent script wait and retry on OOM. Another user's process currently holds 20–43 GiB — the full run's duration depends on it. | open (scheduling) |
| G21 | Category (c) no-primary fixes (984, 21.5 % of bugs with counted files) added as a stratum (D14). In the draft (dataset, RQ2, evaluation). | done |
| G22 | The localstack FLIM/BLAZE pilot runs finished before model saving existed, so their models are not stored. Their scores are valid; models only matter if a new stratum must later be scored by them (localstack has 1 no-primary test bug). Re-running costs ~7 GPU-hours. | accepted (decide if needed) |

