# Annotator A: log of the human round

- **annotator:** A
- **started (date):** 2026-11-22
- **finished (date):** 2026-11-22
- **time spent, reading the protocol (min):** 35.0
- **time spent, files (min):** 60.0
- **time spent, bugs (min):** 40.0
- **how you worked (free text):** 

## Ambiguities

| repo | bug | path | rule applied / question |
|---|---|---|---|
| ansible/ansible | 68024 | docs/docsite/keyword_desc.yml | CLASSIFICATION_RULES.md §3 still lists a 'Documentation path' rule (docs/ + docs extension), the protocol says there is none. Followed the protocol: .yml under docs/ counted YAML -> bug becomes Other-fix (keep no). |
| liquibase/liquibase | 4216 | liquibase-integration-tests/src/test/resources/liquibase/extension/testing/command/generateChangelog.test.groovy | Double extension: last extension .groovy decides -> Groovy. 'liquibase-integration-tests' is not a whole-directory match for integration-tests, but src/test/ matches -> is_test yes. |
| liquibase/liquibase | 5263 | liquibase-extension-testing/src/main/resources/liquibase.sdk.yaml | Module named *-testing is not a test dir under the regex, path is src/main -> is_test no -> poly_subtype behaviour-bearing. Intent may be test support code. |
| elastic/elasticsearch | 84627 | x-pack/plugin/sql/qa/server/src/main/resources/math.sql-spec | Extension taken as .sql-spec (TestData), not .sql; is_test yes via qa/ although under src/main/resources. |
| elastic/elasticsearch | 83431 | x-pack/qa/runtime-fields/src/main/java/org/elasticsearch/xpack/runtimefields/test/CoreTestTranslater.java | src/main/java but qa/ and package dir test/ match -> is_test yes. |
| ansible/ansible | 80413 | test/lib/ansible_test/_util/target/setup/bootstrap.sh | ansible-test framework code under test/lib is test scope by the regex (is_test yes) although it is tooling rather than a test. |
