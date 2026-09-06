# Classification rules

**Status: DRAFT. To be frozen (Phase C) before any bug is classified.**
Every rule is stated with a decision and a rationale before it is applied.
`Scripts/classification_rules.py` is the executable form; this document and that
file must agree, and both carry `RULESET_VERSION`.

The rules carry the headline number. Every SANER objection about definitions
traces to rules being implicit. Two people apply the frozen rules to a 50-bug
sample independently; disagreements are resolved by **amending a rule**, not by
adjudicating the case.

## 1. Changed-file set

The fix commit's changed files = the diff of `fix_commit_sha` against its first
parent (`commit.stats.files`), recorded in full **before any filtering**, each
with its extension. A bug whose fix commit cannot be resolved in the local clone
is **recorded, not dropped**, and reported.

## 2. Extension and language attribution

- Extension = basename substring after the final `.`, lowercased.
- No `.` in basename → rule 6 (special names).
- Extension → language via a vendored copy of GitHub Linguist `languages.yml`,
  extended to every extension actually present in the six projects' fix files.
  Each extension is assigned one category:
  `source | data-config | build | docs | test-data | other`.
- Assumption, stated in the paper: the extension determines the language for the
  file types in scope.

## 3. Boundary rules (each: decision + rationale + sensitivity toggle)

| Category | Match (draft) | Default decision | Rationale | Toggle |
|---|---|---|---|---|
| Generated files | path contains `/generated/`, `.pb.go`, `_pb2.py`, `.g.dart`, Linguist `generated?` heuristics | **exclude** | not authored in the fix; presence is a build artefact | `INCLUDE_GENERATED` |
| Vendored dependencies | path contains `vendor/`, `third_party/`, `node_modules/`, `.venv/` | **exclude** | not the project's own code | `INCLUDE_VENDORED` |
| Lock files | `*.lock`, `package-lock.json`, `poetry.lock`, `Pipfile.lock`, `go.sum`, `yarn.lock` | **exclude** | mechanically regenerated | `INCLUDE_LOCKFILES` |
| Documentation | `.md`, `.rst`, `.adoc`, `.txt` under `docs/`, `LICENSE*`, `CHANGELOG*`, `NOTICE*` | **exclude** | not a localization target | `INCLUDE_DOCS` |
| Changelog fragments | `changelogs/fragments/*.yml` (ansible), `.changes/` | **exclude** | release-notes bookkeeping, not a fix | `INCLUDE_CHANGELOG_FRAGMENTS` |
| Test code | files under `test/`, `tests/`, `*_test.py`, `*Test.java`, `test_*.py` | **include, tagged `test`** | tests are part of many real fixes; tagging lets the paper report with and without | `EXCLUDE_TESTS` |
| Test data / fixtures | data files (`.json`, `.yml`, `.sql`, `.snapshot`, `.expected`) under a test path | **include, tagged `test-data`** | these are the multi-language part of many Poly-fix bugs | `EXCLUDE_TEST_DATA` |
| CI config | `.github/`, `.gitlab-ci.yml`, `.travis.yml`, `Jenkinsfile` | **exclude** | infrastructure, not the fix | `INCLUDE_CI` |
| Version-control artefacts | `.gitignore`, `.gitattributes`, `.mailmap` | **exclude** | not code | — |
| Binary / media | `.png`, `.jpg`, `.pdf`, `.zip`, `.jar`, `.class`, `.mp4`, ... | **exclude** | not a text localization target | — |

## 4. Classification (after rules 1–3)

Let `L` = set of languages of the in-scope files.

- `|in-scope| == 0` → **Excluded**
- no in-scope file is a `source` language → **Other-fix**
- `|L| == 1` → **Mono-fix**
- `|L| >= 2` → **Poly-fix**

`fix_primary_language` = the `source` language of the source file(s); project
language as tiebreak.

## 5. Recorded per bug

`repo_name`, `bug_id`, `fix_commit_sha`, `n_files_raw`, `files_raw` (with
extensions), `n_files_inscope`, `files_inscope`, `fix_extensions`,
`fix_languages`, `fix_primary_language`, `class`, `boundary_flags` (which rules
fired), `commit_recovered` (bool), `tangled_flag` (rule 7).

## 6. Special filenames (no extension)

`Dockerfile` → build; `Makefile`/`makefile` → build; `Jenkinsfile` → CI (exclude);
`.python-version`, `.ruby-version` → other (exclude); `requirements*.txt` → build;
anything else with no extension → `other`, tagged for manual review if it appears
in a Poly-fix.

## 7. Commit tangling

A fix commit that also touches files clearly unrelated to the report (large
refactors, unrelated features) is flagged `tangled_flag` for a manual audit of
~30 Poly-fix commits. The dataset's `ground_truth_files` remains the primary
localization ground truth; the raw commit file set is used only for composition
classification, and divergence between the two is reported.

## 8. Sensitivity

`Scripts/boundary_sensitivity.py` re-runs classification with each toggle above
flipped and reports the prevalence range and which toggles move the headline.
