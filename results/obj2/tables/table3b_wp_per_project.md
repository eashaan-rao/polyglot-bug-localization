| technique   | project                 | class    |   Top@1 |   Top@10 |   MAP |   MRR |
|:------------|:------------------------|:---------|--------:|---------:|------:|------:|
| BM25        | elastic/elasticsearch   | Mono-fix |   0.174 |    0.404 | 0.152 | 0.262 |
| BM25        | elastic/elasticsearch   | Poly-fix |   0.167 |    0.444 | 0.12  | 0.251 |
| BM25        | liquibase/liquibase     | Mono-fix |   0     |    0.13  | 0.037 | 0.051 |
| BM25        | liquibase/liquibase     | Poly-fix |   0     |    0.059 | 0.017 | 0.026 |
| BM25        | apache/dolphinscheduler | Mono-fix |   0.028 |    0.22  | 0.057 | 0.081 |
| BM25        | apache/dolphinscheduler | Poly-fix |   0.032 |    0.323 | 0.053 | 0.106 |
| BM25        | ansible/ansible         | Mono-fix |   0.167 |    0.486 | 0.254 | 0.282 |
| BM25        | ansible/ansible         | Poly-fix |   0.204 |    0.667 | 0.238 | 0.35  |
| BM25        | apache/airflow          | Mono-fix |   0.134 |    0.331 | 0.141 | 0.202 |
| BM25        | apache/airflow          | Poly-fix |   0.095 |    0.381 | 0.088 | 0.183 |
| BM25        | localstack/localstack   | Mono-fix |   0.113 |    0.468 | 0.161 | 0.209 |
| BM25        | localstack/localstack   | Poly-fix |   0.28  |    0.64  | 0.261 | 0.395 |
