# Threats to validity

Drafted early (per the brief). Each threat has a pre-defined mitigation.
Updated 2026-10-17 for the journal design (docs/JOURNAL_PLAN.md v2).

## Construct validity

- **Fix composition vs localization ground truth.** The Mono/Poly class and the
  evaluation ground truth now come from the same source: the fix commit's files
  under the frozen ruleset (`Scripts/bugs.eval_ground_truth`). BeetleBox's own
  `ground_truth_files` equal the commit files for 3 585 / 3 594 kept bugs but
  include changelog fragments and docs that the class excludes; using them would
  let the target and the class disagree.
- **Extension-based language attribution.** A file's language is inferred from its
  extension. Mitigation: stated as an assumption; the attribution table is
  published; ambiguous / no-extension files have explicit rules.
- **Boundary-rule sensitivity.** The prevalence figure depends on how generated,
  vendored, lock, documentation and test-data files are treated. Mitigation:
  `boundary_sensitivity.py` reports the prevalence as a range; the experiments use
  the broad grain and report headline / strict as sensitivity.
- **Rule readings that can be argued (50-bug check, 2026-11-03).** Annotators
  applied the frozen rules exactly as the ruleset does, but questioned three
  intents: airflow's `scripts/ci/` is not CI config, non-docs files under
  `docs/` count, checkstyle-style lint XML counts. Amending all three would
  change the training positives of ≤ 21 / 3 593 kept bugs (0.6 %) and the
  Poly-fix label of ≤ 14 / 984 (1.4 %). Mitigation: kept frozen (amending after
  results is a researcher degree of freedom); counts reported
  (`results/obj2/annotation/v2/reconciliation.md`, `Scripts/annotation_impact.py`).
- **Test scope by path.** `is_test` (S1 no-tests view, Poly sub-type) matches
  test directory names anywhere in the path, so test-harness code under
  `src/main/` in a `test` package is test-scoped (96 primary-language GT files,
  e.g. elasticsearch `test/framework/`). It never affects training.
- **Agreement check by AI annotators.** Two isolated AI annotators agreed with
  each other and the ruleset (κ 1.0 on label, keep and counts); same-model
  agreement is not human agreement. Mitigation: the human two-person round
  uses the same package and the revised protocol, and is what the paper reports.
- **Parseability is measured with one parser per language** (CPython `ast`,
  tree-sitter-java). A file another parser could read counts as unparseable here.
  Mitigation: parse_status is recorded per file and released; `parse_error` is
  reported separately from `no_parser` (implementation vs technique).

## Internal validity

- **Data leakage: BeetleBox was built alongside BLAZE.** Mitigation: BLAZE is
  trained from the public CodeSage-small checkpoint (not BLAZE's released
  BeetleBox-trained weights), reported in its own tables and never aggregated
  with the other techniques.
- **Temporal leakage.** Chronological split per project with purging: training
  bugs fixed after the validation period started, and validation bugs fixed after
  the test period started, are dropped (`Scripts/bugs.chrono_split`). History
  features use only fixes strictly before the query's report date.
- **Report lookup.** `bug_id` is not unique across repositories; all lookups are
  by `(repo_name, bug_id)` with a one-to-one assertion. (The pre-October driver
  queried 20.8 % of bugs with another project's report; those results are
  discarded.)
- **No retrieval stage.** Every technique scores every text file of the pre-fix
  snapshot; a single evaluator ranks them with expected ranks under random
  tie-breaking. Ground-truth files the fix adds are unreachable and reported per
  class, not counted as misses.
- **Dataset filter: BeetleBox removed reports that name a fixed file**
  (`BeetleBoxRemoved`; 1 226 from our six projects). This removes bugs where
  lexical matching is easiest and may bias the classical-vs-parsing comparison
  against BM25. Mitigation (planned, E2): classify and evaluate the removed bugs
  as a separate stratum.
- **Reimplementation fidelity.** Both neural techniques follow their original code
  (BLAZE: Zenodo 15122980, `main-sage.yaml`; FLIM: `flim-main`). Stated
  deviations: BLAZE — in-batch hard-example weighting instead of the GPT-mined
  hard-example set, no comment stripping, LR selected on validation if the paper
  value under-fits; FLIM — positives are the functions the fix changed, no
  CodeSearchNet MIX data, IR feature f2 (JDK API) dropped, other positives of the
  same report masked in the in-batch loss. Each is listed in the method.
- **Training budget and model selection.** Each neural technique is trained up to
  its paper's epoch count (BLAZE 15, FLIM 10) and selected on the same
  chronological validation split by its own original criterion (BLAZE: validation
  loss; FLIM: validation MRR), with the same patience (3). Epochs run, best epoch
  and the per-epoch curves are in every run manifest.
- **Seed variance.** Three seeds per neural technique; per-bug metrics averaged
  over seeds; across-seed SD reported.
- **The parseable-only view mixes two effects** (fewer distractors, unreachable
  ground truth). Mitigation: reach@parse, primary-only and secondary-only metrics
  reported separately.
- **More ground-truth files make Top-k easier.** Poly-fix bugs have more GT files.
  Mitigation: `n_gt_reach` covariate, per-bug random baseline.
- **Commit tangling.** Fix commits that also contain refactors inflate the
  changed-file set. Mitigation: `tangled_flag`; manual audit of ~30 Poly-fix
  commits; report the tangled proportion.
- **Feasibility: technique vs implementation.** A parse failure may reflect the
  approach or only this codebase. Mitigation: every failure is attributed to one
  or the other with the rule stated; implementation versions recorded.
- **One parsing technique.** FLIM only (BL-GAN optional, E3). Mitigation: the
  feasibility matrix is architecture-level; BL-GAN's parser behaviour is recorded
  even if it is not run end to end.
- **Pre-training exposure.** CodeSage and CodeBERT were pre-trained on public
  GitHub code that may include these repositories (code only, no fix links).
  For an LLM-agent arm (E1) this becomes a contamination threat and is measured
  with a closed-book probe.

- **Small validation set for liquibase.** The same split rule for every project leaves
  liquibase 10 (fold 1) and 8 (fold 2) validation bugs after purging (other projects
  21–48), so its LR choice and stopping epoch are noisier. Mitigation: rule not changed
  per project (D18); liquibase is one of the three extra-seed projects, so the
  seed spread reports the instability directly.

## External validity

- **Single dataset (BeetleBox).** The only public dataset with multi-language fix
  ground truth. Acknowledged; not mitigable.
- **Two languages, six projects, purposive selection.** Generalisation claimed
  narrowly. See `PROJECT_SELECTION.md`.
- **Small per-project test sets.** 17–63 Poly-fix test bugs per project in fold 1.
  Mitigation: pooled mixed-effects models are the primary inference; fold 2
  (rolling origin) roughly doubles the Poly-fix test set.
- **Recency of the parsing techniques.** FLIM is 2022. LLM-agent localizers
  (LocAgent, CoSIL, OrcaLoca; 2025) are structure-indexed in the same sense and
  are covered by the agent arm if E1 is taken.
