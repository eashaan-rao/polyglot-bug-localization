# Annotator B — working record (ruleset 0.2.0, 50 bugs / 178 files)

## 0. Isolation

- Rule sources read: `docs/ANNOTATION_PROTOCOL.md`, `docs/CLASSIFICATION_RULES.md`,
  `docs/GLOSSARY.md`. Nothing else.
- Inputs read: `bugs_blank.csv`, `files_blank.csv` (read only, not modified).
- Not opened: `key_*.csv`, `*_annotator_A*`, any script under `Scripts/`, any
  parquet or `results/obj2/` output. One `ls` of `results/obj2/annotation/v2/`
  (run to check my outputs) showed that `key_*.csv` and `*_annotator_A.csv`
  exist. I saw only the file names and never opened the files.
- I did not open any file contents in the git repositories. Every decision was
  made from the path and the change type only.

## 1. Order of work

1. Read the protocol, then the rules document, then the glossary (about 10 min
   for a human). I wrote down the points where the two documents differ (see §3).
2. Printed all 178 file rows with index, bug, change type and path. Checked that
   each bug's `n_files` matched its number of rows in `files_blank.csv` (all 50
   match).
3. **File pass (Step 1 of the protocol)**, one row at a time, top to bottom, in
   this fixed order:
   1. Path rules in order: changelog fragment → lockfile → vendored → generated
      → CI → dev tooling. Then `META-INF/services/` (no case in this sample).
   2. Extension (lower case, the part after the last `.`), looked up in
      Appendix A. A file with no extension was looked up by basename in
      Appendix B. Category `docs` or extension `.txt` gave `documentation`.
      Category `other` gave `binary` / `certificate` / `codegen_template`.
   3. Test scope from the §3 patterns.
   4. Deletion (D).
   5. Otherwise `counts=yes`.
   I typed each decision by hand into a per-row table, with a note wherever I
   had to interpret a rule. Python's `csv` module only copied those values into
   the sheet. It does not hold the extension table.
4. **Bug pass (Step 2)**: I wrote every bug's label, keep, secondary languages
   and subtype by hand from my file rows. Then, as a check against slips only, a
   short script aggregated my own file rows using the Step 2 wording and compared
   the result with my hand entries. There were 0 mismatches.
5. Wrote this record.

Time: about 10 minutes of wall-clock time for me. For a human I estimate about
2–2.5 hours: 20 min reading the rules, about 1.5 h for 178 files (most are quick
`.java` / `.py` / changelog rows), and 20–30 min for the bugs and notes.

## 2. How each kind of case was resolved (practical cheat sheet)

| Case | Decision | Examples (row idx in files_blank) |
|---|---|---|
| `docs/changelog/*.yaml`, `changelogs/fragments/*.yml` | changelog_fragment. This wins over YAML because path rules run first. | 10, 41, 44, 64, 69, 89, 109, 121, 125, 142, 152, 156 |
| `.github/…`, `.azure-pipelines/…` | ci_config | 26, 76, 141 |
| `scripts/ci/libraries/*.sh` (airflow) | **counted as Shell.** The CI rule says `.ci/` (with a dot), and `scripts/ci/` does not match it. | 23, 172, 173 |
| `.md`, `.rst`, `.asciidoc` | documentation. Language left empty. | 22, 83, 98, 99, 106, 107, 116, 133 |
| `.txt` | documentation (protocol says this explicitly) | 144 |
| `.jpg/.png/.svg/.mkv/.mp4` | binary. A deleted `.jpg` also gets binary, because step 2 runs before step 4 (deletion). | 57, 58, 100–104, 117, 118, 132 |
| `.yml/.yaml` under `test/`, `src/yamlRestTest/` | YAML, data-config, is_test=yes | 11, 12, 33, 92–97, 123, 143, 167, 168 |
| `.yml` under `docs/` | **counted as YAML.** The doc path rule needs a docs extension as well. | 115 |
| `*.snapshot.json` (localstack) | JSON (the extension is `.json`, not `.snap`), is_test=yes | 73, 151 |
| `.properties`, `.inventory` | INI, data-config, counted | 2, 51–53, 66 |
| `pom.xml`, checkstyle `.xml` | XML, data-config, counted | 0, 1, 40, 164 |
| `Dockerfile` | Docker, build (Appendix B) | 20, 108 |
| `*.sql-spec`, `*.sha256` | TestData, test-data | 131, 153 |
| `*Tests.java` in `src/test/` | test (by directory; `*Test.java` does not match `Tests`) | 16, 19, 155 |
| `*IT.java` in `src/internalClusterTest/` | test (by `*IT.java`) | 75 |
| R (rename) | judged by the new path | 129 |

