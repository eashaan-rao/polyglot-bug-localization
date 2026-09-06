# Step 1 — Prevalence  (RULESET_VERSION 0.2.0)

Kept bug set: **3594** of 4995 bugs (72.0%) — fix touches the project's primary (AST-parseable) language.

## Poly-fix prevalence (share of Mono+Poly, kept set)

| grain | definition | pooled | range across projects |
|---|---|---|---|
| headline | secondary is YAML / JSON / XML / SQL | **21.0%** (754 bugs) | 14.2% – 39.1% |
| broad | secondary is any language with a grammar (adds build scripts, 2nd programming language, Shell, Jinja, grammars) | **27.4%** (985 bugs) | 17.8% – 49.7% |
| strict | fix spans >= 2 programming languages | **8.2%** (294 bugs) | 0.3% – 35.7% |

## Per project

| project | kept | Mono | Poly | headline % | broad % | strict % | smaller class n |
|---|---|---|---|---|---|---|---|
| elastic/elasticsearch | 721 | 564 | 157 | 15.1% | 17.8% | 0.3% | 157 |
| liquibase/liquibase | 199 | 99 | 100 | 20.1% | 49.7% | 35.7% | 99 |
| apache/dolphinscheduler | 698 | 523 | 175 | 14.6% | 23.6% | 10.7% | 175 |
| ansible/ansible | 626 | 352 | 274 | 39.1% | 43.5% | 13.4% | 274 |
| apache/airflow | 917 | 739 | 178 | 14.2% | 18.8% | 5.5% | 178 |
| localstack/localstack | 433 | 284 | 149 | 29.6% | 34.4% | 2.8% | 149 |
| POOLED | 3594 | 2561 | 1033 | 21.0% | 27.4% | 8.2% | 1033 |

Every project has >= ~100 bugs in its smaller class -> a balanced within-project Mono-vs-Poly comparison is viable for all six.

## Secondary languages in Poly-fix bugs (kept set)

| secondary language | tier | Poly-fix bugs | projects | is a ground-truth target in |
|---|---|---|---|---|
| YAML | T1 | 497 | 6 | 497 |
| JSON | T1 | 163 | 6 | 163 |
| XML | T1 | 117 | 4 | 117 |
| Shell | T3 | 101 | 5 | 101 |
| Groovy | T2 | 72 | 2 | 72 |
| TypeScript | T2 | 47 | 2 | 47 |
| JavaScript | T2 | 43 | 3 | 43 |
| Gradle | T2 | 33 | 1 | 33 |
| SQL | T1 | 19 | 2 | 19 |
| Vue | T2 | 19 | 1 | 19 |
| Jinja | T3 | 18 | 2 | 18 |
| Docker | T2 | 14 | 3 | 14 |
| Python | T3 | 13 | 1 | 13 |
| PowerShell | T3 | 8 | 1 | 8 |
| CSS | T3 | 7 | 3 | 7 |
| Java | T3 | 7 | 1 | 7 |
| Make | T2 | 6 | 1 | 6 |
| XML-Schema | T2 | 5 | 1 | 5 |
| Template | T3 | 3 | 1 | 3 |
| C# | T3 | 2 | 2 | 2 |
| TOML | T3 | 2 | 1 | 2 |
| Terraform | T3 | 2 | 1 | 2 |
| Policy | T3 | 1 | 1 | 1 |
| ANTLR | T2 | 1 | 1 | 1 |
| Autotools | T3 | 1 | 1 | 1 |
| MSBuild | T3 | 1 | 1 | 1 |

Every counted secondary file is also a ground-truth localization target — the polyglot files are what developers had to locate, not incidental edits.

> Note: `broad` includes Shell (101 bugs, mostly test glue). `broad` minus Shell ≈ 884 bugs.
