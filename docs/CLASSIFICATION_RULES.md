# Classification rules

**Status: DRAFT v0.2.0 — to be frozen (Phase C) with the advisor.**
`Scripts/classification_rules.py` is the executable form; this document and that
file must agree, and both carry `RULESET_VERSION`. Numbers below are from
`classify_bugs.py` / `boundary_sensitivity.py` over all 4995 bugs.

## Secondary-language admission (advisor decision)

A file type in a fix counts as a **second language** only if it passes:

- **C1 formal grammar** — a parser for it could exist. Rejects `.ini` / `.cfg` /
  `.properties` (key–value *format*), plain-text `.expected` / `.stdout`
  fixtures, `META-INF/services` class lists, `.csv`.
- **C2 not parseable by the evaluated AST techniques** — not Java, not Python
  (FLIM / COOBA / BL-GAN parse only these two).
- **C3 behaviour-bearing** — encodes behaviour, expected output, a schema, or
  build/deploy wiring; a thing a developer edits *to fix a bug*. Rejects docs,
  changelog fragments, licences, `.gitignore`, CI config (handled by boundary
  rules).
- **C4 attested** — the file appears in the dataset's own `ground_truth_files`
  for ≥1 bug. In this dataset **every** counted secondary file is also a
  ground-truth target.
- **C5** (per-type stats only) ≥15 Poly-fix bugs across ≥2 projects.

C1+C3 ⇔ membership of `GRAMMAR_LANGUAGES` in `classification_rules.py`.

**Three reported grains** (a bug can be in several):

| grain | secondary must be… | pooled Poly-fix % (kept set) | N |
|---|---|---|---|
| **headline** | YAML, JSON, XML, or SQL (also pass C5) | **21.0 %** | 754 |
| **broad** (operational) | any `GRAMMAR_LANGUAGES` member (adds build scripts, 2nd programming language, Shell, Jinja, grammars) | **27.4 %** | 985 |
| **strict** | the fix spans ≥ 2 *programming* languages | **8.2 %** | 294 |

`broad` includes Shell (101 bugs, mostly test glue); `broad` − Shell ≈ 884.
48 Poly-fix bugs are `tier3_only` (only a non-grammar secondary) → in none of
the grains, flagged.

## Bug-level keep filter

Keep a bug only if its fix touches ≥ 1 file in the **project's primary language**
(Java for the JVM repos, Python for the Python repos), so the parsing technique
always has a parseable localization target. → **3594 / 4995 kept (72 %)**;
`Other-fix` becomes empty by construction.

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

`boundary_sensitivity.py`, Poly-fix (raw label, any ≥2 languages) as a share of
Mono+Poly in the kept set:

| Toggle set | Mono | Poly | Poly-fix % | Δ vs headline |
|---|---|---|---|---|
| **headline** | 2561 | 1033 | **28.7 %** | — |
| `strict_source_only` (≥2 programming languages) | 3300 | 294 | 8.2 % | −20.5 pp |
| `exclude_tests` | 2937 | 387 | 11.6 % | −17.1 pp |
| `include_changelog_fragments` | 2087 | 1507 | 41.9 % | +13.2 pp |
| `include_docs` | 2561 | 1033 | 28.7 % | 0.0 |
| `collapse_data_config` | 2561 | 1033 | 28.7 % | 0.0 |
| `count_deletions` | 2558 | 1037 | 28.8 % | +0.1 pp |

The figure is **robust to documentation and data-config treatment** (no change).
It is **sensitive to three choices**: whether test code/data counts
(28.7 % → 11.6 %), whether changelog fragments count (→ 41.9 %), and the strict
"two programming languages" reading (→ 8.2 %). The paper reports the operational
(broad-grain) figure with the range **[8.2 % – 41.9 %]** and names these rules.

## 6. Per-project (kept set)

| Project | kept | Mono | Poly | headline % | broad % | strict % | smaller class n |
|---|---|---|---|---|---|---|---|
| elastic/elasticsearch | 721 | 564 | 157 | 15.1 % | 17.8 % | 0.3 % | 157 |
| liquibase/liquibase | 199 | 99 | 100 | 20.1 % | 49.7 % | 35.7 % | 99 |
| apache/dolphinscheduler | 698 | 523 | 175 | 14.6 % | 23.6 % | 10.7 % | 175 |
| ansible/ansible | 626 | 352 | 274 | 39.1 % | 43.5 % | 13.4 % | 274 |
| apache/airflow | 917 | 739 | 178 | 14.2 % | 18.8 % | 5.5 % | 178 |
| localstack/localstack | 433 | 284 | 149 | 29.6 % | 34.4 % | 2.8 % | 149 |
| **POOLED** | 3594 | 2561 | 1033 | 21.0 % | 27.4 % | 8.2 % | — |

Every project has ≥ ~100 bugs in its smaller class → balanced within-project
comparison viable for all six. Per-project character: ES = YAML test specs +
`build.gradle`; liquibase = Java+Groovy + XML/SQL; dolphinscheduler = XML +
frontend TS/Vue + SQL; ansible = YAML playbooks; airflow = mixed config;
localstack = JSON snapshots (the motivating example).

## 7. Secondary languages in Poly-fix (kept set, bug counts)

YAML 497 (6 proj) · JSON 163 (6) · XML 117 (4) · Shell 101 (5) · Groovy 72 (2) ·
TypeScript 47 (2) · JavaScript 43 (3) · Gradle 33 (1) · SQL 19 (2) · Vue 19 (1) ·
Jinja 18 (2) · Docker 14 (3) · Python 13 (1) · PowerShell 8 · Java 7 · Make 6 ·
XML-Schema 5 · (rest ≤ 3). Every one is also a ground-truth localization target.

## 8. Decisions taken (advisor-confirmed) and still open

**Taken:**
- Secondary-language admission = criteria C1–C4 (§ top). INI/properties,
  plain-text fixtures, SPI lists, CSV are **not** languages.
- Three reported grains: headline (YAML/JSON/XML/SQL), broad (any grammar
  language — the operational definition), strict (≥2 programming languages).
- Bug-level keep filter: fix must touch the project's primary language →
  `Other-fix` is filtered out, not a third analysed class.
- Shell / Groovy stay as languages with a grammar (→ in `broad`); Shell is
  reported separately so a reader can subtract it.
- `.gradle` → language "Gradle", category `build` (counts in broad, not strict).
- Java / Python **can** be a secondary language (`.java`+`.py` fixes: 20 bugs) —
  these land in `strict` and test mixed-corpus degradation, a *different*
  mechanism from the unparseable-file case; analysed as their own sub-set.

**Still open for the freeze:**
1. Test-scope regex completeness — confirm ES `src/yamlRestTest/…`,
   `src/internalClusterTest/…` and ansible `test/integration/targets/…` are all
   covered (spot-check in the 50-bug review).
2. Which grain is *the* headline number in the abstract — recommend **broad**
   (operational, 27.4 %) with headline (21.0 %) and strict (8.2 %) as reported
   cuts.
3. Second annotator for the 50-bug agreement check.
