# Annotation protocol — 50-bug classification agreement check

Ruleset **0.2.0** (frozen 2026-09-06). Package: `results/obj2/annotation/v2/`
(built by `Scripts/make_annotation_sample_v2.py`, seed 20261103). This protocol is
what each annotator follows; it is also the base for the human two-person check.

Protocol revision **2.1** (2026-11-03), after a first round with two isolated AI
annotators (`results/obj2/annotation/v2/reconciliation.md`): exact path
patterns published (§3 Step 1, Appendix C), `dockerfile*` prefix added to
Appendix B, five points made explicit, and a worked-cases table (§3.1) taken
from both annotators' records. The rules themselves are unchanged.

**Time budget for a person:** 2–3 hours — about 30 min reading this protocol and
CLASSIFICATION_RULES.md, 1.5 h for the 178 files (most take seconds; about 15
need thought), 30 min for the 50 bugs and the notes.

## 1. Purpose

The classification rules decide (a) whether a bug is Mono-fix, Poly-fix,
Other-fix or Excluded, (b) whether it is **kept** for the experiments, and
(c) which fix files count as ground truth. (b) and the decisions on
**Java/Python files** also feed model *training*; an error there would force
re-running the experiments, whereas an error on a secondary file only changes
labels and evaluation. The check therefore asks for decisions **per file** and
**per bug**, on a sample drawn from *all* outcomes, not only kept bugs.

Pass criterion: Cohen's kappa ≥ 0.80 between the two annotators on the bug
label, and on the per-file `counts` decision. Disagreements are resolved by
**amending a rule** (and bumping the ruleset version), never by adjudicating a
single case.

## 2. Materials

| File | Use |
|---|---|
| `bugs_blank.csv` | one row per bug (50) — fill `label, keep, secondary_languages, poly_subtype, notes` |
| `files_blank.csv` | one row per changed file (178) — fill `counts, excluded_reason, language, category, is_test, notes` |
| `docs/CLASSIFICATION_RULES.md` | the rules (sections 1–4 and the admission criteria C1–C5) |
| Appendix A below | the extension → language/category table of the frozen ruleset |
| `docs/GLOSSARY.md` | definitions |

**Human round (Excel).** For the two-person round each annotator receives one
workbook, `results/obj2/annotation/human/handout/annotation_<A|B>.xlsx`, which
holds the same 50 bugs and 178 files (sheets `1_files`, `2_bugs`), a `log`
sheet in place of `steps_<annotator>.md`, drop-down lists of the allowed
values, and copies of Appendices A–C and the worked cases. The procedure below
is unchanged; the filled workbook is returned instead of the CSV files and is
converted and scored by `Scripts/annotation_workbook.py import`
(see `results/obj2/annotation/human/README.md`).

**Do not open** `key_bugs.csv`, `key_files.csv`, `Scripts/classification_rules.py`,
`data/obj2/bug_classification.parquet`, `results/obj2/bug_classification.csv`,
or the other annotator's files. Decide from the path, the change type and the
rules only. Do not look at file contents unless a rule cannot be applied from the
path; if you do, say so in `notes`.

## 3. Procedure

Work file by file first, then derive the bug-level answers from your own file
decisions.

### Step 1 — each changed file (`files_*.csv`)

Apply the rules **in this order**; the first rule that excludes a file decides.
A renamed file (R) is judged by its new path.

**How path patterns match.** A pattern written `name/` matches a *whole
directory name* anywhere in the path — including Java package directories
(`…/org/apache/x/api/test/core/Foo.java` matches `test/`), but not part of a
longer name (`dolphinscheduler-api-test/` does not match `test/`). A pattern
written as a file name matches the *last* path component. Matching ignores case.
The exact regular expressions are in Appendix C; when in doubt, they decide.

1. **Path rules** (CLASSIFICATION_RULES.md §3, Appendix C), in this order: changelog fragment
   → lockfile → vendored → generated → CI config → dev tooling. A match gives
   `counts = no`, `excluded_reason` = `changelog_fragment` / `lockfile` /
   `vendored` / `generated` / `ci_config` / `devtooling`, `is_test = no`.
   `META-INF/services/*` → `counts = yes`, language `SPI`, category
   `data-config` (stop here; `is_test = no`).
