# Human two-person round: results and reconciliation (2026-11-22)

Same sample as the AI round: 50 bugs, 178 fix files, ruleset 0.2.0, protocol
rev. 2.1. Two annotators, working independently in Excel
(`returned/annotation_{A,B}.xlsx`); scored with
`Scripts/annotation_workbook.py import --force` (`agreement_report.md`).

## Agreement

| | label | keep | secondary languages | poly sub-type | file `counts` | excluded_reason, language, category, is_test |
|---|---|---|---|---|---|---|
| A vs B | 100% (κ 1.00) | 100% (κ 1.00) | 100% | 100% | 97.8%, 174/178 (κ 0.93) | 100% |
| A vs ruleset | 100% | 100% | 100% | 100% | 97.8% (κ 0.93) | 100% |
| B vs ruleset | 100% | 100% | 100% | 100% | 100% | 100% |

Pass criterion (κ ≥ 0.80 on the bug label and on file `counts`): **met**.
No disagreement concerns a primary-language file or a bug's keep decision, so
none has training impact.

## The four disagreements: annotator slips (evaluation impact only)

| bug | file | A | B and ruleset |
|---|---|---|---|
| elasticsearch 95522 | `x-pack/plugin/core/src/main/resources/logs-json-message-pipeline.json` | counts = no | yes (JSON) |
| ansible 78509 | `test/integration/targets/connection_paramiko_ssh/test_connection.inventory` | no | yes (INI) |
| ansible 62411 | `lib/ansible/executor/powershell/bootstrap_wrapper.ps1` | no | yes (PowerShell) |
| airflow 31431 | `docs/apache-airflow/img/airflow_erd.sha256` | no | yes (TestData) |

In all four, A filled the same language and category as B and the ruleset,
gave no excluded_reason (no rule excludes these files), and counted the file in
A's own bug-level answers (e.g. 95522: secondary languages JSON; YAML). A's
notes ("it is a log file not a cause for a bug", "not counted") show that A
read `counts` as relevance to the bug. The rules are clear here, so these are
annotator slips (protocol §4): no rule amendment. The protocol now states
explicitly that `counts` asks only whether a boundary rule excludes the file
(clarification; rules unchanged).

## Ambiguities raised

Both annotators independently raised the readings the AI round raised: the
closed dev-tooling list (checkstyle XML counted), `scripts/ci/` not being the
CI path `.ci/`, generated files without `generated/` or `*.generated.*`,
module names ending in `-testing` not being test paths, and tooling under
`test/` being test scope. All were applied as written; they remain reported as
boundary threats, as after the AI round.

Annotator A also found that `docs/CLASSIFICATION_RULES.md` §3 listed a
"Documentation path" rule (`docs/` + docs extension) that the protocol says
does not exist. The frozen code has no such path rule (`_RE_DOCS_PATH` is
defined but never used); files with a documentation extension are excluded
wherever they are, so the row had no effect. A followed the protocol. The
document's wording was corrected; no result changes, and the ruleset stays
0.2.0.
