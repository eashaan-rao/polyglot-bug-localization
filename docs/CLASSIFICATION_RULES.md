# Classification rules

**Status: DRAFT v0.1.0 — to be frozen (Phase C) with the advisor before any bug
is classified.** `Scripts/classification_rules.py` is the executable form; this
document and that file must agree, and both carry `RULESET_VERSION`.

The rules carry the headline number. Every SANER objection about definitions
traces to rules being implicit. Two people apply the frozen rules to a 50-bug
sample independently; disagreements are resolved by **amending a rule**, not by
adjudicating the case.

Numbers below are from a dry run over all **4995** BeetleBox bugs in the six
projects (100% fix-commit recovery).

---

## 1. Changed-file set

The fix commit's changed files = the diff of `fix_commit_sha` against its first
parent (empty tree for a root commit). Recorded in full **before any filtering**,
each with its extension and change type (A/M/D/R). A merge fix commit
(2.4% of bugs) is diffed against its first parent. A bug whose fix commit cannot
be resolved is **recorded, not dropped** (0 such bugs here).

Purely-**deleted** files do not count toward composition by default
(`COUNT_DELETIONS` toggle; effect is < 0.1 pp).

## 2. Language attribution

Extension → `(language_id, category)` via the table in
`classification_rules.py::EXT_LANG`, seeded from GitHub Linguist and extended to
every extension present in the six projects' fix files. Dialect variants collapse
to one `language_id` (`yml`+`yaml`→YAML, `ts`+`tsx`→TypeScript, `py`+`pyi`→Python,
`js`+`jsx`+`mjs`+`cjs`→JavaScript). Files with no usable extension are matched by
basename (`Dockerfile*`, `Makefile`, `MANIFEST.in`, `Jenkinsfile`, `LICENSE`, …).

**Categories** and whether they count toward the Mono/Poly language set in the
**headline** configuration:

| Category | Counts? | Members (examples) |
|---|---|---|
| `source` | yes | Python, Java, TypeScript, JavaScript, Vue, Groovy, Shell, PowerShell, C#, Go, Ruby, Batch |
| `schema` | yes | SQL, `.xsd`, `.g4` (ANTLR), `.jj` (JavaCC), `.proto` |
| `data-config` | yes | YAML, JSON, XML, TOML, INI/`.cfg`/`.conf`/`.properties`, Jinja (`.j2`), Terraform, `.policy`, SPI (`META-INF/services/*`) |
| `build` | yes | Gradle, Dockerfile, Make, `MANIFEST.in`, MSBuild (`.csproj`/`.sln`), install4j |
| `style` | yes | CSS / SCSS / LESS |
| `test-data` | yes (tagged) | `.csv-spec`, `.sql-spec`, `.expected`, `.stdout`, `.stderr`, `.sha1/.sha256`, `.snap`, `.interp` |
| `docs` | **no** | Markdown, reST, AsciiDoc, HTML, plain `.txt`, `.inv`, `LICENSE`, `NOTICE`, `CHANGELOG`, `README` |
| `other` | no | binaries, media, certs, codegen templates (`.java.st`), unclassified |

## 3. Path rules (applied before the extension map)

| Rule | Match (regex in `classification_rules.py`) | Default | Toggle |
|---|---|---|---|
| Changelog fragment | `changelogs/fragments/`, `docs/changelog/`, `newsfragments/`, `.changes/` | **exclude** | `INCLUDE_CHANGELOG_FRAGMENTS` |
| Lock file | `package-lock.json`, `yarn.lock`, `poetry.lock`, `go.sum`, `*.lock` | **exclude** | `INCLUDE_LOCKFILES` |
| Vendored | `vendor/`, `third_party/`, `node_modules/`, `.venv/` | **exclude** | `INCLUDE_VENDORED` |
| Generated / codegen | `generated/`, `*.pb.go`, `*_pb2.py`, `*.java.st`, `*.generated.*` | **exclude** | `INCLUDE_GENERATED` |
| CI config | `.github/`, `.gitlab-ci.yml`, `.azure-pipelines/`, `Jenkinsfile`, `.pre-commit-config.*`, `.ci/` | **exclude** | `INCLUDE_CI` |
| Dev tooling | `.flake8`, `.coveragerc`, `.editorconfig`, `.eslint*`, `.prettier*`, `.babelrc`, `tox.ini`, `setup.cfg`, `.gitignore`, `.gitattributes`, `.gitmodules`, `sanity.*.in` | **exclude** (no toggle) | — |
| SPI registration | `META-INF/services/` | keep as `data-config` | — |
| Documentation path | `docs/`, `documentation/`, `site/` + a docs extension | **exclude** | `INCLUDE_DOCS` |
| Test scope | `test/`, `tests/`, `qa/`, `testFixtures/`, `src/test/`, `src/yamlRestTest/`, `*Test.java`, `*IT.java`, `test_*.py`, `*_test.py`, `*Spec.groovy` | **keep, tag `test` / `test_asset`** | `EXCLUDE_TESTS` |