2. **Language and category** from the extension (Appendix A), or from the
   basename for extension-less files (Appendix B); extensions are compared in
   lower case.
   - category `docs` (Markdown, reST, AsciiDoc, HTML, LICENSE, …) **or extension
     `.txt`** → `counts = no`, `excluded_reason = documentation`, `is_test = no`.
     There is **no documentation-path rule**: a `.yml`, `.py` or `.sha256` under
     `docs/` is judged by its extension like any other file.
   - category `other`, or an extension / basename in neither appendix →
     `counts = no`, `excluded_reason` = `binary`, `certificate`,
     `codegen_template` (as in Appendix A) or `unclassified` (unknown);
     `is_test = no`.
3. **Test scope** (only for files that reached this step): `is_test = yes` if
   the path matches a test pattern (Appendix C, `test path`): a directory named
   `test`, `tests`, `__tests__`, `testsuite`, `testdata`, `test-fixtures`,
   `testfixtures`, `it`, `qa`, `integration-test(s)`; or `src/test*/`,
   `src/integ*/`, `src/internalClusterTest*/`, `src/yamlRestTest*/`,
   `src/javaRestTest*/`, `src/internalTest*/`; or a file name `*Test.java`,
   `*IT.java`, `test_*.py`, `*_test.py`, `*_tests.py`, `*Spec.groovy`. It applies to
   **every file type**, build files included (`x-pack/qa/…/build.gradle` → yes);
   else `no`. Test files still count. (`*Tests.java` is not a file pattern; it
   is test only when a directory matches.)
4. **Deletion**: `change_type` = D → `counts = no`, `excluded_reason = deletion`
   (keep the language from step 2; leave `category` empty). A deleted file
   already excluded at step 1 or 2 (e.g. a deleted `.jpg`) keeps that earlier
   reason (`binary`), not `deletion`.
5. Otherwise `counts = yes`, `excluded_reason` empty, and `language` and
   `category` (source / schema / data-config / build / style / test-data) from
   step 2.

### Step 2 — each bug (`bugs_*.csv`)

From the files you marked `counts = yes`:

- **label**: no counted file → `Excluded`; counted files but none in a
  programming language (category `source`) → `Other-fix`; all counted files in
  one language → `Mono-fix`; two or more languages → `Poly-fix`.
- **keep**: `yes` if at least one counted file is in the project's primary
  language (given in the `primary_language` column), else `no`.
- **secondary_languages** (Poly-fix only): the counted languages other than the
  primary one, separated by `; ` (e.g. `JSON; YAML`).
- **poly_subtype** (kept Poly-fix only, and only if at least one secondary
  language has a formal grammar — Appendix A column "grammar"): `behaviour-bearing`
  if at least one secondary-language file has `is_test = no`, otherwise
  `test-asset-only`. Leave empty in all other cases.
  The label counts **every** counted language, INI and TestData included, so a
  bug whose only secondary language is INI is Poly-fix with an empty
  poly_subtype. A Mono-fix in a non-primary language (e.g. PowerShell only) is
  `Mono-fix`, keep `no` — do not change it to Other-fix.
- **notes**: every place where a rule was ambiguous or did not fit, with the
  rule you applied.

### Step 3 — return

Save as `bugs_<annotator>.csv` and `files_<annotator>.csv` (same columns,
`annotator` filled), plus `steps_<annotator>.md`: how you worked, how long it
took, and every ambiguity, with the file and the rule.

### 3.1 Worked cases (from round 1)

These are decisions the rules already fix but that took the round-1 annotators
thought. They are not the answers for this sample; they show how a rule applies.

