**Table 1.** Dataset (BeetleBox, RULESET 0.2.0). Kept = fix touches the project's AST-parseable primary language.

| project                 | language   |   kept bugs |   Mono-fix |   Poly-fix |   Poly% (broad) |   Poly% (headline) |   Poly% (strict) |   min class n |
|:------------------------|:-----------|------------:|-----------:|-----------:|----------------:|-------------------:|-----------------:|--------------:|
| elastic/elasticsearch   | Java       |         721 |        564 |        157 |            17.8 |               15.1 |              0.3 |           157 |
| liquibase/liquibase     | Java       |         199 |         99 |        100 |            49.7 |               20.1 |             35.7 |            99 |
| apache/dolphinscheduler | Java       |         698 |        523 |        175 |            23.6 |               14.6 |             10.7 |           175 |
| ansible/ansible         | Python     |         626 |        352 |        274 |            43.5 |               39.1 |             13.4 |           274 |
| apache/airflow          | Python     |         917 |        739 |        178 |            18.8 |               14.2 |              5.5 |           178 |
| localstack/localstack   | Python     |         433 |        284 |        149 |            34.4 |               29.6 |              2.8 |           149 |
| TOTAL                   |            |        3594 |       2561 |       1033 |            27.4 |               21   |              8.2 |               |