## 4. Classification

After rules 1–3, let `L` = set of `language_id`s of the files that count.

- `|counting files| == 0` → **Excluded**
- no counting file is a programming language (`source`) → **Other-fix**
- `|L| == 1` → **Mono-fix**
- `|L| >= 2` → **Poly-fix**

`fix_primary_language` = a `source` language of the fix; the project's own
language (Java / Python) breaks ties.

## 5. Sensitivity toggles → prevalence reported as a range

Dry-run prevalence over the 4995 bugs (Poly-fix as a share of Mono+Poly):

| Toggle set | Mono | Poly | Other | Excl | Poly-fix % |
|---|---|---|---|---|---|
| **headline** (all toggles off) | 3082 | 1121 | 374 | 418 | **26.7 %** |
| `strict_source_only` (Poly needs ≥2 *programming* languages) | 3884 | 319 | 0 | 792 | 7.6 % |
| `exclude_tests` | 3460 | 472 | 343 | 720 | 12.0 % |
| `include_changelog_fragments` | 2604 | 1599 | 392 | 400 | 38.0 % |
| `include_docs` | 3082 | 1121 | 374 | 418 | 26.7 % (no change) |
| `collapse_data_config` (all data/config = one language) | 3082 | 1121 | 374 | 418 | 26.7 % (no change) |
| `count_deletions` | 3077 | 1127 | 374 | 417 | 26.8 % |

Read: the headline figure is **robust to how documentation and data-config
sub-types are treated** (no change). It is **sensitive to two choices** — whether
test code/data counts (26.7 % → 12.0 %) and whether changelog fragments count
(26.7 % → 38.0 %) — and to the strict "two programming languages" reading
(→ 7.6 %). The paper reports **26.7 % [7.6 % – 38.0 %]** and names the two
load-bearing rules.

## 6. Per-project (headline)

| Project | Mono | Poly | Other | Poly-fix % | min class n |
|---|---|---|---|---|---|
| ansible/ansible | 359 | 278 | 23 | 43.6 % | 278 |
| apache/airflow | 821 | 195 | 60 | 19.2 % | 195 |
| apache/dolphinscheduler | 944 | 238 | 121 | 20.1 % | 238 |
| elastic/elasticsearch | 567 | 157 | 126 | 21.7 % | 157 |
| liquibase/liquibase | 103 | 100 | 30 | 49.3 % | 100 |
| localstack/localstack | 293 | 148 | 12 | 33.6 % | 148 |

Every project has ≥ 100 bugs in its smaller class → a within-project
Mono-vs-Poly comparison with balanced subsampling is viable for all six.

## 7. Secondary languages in headline Poly-fix (bug counts)

YAML 511 · JSON 174 · XML 122 · Shell 101 · Groovy 72 · INI 53 · TypeScript 51 ·
JavaScript 43 · Vue 39 · TestData 38 · CSS 36 · Gradle 33 · Docker 24 · SQL 19 ·
Jinja 18 · PowerShell 9 · Make 7 · (rest ≤ 5)

## 8. Open decisions for the freeze (Phase C, with advisor)

1. **Shell / Groovy as `source`.** A `.py` + test `.sh` fix is currently
   Poly-fix, and counts as two programming languages under `strict_source_only`.
   Keep (they are languages an AST tool cannot parse) or demote to a
   `script`/`build` category that the strict reading ignores? 101 Shell + 72
   Groovy Poly-fix bugs ride on this.
2. **`.gradle` = Gradle (build), not Groovy.** Currently `build`, so it counts in
   the headline but not under `strict_source_only`. Agreed?
3. **Test scope regex.** Confirm the ES `src/yamlRestTest/…` and ansible
   `test/integration/targets/…` patterns are complete.
4. **`Other-fix` handling.** 374 bugs have only non-programming files
   (config/schema only). Report as a third class, or fold into "not analysed"?
5. **`strict_source_only`** — is this a reported sensitivity row, or the paper's
   *secondary headline* (the "language-specific model" reading)?