| Case | Decision | Why |
|---|---|---|
| `docs/changelog/*.yaml`, `changelogs/fragments/*` | `changelog_fragment` | path rules run before the extension |
| `.github/…`, `.azure-pipelines/…` | `ci_config` | CI path |
| `scripts/ci/*.sh` (airflow) | counted, Shell | the CI pattern is the dot-directory `.ci/`; `ci/` is not CI |
| `docs/…/keyword_desc.yml`, `docs/…/x.sha256` | counted by extension (YAML; TestData) | no documentation-path rule |
| `.txt` anywhere, also data under `test/` | `documentation` | step 2, by extension |
| deleted `.jpg` | `binary` | step 2 excludes before step 4 |
| `Dockerfile`, `Dockerfile.ci` | Docker, build | Appendix B, `dockerfile*` prefix |
| `pom.xml`, `checkstyle*.xml` | XML, data-config, counted | by extension; dev-tooling list (Appendix C) is closed |
| `api-generated.ts` | counted, TypeScript | generated needs `generated/` or `*.generated.*` |
| `*.snapshot.json` | JSON | the **last** extension decides |
| `.properties`, `.inventory` | INI, data-config, counted | Appendix A |
| `…/src/main/java/…/api/test/core/Constants.java` | `is_test = yes` | package directory `test/` |
| `x-pack/qa/…/build.gradle` | Gradle, `is_test = yes` | test scope applies to every file type |
| `FooTests.java` under `src/test/` | `is_test = yes` | by directory, not by name |

Tip from round 1: work bug by bug (all files of one bug together), write a note
on every file that needed thought, then derive the bug answers from your own
file rows and re-check them once.

## 4. Scoring and reconciliation (done after both annotators finish)

`Scripts/score_annotation.py` computes, for A vs B and each vs the ruleset key:
Cohen's kappa on `label`, `keep`, `counts`; percent agreement on
`language`, `category`, `is_test`, `poly_subtype`; and lists every disagreement.

Each disagreement is classified by **impact**:

| Impact | Meaning | Consequence |
|---|---|---|
| **training** | concerns a Java/Python file's `counts` / `excluded_reason`, or a bug's `keep` | rule amendment would change training data → experiments re-run |
| **evaluation** | concerns a secondary file, any `is_test`, a label, a sub-type | rule amendment changes labels / evaluation only → no re-run |
| **annotator slip** | the rule is clear and one annotator misapplied it | no amendment |

## Appendix A — extension → language, category (ruleset 0.2.0)

| language | category | grammar (C1–C3) | extensions |
|---|---|---|---|
| Autotools | build | yes | .in |
| Docker | build | yes | .dockerfile |
| Gradle | build | yes | .gradle |
| Installer | build | yes | .install4j |
| MSBuild | build | yes | .csproj, .sln, .vcxproj |
| ACL | data-config | no | .acl |
| CSV | data-config | no | .csv |
| Env | data-config | no | .env |
| INI | data-config | no | .cfg, .cnf, .conf, .config, .ini, .inventory, .properties |
| JSON | data-config | yes | .json, .json5 |
| Jinja | data-config | yes | .j2, .jinja2 |
| Policy | data-config | yes | .policy |
| TOML | data-config | yes | .toml |
| Template | data-config | yes | .mustache, .tpl |
| Terraform | data-config | yes | .tf, .tfvars |
| XML | data-config | yes | .xml |
| YAML | data-config | yes | .kubernetes-helm-yaml, .yaml, .yml |
| AsciiDoc | docs | no | .adoc, .asciidoc |
| HTML | docs | no | .htm, .html |
| Markdown | docs | no | .markdown, .md |
| SphinxInventory | docs | no | .inv |
| Text | docs | no | .txt |
| reST | docs | no | .rst |
| Binary | other | no | .class, .gif, .gz, .ico, .jar, .jpeg, .jpg, .mkv, .mp4, .pdf, .png, .svg, .tgz, .war, .zip |
| Cert | other | no | .crt, .key, .pem |
| CodegenTemplate | other | no | .st |
| ANTLR | schema | yes | .g4 |
| JavaCC | schema | yes | .jj |
| Protobuf | schema | yes | .proto |
| SQL | schema | yes | .sql |
| XML-Schema | schema | yes | .xsd |
| Batch | source | yes | .bat, .cmd |
| C# | source | yes | .cs |
| Cython | source | yes | .pyx |
| Go | source | yes | .go |
| Groovy | source | yes | .groovy |
| Java | source | yes | .java |
| JavaScript | source | yes | .cjs, .js, .jsx, .mjs |
| Kotlin | source | yes | .kt, .kts |
| PowerShell | source | yes | .ps1, .psm1 |
| Python | source | yes | .py, .pyi |
| Ruby | source | yes | .rb |
| Scala | source | yes | .scala |
| Shell | source | yes | .bash, .sh |
| TypeScript | source | yes | .cts, .mts, .ts, .tsx |
| Vue | source | yes | .vue |
| CSS | style | yes | .css, .less, .scss |
| TestData | test-data | no | .ambr, .csv-spec, .expected, .golden, .interp, .sha1, .sha256, .snap, .sql-spec, .stderr, .stdout |

