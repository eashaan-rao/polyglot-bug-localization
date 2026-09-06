# Threats to validity

Drafted early (per the brief). Each threat has a pre-defined mitigation.

## Construct validity

- **Fix composition ≠ localization ground truth.** The Mono/Poly class is
  computed from the fix commit's files; the localization metrics use the
  dataset's `ground_truth_files`. The two can diverge (commit tangling, dataset
  curation). Mitigation: report the divergence rate; use `ground_truth_files` for
  metrics and the commit files only for classification.
- **Extension-based language attribution.** A file's language is inferred from its
  extension. Mitigation: stated as an assumption; the attribution table is
  published; ambiguous / no-extension files have explicit rules.
- **Boundary-rule sensitivity.** The prevalence figure depends on how generated,
  vendored, lock, documentation and test-data files are treated. Mitigation:
  `boundary_sensitivity.py` reports the prevalence as a range.

## Internal validity

- **Data leakage: BeetleBox was built alongside BLAZE.** Mitigation: BLAZE is
  reported in its own column and never aggregated with the other techniques;
  stated where techniques are introduced.
- **No retrieval stage.** The design deliberately has no FAISS/BGE top-K
  pre-filter: every technique (BM25, BLAZE, FLIM) ranks the whole pre-fix
  snapshot, so a technique is never blamed for a file a retriever failed to
  surface. Cost: full-corpus ranking is compute-heavy on large projects
  (elasticsearch ≈ 27 k files/snapshot); mitigated by per-snapshot embedding
  caching and `bm25s`. A supplementary measurement shows a BGE-code retriever
  would have had low, project-dependent recall (0.11–0.90), which is itself
  consistent with the monolingual-assumption thesis.
- **Ground-truth files absent from the buggy snapshot.** A Poly-fix fix that
  *adds* a new file (test, snapshot) means that file cannot be ranked at all in
  the pre-fix snapshot. Mitigation: such files are recorded as rank = ∞ and the
  fraction is reported per class (Poly-fix is affected more).
- **Commit tangling.** Fix commits that also contain refactors inflate the
  changed-file set. Mitigation: `tangled_flag`; manual audit of ~30 Poly-fix
  commits; report the tangled proportion.
- **Balanced-subsampling variance.** The Mono-vs-Poly comparison subsamples the
  larger class. Mitigation: repeat over K seeds/folds; report mean with a
  bootstrap confidence interval.
- **Feasibility: technique vs implementation.** A parse failure may reflect the
  approach or only this codebase. Mitigation: every failure is attributed to one
  or the other with the rule stated; implementation versions recorded.
- **One parsing technique per arm.** FLIM within-project, COOBA cross-project,
  because COOBA's adversarial-transfer architecture is mis-specified
  within-project. Mitigation: both feed the feasibility matrix (architecture-level,
  so the choice does not matter there); the split is stated.

## External validity

- **Single dataset (BeetleBox).** The only public dataset with multi-language fix
  ground truth. Acknowledged; not mitigable.
- **Two languages, six projects, purposive selection.** Generalisation claimed
  narrowly. See `PROJECT_SELECTION.md`.
- **Recency of the parsing techniques.** FLIM and COOBA are 2022/2020. The most
  recent structural technique, SemanticCodeBERT / Semantic Flow Graph (FSE 2023),
  operates at changeset granularity and is cited as motivation, not run.
