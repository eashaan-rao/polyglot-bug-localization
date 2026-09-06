# Glossary

Every term is defined here before it is used anywhere in the paper. Draft this
alongside the introduction; do not use a term in prose until it has an entry.

## Classification

- **Fix commit** — the commit recorded in the dataset as fixing a bug report
  (`fix_commit_sha`). Its changed-file set is taken as the diff against its first
  parent, before any filtering.
- **Extension** — the substring of a file's basename after its final `.`
  (lowercased). Files with no `.` in the basename are handled by explicit rule
  (see `CLASSIFICATION_RULES.md`).
- **Language attribution** — the mapping from a file to a programming language,
  decided from its extension using a vendored copy of GitHub Linguist's
  `languages.yml`. Stated as an assumption, not a fact.
- **In-scope file** — a file in the fix commit that is not excluded by a boundary
  rule (generated, vendored, lock file, documentation, ...).
- **Source-code language** — a language classified as `source` in the attribution
  table (as opposed to `data/config`, `build`, `docs`, `test-data`, `other`).
- **Primary language of a fix** — the source-code language of the source file(s)
  in the fix; the project's dataset-assigned language is the tiebreak.
- **Mono-fix** — a bug whose fix has at least one in-scope file and whose in-scope
  files all map to a single language.
- **Poly-fix** — a bug whose in-scope fix files span two or more languages.
- **Other-fix** — a bug with in-scope fix files, none of which is a source-code
  language.
- **Excluded** — a bug with no in-scope files after the boundary rules.

## Retrieval and ranking

- **No retrieval stage.** This study has no Top-K pre-filter. Each technique
  scores and ranks *every* file in the bug's pre-fix snapshot. So "retrieval
  recall" and "reranker" (below) describe the wider IRBL literature and a
  supplementary measurement, not this study's own pipeline.
- **FAISS** — a library for approximate nearest-neighbour search over dense
  vectors. Used only in the supplementary "what a retrieval stage would have
  cost" figure.
- **Full-snapshot ranking** — each technique assigns a score to every file in the
  snapshot and orders them; the ground-truth file's position in that order is its
  rank. A ground-truth file that does not exist in the pre-fix snapshot (a fix
  that adds a file) has rank ∞.
- **Retrieval recall (supplementary)** — the proportion of a bug's ground-truth
  files a hypothetical BGE+FAISS Top-K would have returned. Reported once, for
  context; not part of any research question.
- **Reranker** — in the wider literature, a technique that reorders a retrieval
  stage's Top-K. Here the techniques are rankers over the full snapshot.
- **MRR** — mean reciprocal rank: the mean over bugs of 1/(rank of the first
  ground-truth file in the ranked list), 0 if none is ranked.
- **MAP** — mean average precision: the mean over bugs of the average of the
  precision values computed at each ground-truth hit.
- **Top@k** (k = 1, 5, 10) — the proportion of bugs with at least one ground-truth
  file in the first k positions.

## Techniques

- **Classical IR technique** — treats every file as a bag of tokens; no training
  on code structure; processes any file type. Here: BM25.
- **Language-agnostic technique** — ranks raw token sequences with a learned
  model; no parser. Here: BLAZE.
- **Parsing / structure-dependent technique** — its architecture requires parsing
  a source file into a structured representation (AST, graph). Cannot represent a
  file it cannot parse. Here: FLIM, COOBA.
- **Architectural feasibility** — whether a technique can produce *any*
  representation of a file of a given type. Binary. Prior to how well it ranks it.
- **Failure mode** — the recorded reason a technique could not ingest a file:
  `no_parser`, `parse_error`, `empty_or_trivial_graph`, `oversize_or_timeout`,
  `encoding_error`.
- **Technique vs implementation** — a failure is attributed to the *technique* if
  the approach cannot represent the input in principle, and to the *available
  implementation* if only this codebase lacks the support.

## Study design

- **Within-project comparison** — Mono-fix vs Poly-fix performance measured inside
  the same project, so project characteristics are held constant.
- **Same-language cross-project arm** — training on one project and testing on
  another of the same language, to check whether a within-project gap persists
  under transfer.
- **Cold start** — localizing bugs in a project with no historical bug-fix data to
  train on.
- **Lexical gap** — the vocabulary mismatch between a natural-language bug report
  and source-code identifiers.
