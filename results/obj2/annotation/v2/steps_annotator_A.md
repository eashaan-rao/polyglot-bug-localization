# Annotator A: how the 50-bug check was done

Ruleset 0.2.0. Annotator A (an AI agent working on its own without seeing Annotator B).
Outputs: `files_annotator_A.csv` (178 rows) and `bugs_annotator_A.csv` (50 rows), both in this folder.

## 0. Isolation

- Rule sources read: `docs/ANNOTATION_PROTOCOL.md`, `docs/CLASSIFICATION_RULES.md`, `docs/GLOSSARY.md`. Nothing else.
- Inputs read: `bugs_blank.csv` and `files_blank.csv`, copied to a scratch folder first; the originals were not changed.
- Not opened: the key files, any script under `Scripts/`, the parquet/CSV classification outputs, eval/stats folders, anything by annotator B.
- **No file contents in the git repositories were opened.** Every decision came from the path, the change type and the written rules.
- Python (stdlib `csv`) was used only to (a) print each bug with its changed files, (b) merge my decision table into the CSV columns, and (c) re-derive each bug label from my file decisions as an arithmetic check against the bug answers I wrote by hand (0 mismatches). The per-file decisions are a hand-written table of 178 rows, one per file, each with a note. No extension lookup was coded.

## 1. Order of work

1. Read the protocol in full (§3 procedure, Appendix A/B), then RULES §1–4 and the admission criteria, then the glossary.
2. Printed the 50 bugs, each with its files (path + change type), grouped by bug. Working bug by bug kept the context visible (e.g. what kind of commit it was).
3. **Pass over files**: for each file, applied protocol Step 1 strictly in this order:
   path rules (changelog → lockfile → vendored → generated → CI → devtooling → SPI) → extension/basename (docs/.txt → documentation; other/unknown → binary/cert/codegen/unclassified) → test scope → deletion → counted.
   Wrote counts / excluded_reason / language / category / is_test, plus a note for every file where a rule needed interpretation.
4. **Pass over bugs**: wrote label, keep, secondary_languages, poly_subtype and notes by hand from the counted files.
5. **Check**: a script re-computed the four bug fields from my file table using the Step 2 definitions; it agreed with my hand answers on all 50.
6. Wrote the CSVs, then this document.

Time: about 10–15 minutes of agent time (most of it reading the rules and deciding the edge cases). For a human I would budget **2–3 hours**: ~30 min on the rules, ~1.5 h on the 178 files (most take seconds; about 15 need thought), ~30 min on bugs and notes.

## 2. How each kind of case was handled (a guide for the human annotator)

| Case | Decision | Rule |
|---|---|---|
| `docs/changelog/*.yaml` (ES), `changelogs/fragments/*` (ansible) | no, `changelog_fragment` | §3 changelog fragment (checked first, so before the YAML extension) |
| `.github/…`, `.azure-pipelines/…` | no, `ci_config` | §3 CI config |
| `.md`, `.rst`, `.asciidoc`, `.txt` | no, `documentation`, language empty | Step 2 docs / `.txt` |
| `.png/.jpg/.svg/.mkv/.mp4` | no, `binary`, language empty | Step 2 other |
| Deleted (D) binary/doc file | reason is the Step-2 reason (`binary`), **not** `deletion` | the first excluding rule wins; Step 2 comes before Step 4. As a result `deletion` never appears in this sample |
| `pom.xml`, checkstyle `*.xml` | yes, XML, `data-config` | Appendix A maps `.xml` → data-config; no rule makes pom.xml `build` |
| `.properties`, `.inventory` | yes, INI, `data-config` | Appendix A; counts, but INI has no grammar |
| `*.snapshot.json`, `*.test.groovy` | language from the **final** extension (JSON, Groovy) | Glossary "Extension" |
| `.sql-spec`, `.sha256` | yes, TestData, `test-data` | Appendix A |
| `Dockerfile` | Docker, build | Appendix B |
| Renamed (R) file | judged by the new path | Step 1 |
| Test scope | yes for paths with a `test/`, `tests/`, `qa/`, `src/test/`, `src/yamlRestTest/` **path segment**, or names `*Test.java`, `*IT.java`, `test_*.py`, `*_test.py` | Step 3; applies to any file type (YAML, JSON, Gradle, Shell, …) |
| Secondary languages when the primary language is not counted (keep=no Poly-fix) | listed every counted language (all are "other than the primary") | Step 2 |
| poly_subtype | only for keep=yes Poly-fix; looked only at secondary files whose language has grammar=yes; behaviour-bearing if any of those is is_test=no | Step 2 |