## Appendix B — extension-less basenames

| basename | language | category |
|---|---|---|
| `dockerfile` | Docker | build |
| `makefile` | Make | build |
| `manifest.in` | Autotools | build |
| `jenkinsfile` | CI | ci |
| `vagrantfile` | Ruby | build |
| `license` | License | docs |
| `notice` | License | docs |
| `changelog` | Changelog | docs |
| `readme` | Doc | docs |
| `codeowners` | VCS | vcs |
| `dockerfile*` (prefix: `Dockerfile.ci`, `Dockerfile.base`) | Docker | build |

## Appendix C — path patterns (ruleset 0.2.0, exact)

Python regular expressions, case-insensitive, searched in the full path.
`(^|/)` means "at the start or after a `/`", i.e. a whole directory name.

| Rule | Regex |
|---|---|
| changelog fragment | `(^\|/)(changelogs?/fragments?\|newsfragments\|\.changes\|docs/changelog\|docs/release-notes\|release_notes)/` |
| lockfile | `(^\|/)(package-lock\.json\|yarn\.lock\|pnpm-lock\.yaml\|poetry\.lock\|Pipfile\.lock\|Cargo\.lock\|go\.sum\|composer\.lock\|Gemfile\.lock)$\|\.lock$` |
| vendored | `(^\|/)(vendor\|third_party\|third-party\|node_modules\|\.venv\|bundled\|external)/` |
| generated | `(^\|/)generated/\|(\.pb\.go\|_pb2\.pyi?\|\.g\.dart\|\.generated\.[A-Za-z]+\|\.java\.st\|\.designer\.cs)$` |
| CI config | `(^\|/)(\.github\|\.gitlab\|\.azure-pipelines\|\.circleci\|\.buildkite\|\.ci)/\|(^\|/)(\.gitlab-ci\.yml\|\.travis\.yml\|azure-pipelines\.yml\|appveyor\.yml\|\.pre-commit-config\.ya?ml\|Jenkinsfile[^/]*)$` |
| dev tooling | `(^\|/)(\.flake8\|\.coveragerc\|\.editorconfig\|\.eslintrc[^/]*\|\.eslintignore\|\.prettierrc[^/]*\|\.prettierignore\|\.babelrc[^/]*\|\.stylelintrc[^/]*\|\.rat-excludes\|\.dockerignore\|\.gitattributes\|\.gitmodules\|\.gitignore\|\.mailmap\|\.npmignore\|\.yamllint\|tox\.ini\|setup\.cfg\|mypy\.ini\|sanity\.[^/]*\.in\|constraints\.txt\|\.env(\.[^/]*)?)$` |
| SPI | `(^\|/)META-INF/services/` |
| test path | `(^\|/)(tests?\|__tests__\|testsuite\|testdata\|test-fixtures\|testfixtures\|it\|qa\|integration-tests?)/\|(^\|/)src/(test\|integ\|internalClusterTest\|yamlRestTest\|javaRestTest\|internalTest)[A-Za-z]*/\|(_test\.py\|_tests\.py\|test_[^/]*\.py\|[A-Za-z0-9]+Test\.java\|[A-Za-z0-9]+IT\.java\|[A-Za-z0-9]+Spec\.groovy)$` |
