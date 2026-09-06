**Table 2.** Architectural feasibility: dominant outcome when each technique ingests a real file of the given type. `trivial_graph` / `degraded_wholefile` = the technique produced no structural representation.

| cell                                 |   n_files | BM25_outcome   | BLAZE_outcome   | FLIM_outcome       | COOBA_outcome   |
|:-------------------------------------|----------:|:---------------|:----------------|:-------------------|:----------------|
| YAML (.yaml, python)                 |        73 | success        | success         | degraded_wholefile | trivial_graph   |
| YAML (.yaml, java)                   |        51 | success        | success         | degraded_wholefile | trivial_graph   |
| JSON (.json, python)                 |        68 | success        | success         | degraded_wholefile | success         |
| JSON (.json, java)                   |        21 | success        | success         | degraded_wholefile | trivial_graph   |
| YAML (.yml, python)                  |        56 | success        | success         | degraded_wholefile | trivial_graph   |
| YAML (.yml, java)                    |        28 | success        | success         | degraded_wholefile | trivial_graph   |
| XML (.xml, java)                     |        56 | success        | success         | degraded_wholefile | trivial_graph   |
| XML (.xml, python)                   |         1 | success        | success         | degraded_wholefile | trivial_graph   |
| SQL (.sql, java)                     |        34 | success        | success         | degraded_wholefile | trivial_graph   |
| Gradle (.gradle, java)               |        25 | success        | success         | structural_success | trivial_graph   |
| JSON (.json5, python)                |        11 | success        | success         | degraded_wholefile | success         |
| XML-Schema (.xsd, java)              |         5 | success        | success         | degraded_wholefile | trivial_graph   |
| YAML (.kubernetes-helm-yaml, python) |         3 | success        | success         | degraded_wholefile | trivial_graph   |
| Docker (.dockerfile, python)         |         1 | success        | success         | degraded_wholefile | trivial_graph   |
| ANTLR (.g4, python)                  |         1 | success        | success         | degraded_wholefile | trivial_graph   |