## 3. Ambiguities and places the rules did not fit

Each one gives the file, the rule, what I did, and what would change under the other reading.

1. **`.ci/` CI-config pattern vs `scripts/ci/`**: `apache/airflow` 12509 `scripts/ci/libraries/_build_images.sh`; 10438 `scripts/ci/libraries/_initialization.sh`, `_verbosity.sh`. RULES §3 lists `.ci/` next to `.github/` and `.azure-pipelines/`, so I read it as the dot-directory `.ci/` and **did not** exclude these (Shell, counted). If the pattern is an unescaped regex `.ci/`, it would also match `/ci/`, and they would be `ci_config`. Then 10438 becomes Excluded (not Mono-fix Shell) and 12509 drops Shell. These are CI helper scripts, so excluding them fits the intent better. **Amend:** write the pattern as a literal path segment, and say whether any `ci/` directory counts as CI config.
2. **`Dockerfile.ci`** (airflow 12509): the extension `.ci` is in neither appendix, so read literally the protocol gives `unclassified`. RULES §2, however, says extension-less files are matched by basename `Dockerfile*`. I took Docker/build. It is also a CI image, yet it does not match any CI path rule. **Amend:** state whether `Dockerfile.*` and `*.dockerfile` variants are Docker, and whether a basename rule wins over an unknown extension.
3. **Is a test pattern a substring or a path segment?** `apache/dolphinscheduler` 13945 `dolphinscheduler-api-test/dolphinscheduler-api-test-core/src/main/java/.../Constants.java`. As a substring, `test/` matches `api-test/`, so is_test=yes. As a path segment it does not. I used path segments (is_test=no). This is a **training-impact** case (Java file is_test). The same question covers `liquibase-extension-testing/…` (not matched either way) and `.../rest-api-spec/test/...` (matched either way). **Amend:** state that patterns match whole path segments, or give the anchored regex.
4. **Generated files without a matching name**: `airflow/www/static/js/types/api-generated.ts` (airflow 23227, 25492). The name says it is generated, but it matches neither `generated/` nor `*.generated.*`, so I counted it as TypeScript. That makes both bugs Poly-fix with TypeScript as a secondary language. With an `*-generated.*` / `*_generated.*` pattern it would drop out (both bugs stay Poly-fix through YAML). `localstack/aws/api/s3/__init__.py` (localstack 7492) is also generated upstream, but nothing in its path shows it, so I counted it. **Amend:** widen the generated pattern or list known generated paths per project.
5. **YAML under `docs/`**: `docs/docsite/keyword_desc.yml` (ansible 68024). The documentation-path rule needs `docs/` **plus a docs extension**, and Step 1 of the protocol does not list a docs-path rule at all. So I counted it as YAML, and the bug is Other-fix rather than Excluded (keep=no either way). It is documentation source in practice. **Amend:** say whether non-docs extensions under `docs/` count.
6. **`.sha256` under `docs/` gives a Poly-fix**: `docs/apache-airflow/img/airflow_erd.sha256` (airflow 31431) maps to TestData/test-data with is_test=no (no test path). This alone makes the bug Poly-fix with secondary "TestData". It is a checksum of a generated ERD image, not test data. poly_subtype stays empty (no grammar). **Amend:** exclude checksums beside docs images (e.g. under the docs-path rule), or exclude `.sha256` outside test paths.
7. **Build file tagged as test**: `x-pack/qa/runtime-fields/build.gradle` (ES 83431). The `qa/` pattern applies "for any file type", so is_test=yes, and the bug's only grammar secondary (Gradle) is test, giving `test-asset-only`. It is the build wiring of a QA module, so the label "test asset" is questionable. **Clarify:** should test scope apply to build files?
8. **`.txt` that is data, not docs**: `test/lib/ansible_test/_data/completion/remote.txt` (ansible 80413). Excluded as documentation by the blanket `.txt` rule, although it is an ansible-test configuration list. The bug is not kept (no Python counted), so the impact is small.
9. **Checkstyle config is not "dev tooling"**: `build-tools-internal/src/main/resources/checkstyle*.xml` (ES 83311). The dev-tooling list names linters for Python/JS (`.flake8`, `.eslint*`) but not checkstyle, so I counted them as XML and the bug is Poly-fix (INI; XML), behaviour-bearing. This commit is a linter upgrade, so the spirit of the rule would exclude them. **Amend:** add `checkstyle*.xml`, `spotless`/`forbidden-apis` configs, etc., or state explicitly that they count.
10. **`pom.xml` category**: RULES §2 names `build` as the category for build files (Gradle, Make, MSBuild), but Appendix A puts every `.xml` in data-config, including `pom.xml`. I followed Appendix A (XML, data-config). The bug labels do not change; the `category` column and the "headline" grain do (XML is in headline, Gradle is not). Bugs: dolphinscheduler 4939, liquibase 2816.
11. **Deleted binary: `binary` or `deletion`?** `docs/img/switch_configure.jpg` (dolphinscheduler 8029) and two `.jpg` in ES 90799. The first excluding rule decides, and Step 2 comes before Step 4, so I used `binary`. A reader might expect `deletion` for every D row. **Clarify** in the protocol.
12. **`src/internalClusterTest/` is still not in the test-pattern list** (RULES §8 open item 1). In this sample it did not matter: `DataStreamLifecycleServiceIT.java` (ES 97399) is caught by `*IT.java`. `test/integration/targets/…` (ansible) is caught by `test/`. `*Tests.java` (plural) is not a listed pattern; every instance in this sample sat under `src/test/` anyway. **Amend:** add `src/internalClusterTest/` and `*Tests.java`.
13. **Mono-fix in a non-primary language**: ansible 62411 (PowerShell only), liquibase 4216 (Groovy tests only), ES 91081 (Groovy build tool + docs), dolphinscheduler 5769 (JavaScript UI only), airflow 10438 (Shell). Step 2 gives Mono-fix with keep=no, and I applied it as written. Note that RULES says "Other-fix becomes empty by construction" in the kept set, but non-kept Mono-fix and Poly-fix bugs exist too (airflow 12509 and ansible 80413 are Poly-fix with keep=no). This is fine, but worth stating so nobody "corrects" these to Other-fix.
14. **poly_subtype when a non-grammar secondary is non-test**: the protocol says "at least one *secondary-language file*". I read it as a file in a **grammar** secondary language, because the subtype exists only for grammar languages. No bug in this sample is affected (e.g. ES 83311 has a non-test XML anyway), but a bug with test YAML plus non-test `.properties` would be decided by this reading. **Clarify.**
15. **secondary_languages ordering**: "alphabetical" was applied case-sensitively (e.g. `TypeScript; YAML`, `INI; XML`). No case clash in this sample.

