# 50-bug agreement check v2 — reconciliation (2026-11-03)

Round 1 annotators: two independent AI agents (A, B), each isolated from the key,
the classifier code and the other's work (see `steps_annotator_{A,B}.md`).
Ruleset 0.2.0. Scores: `agreement_report.md`, `disagreements.csv`.
Dataset-wide impact: `amendment_impact.json` (`Scripts/annotation_impact.py`).

## Result

| Pair | Bug fields (label, keep, secondary_languages, poly_subtype) | File fields |
|---|---|---|
| A vs B | 100 %, κ 1.0 | 100 %, κ 1.0 on every field |
| A vs ruleset | 100 %, κ 1.0 | 100 % except `is_test` 99.4 % (κ 0.987) |
| B vs ruleset | 100 %, κ 1.0 | 100 % except `is_test` 99.4 % (κ 0.987) |

Pass criterion (κ ≥ 0.80 on label and counts) met. **No disagreement has
training impact**; no ruleset amendment, no re-run.

Caveat for the paper: two instances of the same model following one written
protocol are not independent in the way two people are; perfect A–B agreement
shows the protocol is executable without ambiguity on this sample, not that
humans would agree. The human two-person check (same package, protocol §3 as
revised below) is the evidence to report.

## The one disagreement

`apache/dolphinscheduler` 13945,
`dolphinscheduler-api-test/dolphinscheduler-api-test-core/src/main/java/org/apache/dolphinscheduler/api/test/core/Constants.java`:
both annotators `is_test = no`, ruleset `yes`.

- The ruleset matches the anchored pattern `(^|/)tests?/` on the **package
  directory** `…/api/test/core/`. Both annotators looked only at
  `dolphinscheduler-api-test/` (which does not match) and missed the package
  directory. The file is the API-test harness, so `yes` is also right on the
  merits.
- Resolution: **annotator slip** caused by the protocol paraphrasing the
  patterns instead of publishing them. Protocol revised (regexes published,
  "anywhere in the path, including Java package directories").
- Impact: evaluation only. `is_test` never enters training (training positives
  are the counted primary-language GT files, `Scripts/bugs.py:eval_ground_truth`);
  it drives the S1 no-tests view and the Poly sub-type. Dataset-wide, 96
  primary-language GT files are test-scoped only through a `test/` package under
  `src/main/` (e.g. ES `test/framework/src/main/java`, test harness modules).
  Reported in THREATS_TO_VALIDITY as part of the S1 definition.
- `Scripts/score_annotation.py` had tagged a primary-file `is_test` difference
  as "training"; corrected to "evaluation" for the reason above.

## Rule readings the annotators questioned (both raised the same set)

None caused a disagreement — both annotators and the ruleset applied the
written rule identically. They are places where the rule is clear but its
intent can be argued. Dataset-wide effect if the rule were amended
(3593 kept bugs, 984 kept broad Poly-fix, commit files only):

| Reading questioned | Frozen rule | Keep changes | Poly label changes | Primary GT (training) changes | Decision |
|---|---|---:|---:|---:|---|
| `scripts/ci/*` (airflow) as CI config | only `.ci/`, `.github/`, … are CI | 3 | 7 | 10 | keep frozen; threat |
| non-docs files under `docs/` (`keyword_desc.yml`, Sphinx `.py`, `.sha256`) | docs = by extension only | 7 | 5 | 11 | keep frozen; threat |
| checkstyle / forbidden-apis XML as dev tooling | dev-tooling list is closed | 0 | 2 | 0 | keep frozen; threat |
| `api-generated.ts`, `*_generated.*` as generated | only `generated/`, `*.generated.*`, … | 0 | 0 | 0 | keep frozen |
| `Dockerfile.ci` | prefix rule `dockerfile*` → Docker | — | — | — | already handled; Appendix B now lists the prefix |
| `pom.xml` = XML data-config, not build | by extension | 0 | 0 | 0 | keep; category column only |
| deleted binary → `binary` not `deletion` | first excluding step wins | 0 | 0 | 0 | clarified in protocol |
| test scope on build files (`qa/…/build.gradle`) | test scope applies to every file type | 0 | — | 0 | clarified; affects sub-type only |
| `.txt` always documentation (`ansible_test/_data/*.txt`) | by extension | — | — | 0 | keep; bug not kept anyway |
| `localstack/aws/api/*/__init__.py` scaffolded | counted (no path marker) | 0 | 0 | 0 | keep: fixes edit and commit these files, so they are real localisation targets |

Largest combined effect: ≤ 0.6 % of kept bugs' training positives and ≤ 1.4 %
of the Poly-fix label; all three amendable readings are reported as boundary
threats rather than applied, since the ruleset was frozen before results and
amending after seeing them would be a researcher degree of freedom.

## Protocol changes for the human round (docs/ANNOTATION_PROTOCOL.md)

1. Exact regexes for every path rule and the test scope; "match whole directory
   names anywhere in the path, including Java package directories".
2. Appendix B: prefix rule `dockerfile*`.
3. Explicit: no docs-*path* rule — under `docs/` the extension decides.
4. Explicit: a deleted file excluded at step 2 keeps the step-2 reason.
5. Explicit: poly_subtype looks only at grammar secondary languages; the label
   counts every counted language (INI, TestData included).
6. Worked-cases table merged from both annotators' records.
7. Time budget: 2–3 h for a person.