Bug-level conventions I used:
- Mono-fix in a non-primary language (PowerShell, Groovy, JavaScript, Shell) is
  labelled Mono-fix with keep=no (bugs 62411, 4216, 91081, 5769, 10438).
- Poly-fix with keep=no gets an empty poly_subtype (the protocol says "kept
  Poly-fix only") (bugs 12509, 80413).
- Poly-fix whose only secondary language has no grammar (INI, TestData) gets an
  empty poly_subtype (bugs 7180, 78509, 31431, 84627).
- `secondary_languages` lists every counted language other than the primary one,
  including INI and TestData, in alphabetical order.

## 3. Ambiguities and places where the rules do not fit

Each item names the file, the rule I applied, and the alternative reading.

1. **Path patterns: substring or directory component?**
   File: `dolphinscheduler-api-test/dolphinscheduler-api-test-core/src/main/java/.../Constants.java`
   (bug 13945, row 82). The string `test/` appears inside the directory name
   `dolphinscheduler-api-test/`, but no directory is called `test`. I read the
   patterns as matching whole directory names, so I set is_test=no. A
   substring regex would give yes. The code is semantically API-test framework
   code. This is a **Java file, so the disagreement would affect training data**.
   The same question applies to every pattern (`generated/`, `vendor/`, `qa/`, …).
   *Amend:* say whether patterns are anchored to directory boundaries
   (`(^|/)test/`), and say whether a test-only module (`*-api-test`, `*-it`) is
   test scope.
2. **Files with a "generated" name that the rule misses.**
   `airflow/www/static/js/types/api-generated.ts` (rows 30, 177; bugs 23227,
   25492). This file is generated from the OpenAPI spec. But `generated/` needs a
   directory and `*.generated.*` needs dots, and this name has a hyphen. So I
   counted it as TypeScript, which makes both bugs Poly-fix with TypeScript.
   Similar case: `localstack/aws/api/s3/__init__.py` (row 147) is scaffold
   output and also matches no rule. *Amend:* add `*-generated.*` (or `*generated*`
   in the basename), or list known generated paths for each project.
3. **`Dockerfile.ci`** (row 21, bug 12509). It has an extension (`.ci`) that is
   not in Appendix A. Appendix B lists only the exact basename `dockerfile`, and
   the protocol applies Appendix B only to files with no extension. That would
   make the file `unclassified`. But RULES §2 says "Files with no usable
   extension are matched by basename (`Dockerfile*`, …)". I applied the
   `Dockerfile*` glob and set Docker, build. This did not change the bug, because
   row 20 is Docker anyway. *Amend:* put `dockerfile*` (prefix match) in
   Appendix B, or say that a variant suffix is unclassified.
4. **CI rule `.ci/` versus `scripts/ci/`** (airflow rows 23, 172, 173). The rule
   as written (with the dot) does not match airflow's CI scripts. So bug 10438
   ("Fix Breeze failure on MacOS") becomes Mono-fix in Shell, and bug 12509
   becomes Poly-fix (Docker; Shell). Both are not kept. If the rule is meant to
   cover `ci/` directories, these become Other-fix and Mono-fix in Docker, or
   Excluded. *Amend:* say whether `(^|/)ci/` and `scripts/ci/` are CI.
5. **Documentation path rule needs a docs extension, so non-docs files under
   `docs/` are counted.**
   - `docs/docsite/keyword_desc.yml` (row 115, bug 68024, "Add description of …
     keywords") is counted as YAML, so a docs-only change becomes Other-fix
     instead of Excluded.
   - `docs/apache-airflow/img/airflow_erd.sha256` (row 131, bug 31431) maps to
     TestData, which makes the bug Poly-fix with TestData only because of a
     checksum of a docs diagram.
   *Amend:* exclude anything under `docs/` except a listed set of extensions, or
   at least `.sha256`/`.svg` under `docs/`.
6. **`.txt` is always documentation.** `test/lib/ansible_test/_data/completion/remote.txt`
   (row 144, bug 80413) is data that ansible-test reads, not documentation. The
   protocol is explicit, so I applied documentation. Note that this removes the
   bug's only behaviour data file.
7. **ansible-test tool code under `test/lib/`.**
   `test/lib/ansible_test/_util/target/setup/bootstrap.sh` (row 145) matches
   `test/`, so I set is_test=yes. But `test/lib/ansible_test/` is the ansible-test
   product itself, not tests of ansible. RULES §8 open item 1 mentions
   `test/integration/targets/`, and `test/lib/` deserves the same explicit
   decision.
8. **Lint config is not in the dev-tooling list.**
   `build-tools-internal/src/main/resources/checkstyle.xml` and
   `checkstyle-idea.xml` (rows 0, 1, bug 83311 "Upgrade Checkstyle") are lint
   config, the same kind of file as `.eslint*` or `.flake8`. The list does not
   name them, so I counted them as XML. That makes the bug Poly-fix,
   behaviour-bearing. *Amend:* add `checkstyle*.xml`, `forbidden-apis`,
   `spotless`, etc., or state that only the listed names are dev tooling.
9. **`pom.xml` is XML data-config, not build.** Rows 40 and 164. Appendix A
   maps `.xml` to XML data-config, while `build.gradle` is build. This creates an
   asymmetry: bug 2816 (a Mockito bump in `pom.xml`) is Other-fix through
   "data-config". The label does not change, but the category does. *Amend
   (optional):* add a basename `pom.xml` → Maven, build.
10. **Test-scoped build script gives a test-asset-only subtype.**
    `x-pack/qa/runtime-fields/build.gradle` (row 45, bug 83431) has is_test=yes
    because of `qa/`, so the bug is "test-asset-only" with Gradle. The rule is
    clear, but it is questionable to call a build script a test asset.
11. **Which files decide poly_subtype?** The protocol says "behaviour-bearing if
    at least one secondary-language file has is_test = no". It does not say
    whether a non-grammar secondary file (INI/TestData) counts towards that
    check. In this sample it never changes an answer (bug 83311: the non-test
    XML gives behaviour-bearing either way). *Amend:* say "grammar
    secondary-language file".
12. **Poly-fix whose only secondary language has no grammar.** Bugs 7180 and
    78509 (INI), and 31431 and 84627 (TestData). Step 2 still labels these
    Poly-fix (≥2 languages), although the admission criteria C1 say INI and
    plain-text fixtures "are not languages". I followed Step 2: Poly-fix with an
    empty subtype. *Amend:* say explicitly that the label uses raw languages and
    that grain membership is separate. This is what RULES §4 implies but does not
    state.
13. **Deleted binary: binary or deletion?** Rows 100, 117 and 118 (D on `.jpg`).
    Step 2 excludes them as binary before step 4 is reached, so the reason is
    `binary` and the language is empty. The protocol says to keep the language
    only for `deletion`. This is clear from the order, but easy to slip on.
14. **Snapshots.** `tests/integration/test_sns.snapshot.json` (rows 73, 151) is
    JSON by extension, but it plays the same role as `.snap` (TestData). I
    applied the extension. Because of this, localstack bugs get the secondary
    language JSON rather than TestData. This matches RULES §6 ("localstack = JSON
    snapshots").
15. **`src/internalClusterTest/`** (row 75) is not in the test-pattern list (RULES
    §8 open item 1). It did not matter here, because the file ends in `IT.java`.
    A non-`IT` file in that directory would be is_test=no.

## 4. Suggested rule amendments (priority order)

1. Anchor all path patterns to directory boundaries, and state this (item 1).
   This has training impact.
2. Decide `ci/` and `scripts/ci/` (item 4), and add `*-generated.*` (item 2).
3. Make Appendix B a prefix match for `dockerfile*`, and say how a basename with
   an unknown suffix is handled (item 3).
4. Tighten the docs-directory rule (item 5) and the `.txt` rule (item 6).
5. Say that only grammar secondaries decide poly_subtype (item 11), and that the
   label counts non-grammar languages (item 12).
6. Add checkstyle-style lint config to dev tooling, or confirm the list is
   closed (item 8).

## 5. Result summary

- Labels: Poly-fix 24, Mono-fix 17, Other-fix 5, Excluded 4. keep: yes 34, no 16.
- Files: counts=yes 144, counts=no 34. Exclusion reasons: changelog_fragment 12,
  binary 10, documentation 9, ci_config 3.
- poly_subtype: behaviour-bearing 10, test-asset-only 8, empty 32.