## 4. Rules I would amend or clarify (summary)

1. Anchor every path pattern to path segments, and publish the exact regexes in the RULES doc (items 1, 3).
2. Widen the generated-file rule (`*-generated.*`, `*_generated.*`) or keep a per-project list (item 4).
3. Make the docs-path rule part of protocol Step 1 and say what happens to non-docs extensions and checksums under `docs/` (items 5, 6).
4. Add JVM linter configs (checkstyle etc.) to dev tooling (item 9).
5. Decide the `Dockerfile.*` handling and the basename-vs-unknown-extension precedence (item 2).
6. Decide whether test scope applies to build files (item 7), and add `src/internalClusterTest/`, `*Tests.java` (item 12).
7. Align RULES §2 ("build" includes Maven?) with Appendix A for `pom.xml` (item 10).

## 5. Tally (for cross-checking)

- Files: counts=yes 144 / no 34. Excluded reasons: changelog_fragment 12, binary 10, documentation 9, ci_config 3 (no lockfile, vendored, generated, devtooling, certificate, codegen_template, unclassified or deletion in this sample). is_test=yes 53.
- Bugs: Poly-fix 24, Mono-fix 17, Other-fix 5, Excluded 4. keep=yes 34. poly_subtype: behaviour-bearing 10, test-asset-only 8, empty 32 (including 4 kept Poly-fix whose only secondaries lack a grammar: INI ×2, TestData ×2).
