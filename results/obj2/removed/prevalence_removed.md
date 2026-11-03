# Removed bugs (BeetleBoxRemoved) — RULESET 0.2.0

1226 removed bugs in the six projects; 1055 pass the keep filter (86.1 %; kept set: 72.0 %).

## Poly-fix prevalence, removed vs kept

| project                 |   kept |   removed |
|:------------------------|-------:|----------:|
| POOLED                  |   27.4 |      15.9 |
| ansible/ansible         |   43.5 |      35.7 |
| apache/airflow          |   18.8 |       9.1 |
| apache/dolphinscheduler |   23.6 |      14.6 |
| elastic/elasticsearch   |   17.8 |       5.9 |
| liquibase/liquibase     |   49.7 |      50   |
| localstack/localstack   |   34.4 |      20   |

## Which file does the report name? (kept-filter removed bugs)

- reports naming at least one counted fix file: 97.5 %
- Poly-fix: naming a secondary-language file: 20.8 %; naming a primary-language file: 77.4 %

## In the test windows

- fold 1: 202 bugs (Poly-fix 34)
- fold 2: 235 bugs (Poly-fix 34)
