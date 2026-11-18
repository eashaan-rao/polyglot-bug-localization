# Objective 2 statistics (full)

Input: `/home/cs21d002_eashaan/PhD/Objective2/results/obj2/eval/per_bug.parquet`; bugs (seed-averaged rows): 135858

## RQ3 — class effect (Poly-fix minus Mono-fix), pooled model, primary condition

Primary outcome: AP (MAP); AP@10 for LocAgent.

| condition   | tech                 | view   | outcome                 | model              |   n_bugs |   class_effect_poly |   ci_lo |   ci_hi |      p |
|:------------|:---------------------|:-------|:------------------------|:-------------------|---------:|--------------------:|--------:|--------:|-------:|
| primary     | BLAZE                | all    | ap                      | mixedlm_powell     |     1399 |             -0.0213 | -0.0593 |  0.0167 | 0.2711 |
| primary     | BLAZE                | all    | cfr10                   | mixedlm_powell     |     1399 |             -0.0103 | -0.063  |  0.0425 | 0.7031 |
| primary     | BLAZE                | all    | rr                      | mixedlm_powell     |     1399 |              0.0116 | -0.0382 |  0.0614 | 0.6473 |
| primary     | BLAZE                | all    | top10                   | mixedlm_powell     |     1399 |              0.0292 | -0.0335 |  0.0918 | 0.3617 |
| primary     | BLAZE                | all    | top10 (logit, log-odds) | logit_project_fe   |     1399 |              0.1356 | -0.145  |  0.4161 | 0.3437 |
| primary     | BLAZE                | parse  | ap                      | mixedlm_powell     |     1399 |             -0.1029 | -0.1404 | -0.0654 | 0      |
| primary     | BLAZE                | parse  | cfr10                   | mixedlm_powell     |     1399 |             -0.1161 | -0.1667 | -0.0656 | 0      |
| primary     | BLAZE                | parse  | rr                      | mixedlm_powell     |     1399 |             -0.0229 | -0.074  |  0.0281 | 0.3783 |
| primary     | BLAZE                | parse  | top10                   | mixedlm_powell     |     1399 |             -0.0262 | -0.089  |  0.0366 | 0.4144 |
| primary     | BLAZE                | parse  | top10 (logit, log-odds) | logit_project_fe   |     1399 |             -0.1049 | -0.3857 |  0.1759 | 0.4642 |
| primary     | BLAZE_ALL            | all    | ap                      | mixedlm_powell     |      691 |             -0.0307 | -0.0852 |  0.0238 | 0.2692 |
| primary     | BLAZE_ALL            | all    | cfr10                   | mixedlm_powell     |      691 |             -0.0603 | -0.1349 |  0.0143 | 0.1133 |
| primary     | BLAZE_ALL            | all    | rr                      | mixedlm_powell     |      691 |              0.0051 | -0.0949 |  0.105  | 0.9209 |
| primary     | BLAZE_ALL            | all    | top10                   | mixedlm_powell     |      691 |             -0.0494 | -0.1399 |  0.0411 | 0.2843 |
| primary     | BLAZE_ALL            | all    | top10 (logit, log-odds) | logit_project_fe   |      691 |             -0.216  | -0.6262 |  0.1943 | 0.3021 |
| primary     | BLAZE_ALL            | parse  | ap                      | mixedlm_powell     |      691 |             -0.1081 | -0.1619 | -0.0542 | 0.0001 |
| primary     | BLAZE_ALL            | parse  | cfr10                   | mixedlm_powell     |      691 |             -0.1608 | -0.2335 | -0.0882 | 0      |
| primary     | BLAZE_ALL            | parse  | rr                      | mixedlm_powell     |      691 |             -0.0423 | -0.1186 |  0.0341 | 0.2777 |
| primary     | BLAZE_ALL            | parse  | top10                   | mixedlm_powell     |      691 |             -0.1198 | -0.2123 | -0.0272 | 0.0112 |
| primary     | BLAZE_ALL            | parse  | top10 (logit, log-odds) | logit_project_fe   |      691 |             -0.536  | -0.9521 | -0.1198 | 0.0116 |
| primary     | BM25                 | all    | ap                      | mixedlm_powell     |     1399 |             -0.026  | -0.0681 |  0.0161 | 0.2254 |
| primary     | BM25                 | all    | cfr10                   | mixedlm_powell     |     1399 |             -0.0201 | -0.0728 |  0.0326 | 0.4543 |
| primary     | BM25                 | all    | rr                      | mixedlm_powell     |     1399 |              0.0088 | -0.0435 |  0.0612 | 0.7403 |
| primary     | BM25                 | all    | top10                   | mixedlm_powell     |     1399 |              0.0395 | -0.0222 |  0.1011 | 0.21   |
| primary     | BM25                 | all    | top10 (logit, log-odds) | logit_project_fe   |     1399 |              0.1719 | -0.1204 |  0.4642 | 0.2491 |
| primary     | BM25                 | parse  | ap                      | mixedlm_powell     |     1399 |             -0.1293 | -0.1713 | -0.0873 | 0      |
| primary     | BM25                 | parse  | cfr10                   | mixedlm_lbfgs      |     1399 |             -0.1566 | -0.207  | -0.1063 | 0      |
| primary     | BM25                 | parse  | rr                      | mixedlm_lbfgs      |     1399 |             -0.0496 | -0.1036 |  0.0045 | 0.0721 |
| primary     | BM25                 | parse  | top10                   | mixedlm_powell     |     1399 |             -0.0514 | -0.1119 |  0.0091 | 0.0962 |
| primary     | BM25                 | parse  | top10 (logit, log-odds) | logit_project_fe   |     1399 |             -0.2689 | -0.5643 |  0.0264 | 0.0743 |
| primary     | CoChangeFLIM         | all    | ap                      | mixedlm_powell     |     1399 |             -0.0247 | -0.0645 |  0.0151 | 0.2236 |
| primary     | CoChangeFLIM         | all    | cfr10                   | mixedlm_powell     |     1399 |             -0.0546 | -0.1058 | -0.0034 | 0.0366 |
| primary     | CoChangeFLIM         | all    | rr                      | mixedlm_powell     |     1399 |             -0.023  | -0.0715 |  0.0254 | 0.3511 |
| primary     | CoChangeFLIM         | all    | top10                   | mixedlm_powell     |     1399 |             -0.0173 | -0.0756 |  0.0409 | 0.5593 |
| primary     | CoChangeFLIM         | all    | top10 (logit, log-odds) | logit_project_fe   |     1399 |             -0.0776 | -0.3867 |  0.2316 | 0.6228 |
| primary     | CoChangeFLIM         | parse  | ap                      | mixedlm_powell     |     1399 |             -0.1335 | -0.1743 | -0.0928 | 0      |
| primary     | CoChangeFLIM         | parse  | cfr10                   | mixedlm_powell     |     1399 |             -0.1781 | -0.2268 | -0.1293 | 0      |
| primary     | CoChangeFLIM         | parse  | rr                      | mixedlm_lbfgs      |     1399 |             -0.033  | -0.0861 |  0.02   | 0.222  |
| primary     | CoChangeFLIM         | parse  | top10                   | mixedlm_lbfgs      |     1399 |             -0.0665 | -0.1234 | -0.0097 | 0.0218 |
| primary     | CoChangeFLIM         | parse  | top10 (logit, log-odds) | logit_project_fe   |     1399 |             -0.3753 | -0.6915 | -0.0591 | 0.02   |
| primary     | CoChangeLocAgent     | all    | ap10                    | mixedlm_powell     |      781 |             -0.0934 | -0.1466 | -0.0401 | 0.0006 |
| primary     | CoChangeLocAgent     | all    | cfr10                   | ols_project_fe_hc3 |      781 |             -0.1325 | -0.1946 | -0.0704 | 0      |
| primary     | CoChangeLocAgent     | all    | top10                   | ols_project_fe_hc3 |      781 |             -0.0323 | -0.1048 |  0.0402 | 0.382  |
| primary     | CoChangeLocAgent     | all    | rr10                    | mixedlm_powell     |      781 |             -0.0097 | -0.0626 |  0.0431 | 0.7178 |
| primary     | CoChangeLocAgent     | all    | top10 (logit, log-odds) | logit_project_fe   |      781 |             -0.283  | -0.7806 |  0.2146 | 0.2649 |
| primary     | CoChangeLocAgent     | parse  | ap10                    | mixedlm_powell     |      781 |             -0.1562 | -0.2078 | -0.1046 | 0      |
| primary     | CoChangeLocAgent     | parse  | cfr10                   | ols_project_fe_hc3 |      781 |             -0.2212 | -0.2771 | -0.1653 | 0      |
| primary     | CoChangeLocAgent     | parse  | top10                   | mixedlm_powell     |      781 |             -0.0297 | -0.0913 |  0.0318 | 0.3437 |
| primary     | CoChangeLocAgent     | parse  | rr10                    | mixedlm_powell     |      781 |             -0.0166 | -0.069  |  0.0359 | 0.5359 |
| primary     | CoChangeLocAgent     | parse  | top10 (logit, log-odds) | logit_project_fe   |      781 |             -0.2862 | -0.7797 |  0.2073 | 0.2557 |
| primary     | CoChangeSweRank      | all    | ap                      | ols_project_fe_hc3 |      781 |             -0.0815 | -0.1346 | -0.0285 | 0.0026 |
| primary     | CoChangeSweRank      | all    | cfr10                   | ols_project_fe_hc3 |      781 |             -0.078  | -0.1412 | -0.0147 | 0.0157 |
| primary     | CoChangeSweRank      | all    | rr                      | mixedlm_powell     |      781 |             -0.0049 | -0.0582 |  0.0483 | 0.8563 |
| primary     | CoChangeSweRank      | all    | top10                   | ols_project_fe_hc3 |      781 |              0.0058 | -0.0677 |  0.0792 | 0.8778 |
| primary     | CoChangeSweRank      | all    | top10 (logit, log-odds) | logit_project_fe   |      781 |              0.0016 | -0.5197 |  0.523  | 0.9951 |
| primary     | CoChangeSweRank      | parse  | ap                      | ols_project_fe_hc3 |      781 |             -0.1877 | -0.2375 | -0.1379 | 0      |
| primary     | CoChangeSweRank      | parse  | cfr10                   | ols_project_fe_hc3 |      781 |             -0.233  | -0.2885 | -0.1775 | 0      |
| primary     | CoChangeSweRank      | parse  | rr                      | mixedlm_powell     |      781 |             -0.0068 | -0.0639 |  0.0503 | 0.8148 |
| primary     | CoChangeSweRank      | parse  | top10                   | mixedlm_powell     |      781 |             -0.0202 | -0.0814 |  0.041  | 0.5176 |
| primary     | CoChangeSweRank      | parse  | top10 (logit, log-odds) | logit_project_fe   |      781 |             -0.3192 | -0.8336 |  0.1952 | 0.224  |
| primary     | FLIM                 | all    | ap                      | mixedlm_powell     |     1399 |             -0.1033 | -0.1446 | -0.0619 | 0      |
| primary     | FLIM                 | all    | cfr10                   | mixedlm_powell     |     1399 |             -0.1359 | -0.1861 | -0.0857 | 0      |
| primary     | FLIM                 | all    | rr                      | mixedlm_powell     |     1399 |             -0.027  | -0.08   |  0.0261 | 0.3197 |
| primary     | FLIM                 | all    | top10                   | mixedlm_powell     |     1399 |             -0.0529 | -0.1104 |  0.0046 | 0.0713 |
| primary     | FLIM                 | all    | top10 (logit, log-odds) | logit_project_fe   |     1399 |             -0.2837 | -0.5956 |  0.0281 | 0.0746 |
| primary     | FLIM                 | parse  | ap                      | mixedlm_powell     |     1399 |             -0.1335 | -0.1743 | -0.0928 | 0      |
| primary     | FLIM                 | parse  | cfr10                   | mixedlm_powell     |     1399 |             -0.1781 | -0.2268 | -0.1293 | 0      |
| primary     | FLIM                 | parse  | rr                      | mixedlm_lbfgs      |     1399 |             -0.033  | -0.0861 |  0.02   | 0.222  |
| primary     | FLIM                 | parse  | top10                   | mixedlm_lbfgs      |     1399 |             -0.0665 | -0.1234 | -0.0097 | 0.0218 |
| primary     | FLIM                 | parse  | top10 (logit, log-odds) | logit_project_fe   |     1399 |             -0.3753 | -0.6915 | -0.0591 | 0.02   |
| primary     | HybridFLIM           | all    | ap                      | mixedlm_powell     |     1399 |             -0.0499 | -0.091  | -0.0088 | 0.0173 |
| primary     | HybridFLIM           | all    | cfr10                   | mixedlm_lbfgs      |     1399 |             -0.0919 | -0.142  | -0.0417 | 0.0003 |
| primary     | HybridFLIM           | all    | rr                      | mixedlm_lbfgs      |     1399 |             -0.0235 | -0.0744 |  0.0273 | 0.3642 |
| primary     | HybridFLIM           | all    | top10                   | mixedlm_powell     |     1399 |             -0.0331 | -0.0905 |  0.0242 | 0.2573 |
| primary     | HybridFLIM           | all    | top10 (logit, log-odds) | logit_project_fe   |     1399 |             -0.203  | -0.5147 |  0.1087 | 0.2018 |
| primary     | HybridFLIM           | parse  | ap                      | mixedlm_powell     |     1399 |             -0.1335 | -0.1743 | -0.0928 | 0      |
| primary     | HybridFLIM           | parse  | cfr10                   | mixedlm_powell     |     1399 |             -0.1781 | -0.2268 | -0.1293 | 0      |
| primary     | HybridFLIM           | parse  | rr                      | mixedlm_lbfgs      |     1399 |             -0.033  | -0.0861 |  0.02   | 0.222  |
| primary     | HybridFLIM           | parse  | top10                   | mixedlm_lbfgs      |     1399 |             -0.0665 | -0.1234 | -0.0097 | 0.0218 |
| primary     | HybridFLIM           | parse  | top10 (logit, log-odds) | logit_project_fe   |     1399 |             -0.3753 | -0.6915 | -0.0591 | 0.02   |
| primary     | HybridLocAgent       | all    | ap10                    | mixedlm_powell     |      781 |             -0.1007 | -0.1534 | -0.0481 | 0.0002 |
| primary     | HybridLocAgent       | all    | cfr10                   | mixedlm_powell     |      781 |             -0.0951 | -0.1527 | -0.0374 | 0.0012 |
| primary     | HybridLocAgent       | all    | top10                   | mixedlm_powell     |      781 |              0.0265 | -0.0308 |  0.0838 | 0.3653 |
| primary     | HybridLocAgent       | all    | rr10                    | mixedlm_powell     |      781 |             -0.0238 | -0.0856 |  0.0381 | 0.4517 |
| primary     | HybridLocAgent       | all    | top10 (logit, log-odds) | logit_project_fe   |      781 |              0.1317 | -0.4501 |  0.7134 | 0.6574 |
| primary     | HybridLocAgent       | parse  | ap10                    | mixedlm_powell     |      781 |             -0.1696 | -0.2212 | -0.118  | 0      |
| primary     | HybridLocAgent       | parse  | cfr10                   | mixedlm_powell     |      781 |             -0.2221 | -0.2757 | -0.1685 | 0      |
| primary     | HybridLocAgent       | parse  | top10                   | mixedlm_powell     |      781 |             -0.0288 | -0.0857 |  0.028  | 0.3199 |
| primary     | HybridLocAgent       | parse  | rr10                    | mixedlm_lbfgs      |      781 |             -0.0256 | -0.0895 |  0.0383 | 0.4327 |
| primary     | HybridLocAgent       | parse  | top10 (logit, log-odds) | logit_project_fe   |      781 |             -0.3601 | -0.8978 |  0.1776 | 0.1893 |
| primary     | HybridSweRank        | all    | ap                      | mixedlm_powell     |      781 |             -0.1099 | -0.1638 | -0.0561 | 0.0001 |
| primary     | HybridSweRank        | all    | cfr10                   | mixedlm_powell     |      781 |             -0.1233 | -0.1806 | -0.066  | 0      |
| primary     | HybridSweRank        | all    | rr                      | mixedlm_powell     |      781 |             -0.0307 | -0.0943 |  0.0329 | 0.3436 |
| primary     | HybridSweRank        | all    | top10                   | mixedlm_powell     |      781 |             -0.0067 | -0.0664 |  0.053  | 0.8267 |
| primary     | HybridSweRank        | all    | top10 (logit, log-odds) | logit_project_fe   |      781 |             -0.1599 | -0.6926 |  0.3728 | 0.5563 |
| primary     | HybridSweRank        | parse  | ap                      | mixedlm_powell     |      781 |             -0.186  | -0.2378 | -0.1341 | 0      |
| primary     | HybridSweRank        | parse  | cfr10                   | mixedlm_powell     |      781 |             -0.2126 | -0.2669 | -0.1583 | 0      |
| primary     | HybridSweRank        | parse  | rr                      | mixedlm_powell     |      781 |             -0.0314 | -0.0953 |  0.0324 | 0.3347 |
| primary     | HybridSweRank        | parse  | top10                   | mixedlm_lbfgs      |      781 |             -0.0256 | -0.0847 |  0.0336 | 0.3973 |
| primary     | HybridSweRank        | parse  | top10 (logit, log-odds) | logit_project_fe   |      781 |             -0.3155 | -0.84   |  0.2091 | 0.2385 |
| primary     | LocAgent             | all    | ap10                    | mixedlm_powell     |      781 |             -0.1629 | -0.2113 | -0.1145 | 0      |
| primary     | LocAgent             | all    | cfr10                   | mixedlm_powell     |      781 |             -0.1852 | -0.2356 | -0.1348 | 0      |
| primary     | LocAgent             | all    | top10                   | mixedlm_powell     |      781 |             -0.0569 | -0.1239 |  0.01   | 0.0956 |
| primary     | LocAgent             | all    | rr10                    | mixedlm_powell     |      781 |             -0.0532 | -0.1235 |  0.0171 | 0.1383 |
| primary     | LocAgent             | all    | top10 (logit, log-odds) | logit_project_fe   |      781 |             -0.3985 | -0.848  |  0.051  | 0.0823 |
| primary     | LocAgent             | parse  | ap10                    | mixedlm_powell     |      781 |             -0.1628 | -0.211  | -0.1145 | 0      |
| primary     | LocAgent             | parse  | cfr10                   | mixedlm_powell     |      781 |             -0.1846 | -0.2349 | -0.1344 | 0      |
| primary     | LocAgent             | parse  | top10                   | mixedlm_powell     |      781 |             -0.0569 | -0.1239 |  0.0102 | 0.0965 |
| primary     | LocAgent             | parse  | rr10                    | mixedlm_powell     |      781 |             -0.0539 | -0.1242 |  0.0163 | 0.1326 |
| primary     | LocAgent             | parse  | top10 (logit, log-odds) | logit_project_fe   |      781 |             -0.3928 | -0.842  |  0.0563 | 0.0865 |
| primary     | LocAgentRep          | all    | ap                      | mixedlm_lbfgs      |       74 |             -0.2864 | -0.4435 | -0.1293 | 0.0004 |
| primary     | LocAgentRep          | all    | cfr10                   | mixedlm_lbfgs      |       74 |             -0.324  | -0.4671 | -0.1809 | 0      |
| primary     | LocAgentRep          | all    | rr                      | mixedlm_powell     |       74 |             -0.1319 | -0.3758 |  0.1121 | 0.2894 |
| primary     | LocAgentRep          | all    | top10                   | mixedlm_powell     |       74 |             -0.1546 | -0.3868 |  0.0775 | 0.1918 |
| primary     | LocAgentRep          | all    | top10 (logit, log-odds) | logit_project_fe   |       74 |             -1.9143 | -3.9465 |  0.1179 | 0.0649 |
| primary     | LocAgentRep          | parse  | ap                      | mixedlm_lbfgs      |       74 |             -0.2907 | -0.4481 | -0.1334 | 0.0003 |
| primary     | LocAgentRep          | parse  | cfr10                   | mixedlm_lbfgs      |       74 |             -0.327  | -0.4708 | -0.1832 | 0      |
| primary     | LocAgentRep          | parse  | rr                      | mixedlm_powell     |       74 |             -0.1478 | -0.3874 |  0.0919 | 0.2269 |
| primary     | LocAgentRep          | parse  | top10                   | mixedlm_powell     |       74 |             -0.1723 | -0.399  |  0.0544 | 0.1362 |
| primary     | LocAgentRep          | parse  | top10 (logit, log-odds) | logit_project_fe   |       74 |             -1.895  | -3.921  |  0.131  | 0.0668 |
| primary     | SweRank              | all    | ap                      | mixedlm_lbfgs      |      781 |             -0.1719 | -0.2216 | -0.1222 | 0      |
| primary     | SweRank              | all    | cfr10                   | mixedlm_powell     |      781 |             -0.1899 | -0.239  | -0.1408 | 0      |
| primary     | SweRank              | all    | rr                      | mixedlm_powell     |      781 |             -0.0398 | -0.1106 |  0.0311 | 0.2713 |
| primary     | SweRank              | all    | top10                   | mixedlm_powell     |      781 |             -0.0285 | -0.0925 |  0.0355 | 0.383  |
| primary     | SweRank              | all    | ap10                    | mixedlm_powell     |      781 |             -0.1675 | -0.2176 | -0.1174 | 0      |
| primary     | SweRank              | all    | rr10                    | mixedlm_powell     |      781 |             -0.0383 | -0.1098 |  0.0333 | 0.2946 |
| primary     | SweRank              | all    | top10 (logit, log-odds) | logit_project_fe   |      781 |             -0.3409 | -0.8319 |  0.15   | 0.1735 |
| primary     | SweRank              | parse  | ap                      | mixedlm_powell     |      781 |             -0.1717 | -0.2213 | -0.1222 | 0      |
| primary     | SweRank              | parse  | cfr10                   | mixedlm_powell     |      781 |             -0.1891 | -0.238  | -0.1401 | 0      |
| primary     | SweRank              | parse  | rr                      | mixedlm_powell     |      781 |             -0.0419 | -0.1106 |  0.0267 | 0.2315 |
| primary     | SweRank              | parse  | top10                   | mixedlm_lbfgs      |      781 |             -0.0321 | -0.0944 |  0.0301 | 0.3118 |
| primary     | SweRank              | parse  | ap10                    | mixedlm_powell     |      781 |             -0.1666 | -0.2166 | -0.1167 | 0      |
| primary     | SweRank              | parse  | rr10                    | mixedlm_powell     |      781 |             -0.0406 | -0.11   |  0.0288 | 0.2512 |
| primary     | SweRank              | parse  | top10 (logit, log-odds) | logit_project_fe   |      781 |             -0.3313 | -0.822  |  0.1593 | 0.1857 |
| primary     | SweRankAll           | all    | ap                      | mixedlm_powell     |      781 |             -0.0445 | -0.1019 |  0.013  | 0.1291 |
| primary     | SweRankAll           | all    | cfr10                   | mixedlm_lbfgs      |      781 |             -0.0093 | -0.068  |  0.0494 | 0.7566 |
| primary     | SweRankAll           | all    | rr                      | mixedlm_lbfgs      |      781 |              0.0404 | -0.0321 |  0.1129 | 0.2746 |
| primary     | SweRankAll           | all    | top10                   | mixedlm_powell     |      781 |              0.0256 | -0.0304 |  0.0815 | 0.3706 |
| primary     | SweRankAll           | all    | ap10                    | mixedlm_powell     |      781 |             -0.0467 | -0.1057 |  0.0123 | 0.1207 |
| primary     | SweRankAll           | all    | rr10                    | mixedlm_powell     |      781 |              0.0408 | -0.0324 |  0.114  | 0.275  |
| primary     | SweRankAll           | all    | top10 (logit, log-odds) | logit_project_fe   |      781 |              0.1681 | -0.4129 |  0.7492 | 0.5706 |
| primary     | SweRankAll           | parse  | ap                      | mixedlm_powell     |      781 |             -0.1958 | -0.2506 | -0.1411 | 0      |
| primary     | SweRankAll           | parse  | cfr10                   | mixedlm_powell     |      781 |             -0.2327 | -0.2869 | -0.1785 | 0      |
| primary     | SweRankAll           | parse  | rr                      | mixedlm_powell     |      781 |             -0.0141 | -0.0801 |  0.0519 | 0.6757 |
| primary     | SweRankAll           | parse  | top10                   | mixedlm_powell     |      781 |             -0.0421 | -0.0983 |  0.014  | 0.1414 |
| primary     | SweRankAll           | parse  | ap10                    | mixedlm_lbfgs      |      781 |             -0.1811 | -0.2371 | -0.125  | 0      |
| primary     | SweRankAll           | parse  | rr10                    | mixedlm_powell     |      781 |             -0.0147 | -0.0817 |  0.0523 | 0.6673 |
| primary     | SweRankAll           | parse  | top10 (logit, log-odds) | logit_project_fe   |      781 |             -0.5335 | -1.0869 |  0.0199 | 0.0588 |
| primary     | SweRankEmbed         | all    | ap                      | mixedlm_powell     |      781 |             -0.1723 | -0.2199 | -0.1247 | 0      |
| primary     | SweRankEmbed         | all    | cfr10                   | mixedlm_powell     |      781 |             -0.1921 | -0.2425 | -0.1418 | 0      |
| primary     | SweRankEmbed         | all    | rr                      | mixedlm_powell     |      781 |             -0.0718 | -0.1428 | -0.0009 | 0.0473 |
| primary     | SweRankEmbed         | all    | top10                   | mixedlm_powell     |      781 |             -0.0503 | -0.1193 |  0.0188 | 0.1535 |
| primary     | SweRankEmbed         | all    | ap10                    | mixedlm_powell     |      781 |             -0.166  | -0.2143 | -0.1178 | 0      |
| primary     | SweRankEmbed         | all    | rr10                    | mixedlm_powell     |      781 |             -0.0712 | -0.1432 |  0.0008 | 0.0525 |
| primary     | SweRankEmbed         | all    | top10 (logit, log-odds) | logit_project_fe   |      781 |             -0.4635 | -0.921  | -0.0059 | 0.0471 |
| primary     | SweRankEmbed         | parse  | ap                      | mixedlm_powell     |      781 |             -0.1724 | -0.2198 | -0.1249 | 0      |
| primary     | SweRankEmbed         | parse  | cfr10                   | mixedlm_powell     |      781 |             -0.1913 | -0.2415 | -0.1411 | 0      |
| primary     | SweRankEmbed         | parse  | rr                      | mixedlm_powell     |      781 |             -0.0749 | -0.1448 | -0.005  | 0.0356 |
| primary     | SweRankEmbed         | parse  | top10                   | mixedlm_powell     |      781 |             -0.0555 | -0.1221 |  0.0111 | 0.1021 |
| primary     | SweRankEmbed         | parse  | ap10                    | mixedlm_powell     |      781 |             -0.1653 | -0.2134 | -0.1172 | 0      |
| primary     | SweRankEmbed         | parse  | rr10                    | mixedlm_powell     |      781 |             -0.0744 | -0.1452 | -0.0035 | 0.0398 |
| primary     | SweRankEmbed         | parse  | top10 (logit, log-odds) | logit_project_fe   |      781 |             -0.4547 | -0.912  |  0.0025 | 0.0513 |
| primary     | SweRankEmbedAll      | all    | ap                      | mixedlm_powell     |      781 |             -0.0632 | -0.1211 | -0.0053 | 0.0323 |
| primary     | SweRankEmbedAll      | all    | cfr10                   | mixedlm_powell     |      781 |             -0.0272 | -0.1033 |  0.049  | 0.4842 |
| primary     | SweRankEmbedAll      | all    | rr                      | mixedlm_powell     |      781 |             -0.0273 | -0.0959 |  0.0412 | 0.4342 |
| primary     | SweRankEmbedAll      | all    | top10                   | ols_project_fe_hc3 |      781 |              0.028  | -0.0391 |  0.0951 | 0.413  |
| primary     | SweRankEmbedAll      | all    | ap10                    | mixedlm_powell     |      781 |             -0.0687 | -0.1286 | -0.0088 | 0.0246 |
| primary     | SweRankEmbedAll      | all    | rr10                    | mixedlm_powell     |      781 |             -0.0264 | -0.0963 |  0.0436 | 0.46   |
| primary     | SweRankEmbedAll      | all    | top10 (logit, log-odds) | logit_project_fe   |      781 |              0.1646 | -0.3493 |  0.6785 | 0.5302 |
| primary     | SweRankEmbedAll      | parse  | ap                      | mixedlm_powell     |      781 |             -0.2075 | -0.262  | -0.153  | 0      |
| primary     | SweRankEmbedAll      | parse  | cfr10                   | mixedlm_powell     |      781 |             -0.216  | -0.2742 | -0.1578 | 0      |
| primary     | SweRankEmbedAll      | parse  | rr                      | mixedlm_powell     |      781 |             -0.078  | -0.1456 | -0.0103 | 0.0238 |
| primary     | SweRankEmbedAll      | parse  | top10                   | mixedlm_powell     |      781 |             -0.0298 | -0.0909 |  0.0312 | 0.3382 |
| primary     | SweRankEmbedAll      | parse  | ap10                    | mixedlm_powell     |      781 |             -0.1913 | -0.2473 | -0.1353 | 0      |
| primary     | SweRankEmbedAll      | parse  | rr10                    | mixedlm_lbfgs      |      781 |             -0.078  | -0.1468 | -0.0092 | 0.0263 |
| primary     | SweRankEmbedAll      | parse  | top10 (logit, log-odds) | logit_project_fe   |      781 |             -0.354  | -0.8634 |  0.1554 | 0.1731 |
| primary     | SweRankEmbedAllCap10 | all    | ap                      | mixedlm_powell     |      781 |             -0.0741 | -0.1301 | -0.0181 | 0.0095 |
| primary     | SweRankEmbedAllCap10 | all    | cfr10                   | mixedlm_powell     |      781 |             -0.0434 | -0.1047 |  0.0179 | 0.1656 |
| primary     | SweRankEmbedAllCap10 | all    | rr                      | mixedlm_powell     |      781 |             -0.0311 | -0.1005 |  0.0383 | 0.3801 |
| primary     | SweRankEmbedAllCap10 | all    | top10                   | mixedlm_powell     |      781 |              0.0459 | -0.0225 |  0.1144 | 0.1883 |
| primary     | SweRankEmbedAllCap10 | all    | ap10                    | mixedlm_powell     |      781 |             -0.0779 | -0.1356 | -0.0202 | 0.0082 |
| primary     | SweRankEmbedAllCap10 | all    | rr10                    | mixedlm_powell     |      781 |             -0.029  | -0.0999 |  0.0418 | 0.422  |
| primary     | SweRankEmbedAllCap10 | all    | top10 (logit, log-odds) | logit_project_fe   |      781 |              0.2533 | -0.2599 |  0.7666 | 0.3334 |
| primary     | SweRankEmbedAllCap10 | parse  | ap                      | mixedlm_powell     |      781 |             -0.1984 | -0.252  | -0.1448 | 0      |
| primary     | SweRankEmbedAllCap10 | parse  | cfr10                   | mixedlm_powell     |      781 |             -0.2158 | -0.2727 | -0.1589 | 0      |
| primary     | SweRankEmbedAllCap10 | parse  | rr                      | mixedlm_powell     |      781 |             -0.0719 | -0.1398 | -0.0039 | 0.0383 |
| primary     | SweRankEmbedAllCap10 | parse  | top10                   | mixedlm_powell     |      781 |             -0.0323 | -0.0945 |  0.0299 | 0.3094 |
| primary     | SweRankEmbedAllCap10 | parse  | ap10                    | mixedlm_lbfgs      |      781 |             -0.183  | -0.238  | -0.128  | 0      |
| primary     | SweRankEmbedAllCap10 | parse  | rr10                    | mixedlm_powell     |      781 |             -0.0712 | -0.1404 | -0.002  | 0.0438 |
| primary     | SweRankEmbedAllCap10 | parse  | top10 (logit, log-odds) | logit_project_fe   |      781 |             -0.3495 | -0.8471 |  0.1482 | 0.1688 |
| primary     | SweRankEmbedNonPy    | all    | ap                      | mixedlm_lbfgs      |      781 |             -0.0226 | -0.073  |  0.0278 | 0.3801 |
| primary     | SweRankEmbedNonPy    | all    | cfr10                   | mixedlm_powell     |      781 |              0.0327 | -0.0223 |  0.0876 | 0.2441 |
| primary     | SweRankEmbedNonPy    | all    | rr                      | mixedlm_powell     |      781 |             -0.0019 | -0.1611 |  0.1574 | 0.9817 |
| primary     | SweRankEmbedNonPy    | all    | top10                   | mixedlm_powell     |      781 |              0.0654 | -0.0139 |  0.1447 | 0.1058 |
| primary     | SweRankEmbedNonPy    | all    | ap10                    | mixedlm_powell     |      781 |             -0.0304 | -0.0816 |  0.0208 | 0.2446 |
| primary     | SweRankEmbedNonPy    | all    | rr10                    | mixedlm_powell     |      781 |             -0.0009 | -0.1376 |  0.1357 | 0.9893 |
| primary     | SweRankEmbedNonPy    | all    | top10 (logit, log-odds) | logit_project_fe   |      781 |              0.5396 |  0.0582 |  1.021  | 0.028  |
| primary     | SweRankEmbedNonPy    | parse  | ap                      | mixedlm_powell     |      781 |             -0.1726 | -0.2202 | -0.125  | 0      |
| primary     | SweRankEmbedNonPy    | parse  | cfr10                   | mixedlm_powell     |      781 |             -0.1922 | -0.2424 | -0.142  | 0      |
| primary     | SweRankEmbedNonPy    | parse  | rr                      | mixedlm_powell     |      781 |             -0.0734 | -0.1432 | -0.0036 | 0.0393 |
| primary     | SweRankEmbedNonPy    | parse  | top10                   | mixedlm_powell     |      781 |             -0.0555 | -0.1221 |  0.0111 | 0.1021 |
| primary     | SweRankEmbedNonPy    | parse  | ap10                    | mixedlm_powell     |      781 |             -0.1657 | -0.214  | -0.1175 | 0      |
| primary     | SweRankEmbedNonPy    | parse  | rr10                    | mixedlm_powell     |      781 |             -0.0729 | -0.1437 | -0.002  | 0.0438 |
| primary     | SweRankEmbedNonPy    | parse  | top10 (logit, log-odds) | logit_project_fe   |      781 |             -0.4547 | -0.912  |  0.0025 | 0.0513 |
| primary     | SweRankEmbedPyTest   | all    | ap                      | mixedlm_powell     |      781 |             -0.2069 | -0.2631 | -0.1506 | 0      |
| primary     | SweRankEmbedPyTest   | all    | cfr10                   | ols_project_fe_hc3 |      781 |             -0.2204 | -0.2759 | -0.165  | 0      |
| primary     | SweRankEmbedPyTest   | all    | rr                      | mixedlm_powell     |      781 |             -0.0686 | -0.1379 |  0.0008 | 0.0527 |
| primary     | SweRankEmbedPyTest   | all    | top10                   | mixedlm_powell     |      781 |             -0.0154 | -0.0795 |  0.0486 | 0.6366 |
| primary     | SweRankEmbedPyTest   | all    | ap10                    | mixedlm_powell     |      781 |             -0.191  | -0.2488 | -0.1332 | 0      |
| primary     | SweRankEmbedPyTest   | all    | rr10                    | mixedlm_powell     |      781 |             -0.0679 | -0.1383 |  0.0026 | 0.0591 |
| primary     | SweRankEmbedPyTest   | all    | top10 (logit, log-odds) | logit_project_fe   |      781 |             -0.2685 | -0.7716 |  0.2347 | 0.2956 |
| primary     | SweRankEmbedPyTest   | parse  | ap                      | mixedlm_powell     |      781 |             -0.2101 | -0.2654 | -0.1549 | 0      |
| primary     | SweRankEmbedPyTest   | parse  | cfr10                   | ols_project_fe_hc3 |      781 |             -0.2203 | -0.2758 | -0.1649 | 0      |
| primary     | SweRankEmbedPyTest   | parse  | rr                      | mixedlm_powell     |      781 |             -0.0718 | -0.1401 | -0.0036 | 0.0391 |
| primary     | SweRankEmbedPyTest   | parse  | top10                   | mixedlm_powell     |      781 |             -0.0198 | -0.0819 |  0.0423 | 0.5328 |
| primary     | SweRankEmbedPyTest   | parse  | ap10                    | mixedlm_powell     |      781 |             -0.1939 | -0.2506 | -0.1373 | 0      |
| primary     | SweRankEmbedPyTest   | parse  | rr10                    | mixedlm_powell     |      781 |             -0.0712 | -0.1405 | -0.0018 | 0.0443 |
| primary     | SweRankEmbedPyTest   | parse  | top10 (logit, log-odds) | logit_project_fe   |      781 |             -0.2648 | -0.7674 |  0.2379 | 0.3019 |

## RQ4 — inversion test (d = A - B; interaction = Poly-fix minus Mono-fix difference)

| condition   | pair                                                         | outcome   | model              |   n_bugs |   interaction_poly |   ci_lo |   ci_hi |      p |   mean_diff_mono |   mean_diff_poly | inversion_pattern   |
|:------------|:-------------------------------------------------------------|:----------|:-------------------|---------:|-------------------:|--------:|--------:|-------:|-----------------:|-----------------:|:--------------------|
| primary     | BM25 vs FLIM-strict                                          | ap        | mixedlm_lbfgs      |     1399 |             0.1075 |  0.0676 |  0.1473 | 0      |          -0.0586 |           0.0289 | True                |
| primary     | BM25 vs FLIM-strict                                          | cfr10     | mixedlm_lbfgs      |     1399 |             0.1501 |  0.099  |  0.2012 | 0      |          -0.0841 |           0.0457 | True                |
| primary     | BM25 vs FLIM-strict                                          | rr        | mixedlm_powell     |     1399 |             0.0402 | -0.0128 |  0.0932 | 0.1368 |          -0.0769 |          -0.0773 | False               |
| primary     | BM25 vs FLIM-strict                                          | top10     | mixedlm_lbfgs      |     1399 |             0.0961 |  0.0305 |  0.1617 | 0.0041 |          -0.0992 |          -0.0423 | False               |
| primary     | BM25 vs FLIM-fallback                                        | ap        | mixedlm_powell     |     1399 |             0.0788 |  0.0396 |  0.118  | 0.0001 |          -0.054  |           0.0024 | True                |
| primary     | BM25 vs FLIM-fallback                                        | cfr10     | mixedlm_powell     |     1399 |             0.1109 |  0.0599 |  0.1618 | 0      |          -0.0739 |           0.018  | True                |
| primary     | BM25 vs FLIM-fallback                                        | rr        | mixedlm_powell     |     1399 |             0.038  | -0.015  |  0.091  | 0.1602 |          -0.0729 |          -0.0752 | False               |
| primary     | BM25 vs FLIM-fallback                                        | top10     | mixedlm_powell     |     1399 |             0.0879 |  0.0229 |  0.1529 | 0.0081 |          -0.0866 |          -0.0375 | False               |
| primary     | BM25-parse vs FLIM-strict (control)                          | ap        | mixedlm_lbfgs      |     1399 |             0.0043 | -0.0348 |  0.0434 | 0.8294 |          -0.0093 |          -0.0258 | False               |
| primary     | BM25-parse vs FLIM-strict (control)                          | cfr10     | mixedlm_powell     |     1399 |             0.0172 | -0.0319 |  0.0663 | 0.4916 |          -0.0408 |          -0.0349 | False               |
| primary     | BM25-parse vs FLIM-strict (control)                          | rr        | ols_project_fe_hc3 |     1399 |            -0.018  | -0.0734 |  0.0375 | 0.5258 |          -0.0171 |          -0.0674 | False               |
| primary     | BM25-parse vs FLIM-strict (control)                          | top10     | mixedlm_powell     |     1399 |             0.0088 | -0.054  |  0.0716 | 0.7838 |          -0.0483 |          -0.0614 | False               |
| primary     | BM25 vs LocAgent                                             | ap10      | mixedlm_powell     |      781 |             0.137  |  0.0753 |  0.1988 | 0      |          -0.1141 |           0.0365 | True                |
| primary     | BM25 vs LocAgent                                             | cfr10     | mixedlm_powell     |      781 |             0.1466 |  0.0738 |  0.2194 | 0.0001 |          -0.0073 |           0.1431 | True                |
| primary     | BM25 vs LocAgent                                             | top10     | mixedlm_powell     |      781 |             0.0804 | -0.008  |  0.1687 | 0.0745 |          -0.1255 |          -0.0258 | False               |
| primary     | BM25 vs LocAgent                                             | rr10      | mixedlm_powell     |      781 |             0.0967 |  0.0157 |  0.1777 | 0.0193 |          -0.246  |          -0.1442 | False               |
| primary     | BM25 vs SweRank                                              | ap        | mixedlm_powell     |      781 |             0.1431 |  0.081  |  0.2052 | 0      |          -0.1131 |           0.0418 | True                |
| primary     | BM25 vs SweRank                                              | cfr10     | mixedlm_powell     |      781 |             0.1506 |  0.0769 |  0.2243 | 0.0001 |          -0.0182 |           0.1127 | True                |
| primary     | BM25 vs SweRank                                              | rr        | mixedlm_powell     |      781 |             0.0838 |  0.0043 |  0.1634 | 0.0389 |          -0.2643 |          -0.1867 | False               |
| primary     | BM25 vs SweRank                                              | top10     | mixedlm_powell     |      781 |             0.0502 | -0.0386 |  0.1389 | 0.2677 |          -0.149  |          -0.0886 | False               |
| primary     | BM25 vs SweRank (top-10)                                     | ap10      | mixedlm_powell     |      781 |             0.1404 |  0.0769 |  0.2039 | 0      |          -0.1301 |           0.0173 | True                |
| primary     | BM25 vs SweRank (top-10)                                     | cfr10     | mixedlm_powell     |      781 |             0.1506 |  0.0769 |  0.2243 | 0.0001 |          -0.0182 |           0.1127 | True                |
| primary     | BM25 vs SweRank (top-10)                                     | top10     | mixedlm_powell     |      781 |             0.0502 | -0.0386 |  0.1389 | 0.2677 |          -0.149  |          -0.0886 | False               |
| primary     | BM25 vs SweRank (top-10)                                     | rr10      | mixedlm_powell     |      781 |             0.0825 |  0.0016 |  0.1634 | 0.0455 |          -0.2707 |          -0.1932 | False               |
| primary     | SweRankEmbed vs SweRank (reranker effect)                    | ap        | ols_project_fe_hc3 |      781 |             0.0012 | -0.0253 |  0.0278 | 0.9269 |          -0.0624 |          -0.0503 | False               |
| primary     | SweRankEmbed vs SweRank (reranker effect)                    | cfr10     | ols_project_fe_hc3 |      781 |            -0.0028 | -0.0226 |  0.0171 | 0.7852 |          -0.0258 |          -0.0256 | False               |
| primary     | SweRankEmbed vs SweRank (reranker effect)                    | rr        | ols_project_fe_hc3 |      781 |            -0.024  | -0.072  |  0.0239 | 0.3258 |          -0.0836 |          -0.1156 | False               |
| primary     | SweRankEmbed vs SweRank (reranker effect)                    | top10     | ols_project_fe_hc3 |      781 |            -0.0225 | -0.0524 |  0.0073 | 0.1395 |          -0.0255 |          -0.0406 | False               |
| primary     | HybridFLIM vs FLIM-strict                                    | ap        | mixedlm_powell     |     1399 |             0.0818 |  0.0711 |  0.0925 | 0      |          -0.0209 |           0.0513 | True                |
| primary     | HybridFLIM vs FLIM-strict                                    | cfr10     | mixedlm_powell     |     1399 |             0.0827 |  0.0654 |  0.1    | 0      |          -0.0173 |           0.0564 | True                |
| primary     | HybridFLIM vs FLIM-strict                                    | rr        | mixedlm_lbfgs      |     1399 |             0.009  | -0.0039 |  0.0218 | 0.171  |          -0.021  |          -0.0349 | False               |
| primary     | HybridFLIM vs FLIM-strict                                    | top10     | mixedlm_powell     |     1399 |             0.0279 |  0.0057 |  0.0502 | 0.0137 |          -0.0136 |           0.0056 | True                |
| primary     | HybridSweRank vs SweRank                                     | ap        | mixedlm_powell     |      781 |             0.0588 |  0.0301 |  0.0874 | 0.0001 |           0.0318 |           0.1031 | False               |
| primary     | HybridSweRank vs SweRank                                     | cfr10     | mixedlm_powell     |      781 |             0.0647 |  0.0272 |  0.1021 | 0.0007 |           0.0801 |           0.1567 | False               |
| primary     | HybridSweRank vs SweRank                                     | rr        | mixedlm_powell     |      781 |             0.0143 | -0.0143 |  0.0428 | 0.3275 |          -0.0533 |          -0.0658 | False               |
| primary     | HybridSweRank vs SweRank                                     | top10     | ols_project_fe_hc3 |      781 |             0.0245 | -0.0167 |  0.0657 | 0.2441 |           0.0098 |           0.0406 | False               |
| primary     | HybridLocAgent vs LocAgent                                   | ap10      | mixedlm_powell     |      781 |             0.0615 |  0.0314 |  0.0916 | 0.0001 |           0.0319 |           0.0956 | False               |
| primary     | HybridLocAgent vs LocAgent                                   | cfr10     | mixedlm_powell     |      781 |             0.0837 |  0.0405 |  0.1269 | 0.0001 |           0.1436 |           0.2225 | False               |
| primary     | HybridLocAgent vs LocAgent                                   | top10     | mixedlm_powell     |      781 |             0.0761 |  0.0302 |  0.1221 | 0.0012 |           0.049  |           0.1292 | False               |
| primary     | HybridLocAgent vs LocAgent                                   | rr10      | mixedlm_powell     |      781 |             0.0286 | -0.0023 |  0.0594 | 0.0699 |          -0.0522 |          -0.0387 | False               |
| primary     | BM25 vs HybridFLIM                                           | ap        | mixedlm_powell     |     1399 |             0.0296 | -0.0101 |  0.0693 | 0.1441 |          -0.0377 |          -0.0224 | False               |
| primary     | BM25 vs HybridFLIM                                           | cfr10     | mixedlm_powell     |     1399 |             0.0706 |  0.0224 |  0.1187 | 0.0041 |          -0.0669 |          -0.0106 | False               |
| primary     | BM25 vs HybridFLIM                                           | rr        | mixedlm_powell     |     1399 |             0.0345 | -0.0184 |  0.0873 | 0.2012 |          -0.0559 |          -0.0424 | False               |
| primary     | BM25 vs HybridFLIM                                           | top10     | mixedlm_powell     |     1399 |             0.0683 |  0.0047 |  0.132  | 0.0353 |          -0.0856 |          -0.0478 | False               |
| primary     | BM25 vs HybridSweRank                                        | ap        | mixedlm_powell     |      781 |             0.0848 |  0.0336 |  0.136  | 0.0012 |          -0.1449 |          -0.0613 | False               |
| primary     | BM25 vs HybridSweRank                                        | cfr10     | mixedlm_powell     |      781 |             0.0871 |  0.0244 |  0.1498 | 0.0065 |          -0.0983 |          -0.044  | False               |
| primary     | BM25 vs HybridSweRank                                        | rr        | mixedlm_powell     |      781 |             0.0723 | -0.0014 |  0.1461 | 0.0546 |          -0.211  |          -0.1209 | False               |
| primary     | BM25 vs HybridSweRank                                        | top10     | mixedlm_powell     |      781 |             0.031  | -0.0492 |  0.1112 | 0.4493 |          -0.1588 |          -0.1292 | False               |
| primary     | BM25 vs HybridLocAgent                                       | ap10      | mixedlm_powell     |      781 |             0.0748 |  0.026  |  0.1235 | 0.0026 |          -0.146  |          -0.0592 | False               |
| primary     | BM25 vs HybridLocAgent                                       | cfr10     | mixedlm_powell     |      781 |             0.0587 |  0.0066 |  0.1108 | 0.0273 |          -0.1509 |          -0.0794 | False               |
| primary     | BM25 vs HybridLocAgent                                       | top10     | mixedlm_powell     |      781 |             0.0013 | -0.0839 |  0.0864 | 0.9766 |          -0.1745 |          -0.155  | False               |
| primary     | BM25 vs HybridLocAgent                                       | rr10      | mixedlm_powell     |      781 |             0.0674 | -0.0056 |  0.1404 | 0.0704 |          -0.1938 |          -0.1055 | False               |
| primary     | BM25 vs SweRankEmbedAll                                      | ap        | mixedlm_powell     |      781 |             0.0328 | -0.0251 |  0.0908 | 0.2669 |          -0.1322 |          -0.0759 | False               |
| primary     | BM25 vs SweRankEmbedAll                                      | cfr10     | ols_project_fe_hc3 |      781 |            -0.0043 | -0.0749 |  0.0662 | 0.9045 |          -0.1329 |          -0.1108 | False               |
| primary     | BM25 vs SweRankEmbedAll                                      | rr        | mixedlm_powell     |      781 |             0.0683 | -0.0055 |  0.1422 | 0.0698 |          -0.1565 |          -0.0942 | False               |
| primary     | BM25 vs SweRankEmbedAll                                      | top10     | ols_project_fe_hc3 |      781 |             0.0035 | -0.0807 |  0.0877 | 0.9352 |          -0.1314 |          -0.1255 | False               |
| primary     | SweRankEmbed vs SweRankEmbedAll (corpus extension)           | ap        | mixedlm_powell     |      781 |             0.1081 |  0.0675 |  0.1488 | 0      |           0.0815 |           0.168  | False               |
| primary     | SweRankEmbed vs SweRankEmbedAll (corpus extension)           | cfr10     | mixedlm_powell     |      781 |             0.1581 |  0.1021 |  0.2141 | 0      |           0.1405 |           0.249  | False               |
| primary     | SweRankEmbed vs SweRankEmbedAll (corpus extension)           | rr        | ols_project_fe_hc3 |      781 |             0.0482 | -0.0051 |  0.1014 | 0.0763 |          -0.0242 |           0.0231 | True                |
| primary     | SweRankEmbed vs SweRankEmbedAll (corpus extension)           | top10     | ols_project_fe_hc3 |      781 |             0.0895 |  0.0205 |  0.1585 | 0.011  |           0.0078 |           0.0775 | False               |
| primary     | BM25 vs SweRankAll                                           | ap        | mixedlm_powell     |      781 |             0.0149 | -0.0424 |  0.0722 | 0.6113 |          -0.2186 |          -0.1563 | False               |
| primary     | BM25 vs SweRankAll                                           | cfr10     | mixedlm_powell     |      781 |            -0.0328 | -0.1037 |  0.038  | 0.364  |          -0.1752 |          -0.168  | False               |
| primary     | BM25 vs SweRankAll                                           | rr        | mixedlm_powell     |      781 |             0.0005 | -0.0729 |  0.0739 | 0.9884 |          -0.2571 |          -0.236  | False               |
| primary     | BM25 vs SweRankAll                                           | top10     | mixedlm_powell     |      781 |            -0.0041 | -0.0828 |  0.0747 | 0.9196 |          -0.1706 |          -0.155  | False               |
| primary     | SweRankEmbedNonPy vs SweRankEmbed (non-Python files added)   | ap        | mixedlm_powell     |      781 |             0.15   |  0.1284 |  0.1715 | 0      |          -0.0287 |           0.1082 | True                |
| primary     | SweRankEmbedNonPy vs SweRankEmbed (non-Python files added)   | cfr10     | mixedlm_powell     |      781 |             0.2222 |  0.1905 |  0.2538 | 0      |          -0.0197 |           0.1726 | True                |
| primary     | SweRankEmbedNonPy vs SweRankEmbed (non-Python files added)   | rr        | mixedlm_powell     |      781 |             0.0735 |  0.043  |  0.104  | 0      |          -0.0331 |           0.0283 | True                |
| primary     | SweRankEmbedNonPy vs SweRankEmbed (non-Python files added)   | top10     | mixedlm_lbfgs      |      781 |             0.1355 |  0.094  |  0.1769 | 0      |          -0.0275 |           0.0664 | True                |
| primary     | SweRankEmbedPyTest vs SweRankEmbed (Python test files added) | ap        | mixedlm_powell     |      781 |            -0.0396 | -0.0716 | -0.0076 | 0.0154 |           0.1109 |           0.0618 | False               |
| primary     | SweRankEmbedPyTest vs SweRankEmbed (Python test files added) | cfr10     | mixedlm_powell     |      781 |            -0.0279 | -0.0712 |  0.0153 | 0.206  |           0.1516 |           0.1046 | False               |
| primary     | SweRankEmbedPyTest vs SweRankEmbed (Python test files added) | rr        | ols_project_fe_hc3 |      781 |             0.0042 | -0.0352 |  0.0435 | 0.8361 |           0.0039 |           0.0136 | False               |
| primary     | SweRankEmbedPyTest vs SweRankEmbed (Python test files added) | top10     | ols_project_fe_hc3 |      781 |             0.0381 | -0.0157 |  0.0918 | 0.1649 |           0.0118 |           0.059  | False               |
| primary     | SweRankEmbedAllCap10 vs SweRankEmbedAll (10-chunk cap)       | ap        | mixedlm_powell     |      781 |            -0.0089 | -0.0216 |  0.0038 | 0.1681 |          -0.0149 |          -0.0233 | False               |
| primary     | SweRankEmbedAllCap10 vs SweRankEmbedAll (10-chunk cap)       | cfr10     | mixedlm_powell     |      781 |            -0.0127 | -0.0312 |  0.0057 | 0.1766 |          -0.0149 |          -0.0264 | False               |
| primary     | SweRankEmbedAllCap10 vs SweRankEmbedAll (10-chunk cap)       | rr        | mixedlm_lbfgs      |      781 |            -0.0068 | -0.0374 |  0.0238 | 0.6637 |          -0.0015 |          -0.0131 | False               |
| primary     | SweRankEmbedAllCap10 vs SweRankEmbedAll (10-chunk cap)       | top10     | ols_project_fe_hc3 |      781 |             0.0114 | -0.0066 |  0.0294 | 0.216  |          -0.0039 |           0      | True                |
| primary     | BM25 vs SweRankEmbedNonPy                                    | ap        | mixedlm_powell     |      781 |            -0.0061 | -0.0663 |  0.0541 | 0.8437 |          -0.022  |          -0.0162 | False               |
| primary     | BM25 vs SweRankEmbedNonPy                                    | cfr10     | mixedlm_powell     |      781 |            -0.0716 | -0.145  |  0.0018 | 0.0557 |           0.0273 |          -0.0343 | False               |
| primary     | BM25 vs SweRankEmbedNonPy                                    | rr        | mixedlm_powell     |      781 |             0.0408 | -0.036  |  0.1177 | 0.2977 |          -0.1476 |          -0.0994 | False               |
| primary     | BM25 vs SweRankEmbedNonPy                                    | top10     | ols_project_fe_hc3 |      781 |            -0.047  | -0.139  |  0.0451 | 0.3174 |          -0.0961 |          -0.1144 | False               |
| primary     | CoChangeFLIM vs FLIM-strict                                  | ap        | mixedlm_powell     |     1399 |             0.1081 |  0.0945 |  0.1217 | 0      |          -0.0453 |           0.0616 | True                |
| primary     | CoChangeFLIM vs FLIM-strict                                  | cfr10     | mixedlm_powell     |     1399 |             0.1221 |  0.1016 |  0.1426 | 0      |          -0.0306 |           0.0837 | True                |
| primary     | CoChangeFLIM vs FLIM-strict                                  | rr        | mixedlm_powell     |     1399 |             0.0054 | -0.0149 |  0.0257 | 0.6038 |          -0.0529 |          -0.0528 | False               |
| primary     | CoChangeFLIM vs FLIM-strict                                  | top10     | mixedlm_lbfgs      |     1399 |             0.0419 |  0.0156 |  0.0682 | 0.0018 |          -0.0296 |           0.0072 | True                |
| primary     | CoChangeSweRank vs SweRank                                   | ap        | mixedlm_powell     |      781 |             0.0911 |  0.0524 |  0.1298 | 0      |           0.021  |           0.1226 | False               |
| primary     | CoChangeSweRank vs SweRank                                   | cfr10     | mixedlm_powell     |      781 |             0.1108 |  0.0647 |  0.1569 | 0      |           0.1192 |           0.203  | False               |
| primary     | CoChangeSweRank vs SweRank                                   | rr        | mixedlm_powell     |      781 |             0.0478 |  0.0115 |  0.0841 | 0.0098 |          -0.169  |          -0.1072 | False               |
| primary     | CoChangeSweRank vs SweRank                                   | top10     | mixedlm_powell     |      781 |             0.0415 | -0.0018 |  0.0848 | 0.0606 |          -0.0039 |           0.0406 | True                |
| primary     | CoChangeLocAgent vs LocAgent                                 | ap10      | mixedlm_powell     |      781 |             0.0712 |  0.033  |  0.1093 | 0.0003 |          -0.0073 |           0.0607 | True                |
| primary     | CoChangeLocAgent vs LocAgent                                 | cfr10     | mixedlm_powell     |      781 |             0.0508 |  0.0096 |  0.092  | 0.0157 |           0.1577 |           0.197  | False               |
| primary     | CoChangeLocAgent vs LocAgent                                 | top10     | mixedlm_powell     |      781 |             0.0249 | -0.016  |  0.0659 | 0.2323 |           0.0373 |           0.0664 | False               |
| primary     | CoChangeLocAgent vs LocAgent                                 | rr10      | mixedlm_lbfgs      |      781 |             0.0369 |  0.0027 |  0.071  | 0.0343 |          -0.1926 |          -0.1514 | False               |
| primary     | BM25 vs CoChangeFLIM                                         | ap        | ols_project_fe_hc3 |     1399 |            -0.0032 | -0.0421 |  0.0356 | 0.8701 |          -0.0133 |          -0.0327 | False               |
| primary     | BM25 vs CoChangeFLIM                                         | cfr10     | mixedlm_powell     |     1399 |             0.0267 | -0.0245 |  0.0779 | 0.3073 |          -0.0535 |          -0.038  | False               |
| primary     | BM25 vs CoChangeFLIM                                         | rr        | mixedlm_powell     |     1399 |             0.034  | -0.0175 |  0.0855 | 0.1956 |          -0.024  |          -0.0244 | False               |
| primary     | BM25 vs CoChangeFLIM                                         | top10     | mixedlm_lbfgs      |     1399 |             0.0506 | -0.014  |  0.1153 | 0.1247 |          -0.0697 |          -0.0494 | False               |
| primary     | BM25 vs CoChangeSweRank                                      | ap        | ols_project_fe_hc3 |      781 |             0.055  | -0.0061 |  0.1161 | 0.0779 |          -0.1341 |          -0.0809 | False               |
| primary     | BM25 vs CoChangeSweRank                                      | cfr10     | ols_project_fe_hc3 |      781 |             0.0424 | -0.0358 |  0.1207 | 0.2881 |          -0.1375 |          -0.0904 | False               |
| primary     | BM25 vs CoChangeSweRank                                      | rr        | mixedlm_powell     |      781 |             0.0457 | -0.0267 |  0.1181 | 0.2157 |          -0.0954 |          -0.0795 | False               |
| primary     | BM25 vs CoChangeSweRank                                      | top10     | ols_project_fe_hc3 |      781 |             0.0257 | -0.0667 |  0.1182 | 0.5851 |          -0.1451 |          -0.1292 | False               |
| primary     | BM25 vs CoChangeLocAgent                                     | ap10      | mixedlm_powell     |      781 |             0.0827 |  0.0146 |  0.1507 | 0.0173 |          -0.1067 |          -0.0243 | False               |
| primary     | BM25 vs CoChangeLocAgent                                     | cfr10     | ols_project_fe_hc3 |      781 |             0.0969 |  0.0229 |  0.1709 | 0.0103 |          -0.165  |          -0.054  | False               |
| primary     | BM25 vs CoChangeLocAgent                                     | top10     | ols_project_fe_hc3 |      781 |             0.0638 | -0.0249 |  0.1526 | 0.1585 |          -0.1627 |          -0.0923 | False               |
| primary     | BM25 vs CoChangeLocAgent                                     | rr10      | mixedlm_lbfgs      |      781 |             0.0488 | -0.0251 |  0.1227 | 0.1953 |          -0.0535 |           0.0072 | True                |
| primary     | SweRankAll vs SweRank (corpus extension, reranked)           | ap        | mixedlm_powell     |      781 |             0.126  |  0.0841 |  0.1679 | 0      |           0.1055 |           0.1981 | False               |
| primary     | SweRankAll vs SweRank (corpus extension, reranked)           | cfr10     | mixedlm_lbfgs      |      781 |             0.1801 |  0.1246 |  0.2357 | 0      |           0.157  |           0.2806 | False               |
| primary     | SweRankAll vs SweRank (corpus extension, reranked)           | rr        | mixedlm_powell     |      781 |             0.0725 |  0.0263 |  0.1187 | 0.0021 |          -0.0072 |           0.0493 | True                |
| primary     | SweRankAll vs SweRank (corpus extension, reranked)           | top10     | ols_project_fe_hc3 |      781 |             0.0616 | -0.0099 |  0.1331 | 0.0915 |           0.0216 |           0.0664 | False               |
| primary     | BLAZE_ALL vs BLAZE (ablation)                                | ap        | mixedlm_powell     |      691 |             0.0009 | -0.0459 |  0.0477 | 0.9711 |          -0.0104 |          -0.0061 | False               |
| primary     | BLAZE_ALL vs BLAZE (ablation)                                | cfr10     | ols_project_fe_hc3 |      691 |             0.0033 | -0.0569 |  0.0635 | 0.9152 |          -0.0307 |          -0.0059 | False               |
| primary     | BLAZE_ALL vs BLAZE (ablation)                                | rr        | mixedlm_powell     |      691 |            -0.0236 | -0.09   |  0.0427 | 0.4852 |          -0.0034 |          -0.0126 | False               |
| primary     | BLAZE_ALL vs BLAZE (ablation)                                | top10     | ols_project_fe_hc3 |      691 |            -0.0934 | -0.1872 |  0.0004 | 0.051  |          -0.0028 |          -0.0563 | False               |

## Decomposition (primary condition)

| condition   | tech                 | view   | class    |   n_bugs |   MRR |   MAP |   CFR10 |   MRR_primary_gt |   MRR_secondary_gt |   MAP_primary_gt |   MAP_secondary_gt |   reach_at_parse |   all_gt_parseable |   random_MRR |   random_top10 |
|:------------|:---------------------|:-------|:---------|---------:|------:|------:|--------:|-----------------:|-------------------:|-----------------:|-------------------:|-----------------:|-------------------:|-------------:|---------------:|
| primary     | BLAZE                | all    | Mono-fix |      981 | 0.329 | 0.255 |   0.412 |            0.329 |            nan     |            0.255 |            nan     |            1     |              0.999 |        0.004 |          0.006 |
| primary     | BLAZE                | all    | Poly-fix |      418 | 0.396 | 0.244 |   0.363 |            0.361 |              0.114 |            0.279 |              0.109 |            0.983 |              0.105 |        0.009 |          0.013 |
| primary     | BLAZE                | parse  | Mono-fix |      981 | 0.348 | 0.273 |   0.43  |            0.348 |            nan     |            0.273 |            nan     |            1     |              0.999 |        0.006 |          0.009 |
| primary     | BLAZE                | parse  | Poly-fix |      418 | 0.395 | 0.191 |   0.292 |            0.402 |              0     |            0.315 |              0     |            0.983 |              0.105 |        0.009 |          0.014 |
| primary     | BLAZE_ALL            | all    | Mono-fix |      478 | 0.314 | 0.244 |   0.396 |            0.314 |            nan     |            0.244 |            nan     |            1     |              0.998 |        0.004 |          0.005 |
| primary     | BLAZE_ALL            | all    | Poly-fix |      213 | 0.389 | 0.227 |   0.335 |            0.36  |              0.104 |            0.269 |              0.097 |            0.981 |              0.108 |        0.008 |          0.011 |
| primary     | BLAZE_ALL            | parse  | Mono-fix |      478 | 0.334 | 0.26  |   0.406 |            0.334 |            nan     |            0.26  |            nan     |            1     |              0.998 |        0.005 |          0.007 |
| primary     | BLAZE_ALL            | parse  | Poly-fix |      213 | 0.383 | 0.178 |   0.265 |            0.39  |              0     |            0.297 |              0     |            0.981 |              0.108 |        0.008 |          0.012 |
| primary     | BM25                 | all    | Mono-fix |      981 | 0.389 | 0.311 |   0.471 |            0.389 |            nan     |            0.311 |            nan     |            1     |              0.999 |        0.004 |          0.006 |
| primary     | BM25                 | all    | Poly-fix |      418 | 0.436 | 0.274 |   0.401 |            0.357 |              0.185 |            0.277 |              0.167 |            0.983 |              0.105 |        0.009 |          0.013 |
| primary     | BM25                 | parse  | Mono-fix |      981 | 0.449 | 0.36  |   0.515 |            0.449 |            nan     |            0.36  |            nan     |            1     |              0.999 |        0.006 |          0.009 |
| primary     | BM25                 | parse  | Poly-fix |      418 | 0.445 | 0.219 |   0.32  |            0.453 |              0     |            0.351 |              0     |            0.983 |              0.105 |        0.009 |          0.014 |
| primary     | CoChangeFLIM         | all    | Mono-fix |      981 | 0.413 | 0.324 |   0.525 |            0.413 |            nan     |            0.324 |            nan     |            1     |              0.999 |        0.004 |          0.006 |
| primary     | CoChangeFLIM         | all    | Poly-fix |      418 | 0.46  | 0.306 |   0.439 |            0.436 |              0.172 |            0.322 |              0.15  |            0.983 |              0.105 |        0.009 |          0.013 |
| primary     | CoChangeFLIM         | parse  | Mono-fix |      981 | 0.466 | 0.37  |   0.555 |            0.466 |            nan     |            0.37  |            nan     |            1     |              0.999 |        0.006 |          0.009 |
| primary     | CoChangeFLIM         | parse  | Poly-fix |      418 | 0.513 | 0.245 |   0.355 |            0.522 |              0     |            0.395 |              0     |            0.983 |              0.105 |        0.009 |          0.014 |
| primary     | CoChangeLocAgent     | all    | Mono-fix |      510 | 0.497 | 0.464 |   0.715 |            0.497 |            nan     |            0.464 |            nan     |            1     |              0.998 |        0.005 |          0.008 |
| primary     | CoChangeLocAgent     | all    | Poly-fix |      271 | 0.488 | 0.344 |   0.512 |            0.488 |              0.095 |            0.434 |              0.087 |            0.985 |              0.1   |        0.009 |          0.015 |
| primary     | CoChangeLocAgent     | parse  | Mono-fix |      510 | 0.513 | 0.477 |   0.719 |            0.513 |            nan     |            0.477 |            nan     |            1     |              0.998 |        0.008 |          0.011 |
| primary     | CoChangeLocAgent     | parse  | Poly-fix |      271 | 0.503 | 0.28  |   0.434 |            0.511 |              0     |            0.458 |              0     |            0.985 |              0.1   |        0.01  |          0.016 |
| primary     | CoChangeSweRank      | all    | Mono-fix |      510 | 0.545 | 0.499 |   0.687 |            0.545 |            nan     |            0.499 |            nan     |            1     |              0.998 |        0.005 |          0.008 |
| primary     | CoChangeSweRank      | all    | Poly-fix |      271 | 0.579 | 0.4   |   0.549 |            0.571 |              0.136 |            0.49  |              0.122 |            0.985 |              0.1   |        0.009 |          0.015 |
| primary     | CoChangeSweRank      | parse  | Mono-fix |      510 | 0.575 | 0.524 |   0.698 |            0.575 |            nan     |            0.524 |            nan     |            1     |              0.998 |        0.008 |          0.011 |
| primary     | CoChangeSweRank      | parse  | Poly-fix |      271 | 0.618 | 0.326 |   0.422 |            0.628 |              0     |            0.542 |              0     |            0.985 |              0.1   |        0.01  |          0.016 |
| primary     | FLIM                 | all    | Mono-fix |      981 | 0.462 | 0.365 |   0.545 |            0.462 |            nan     |            0.365 |            nan     |            1     |              0.999 |        0.004 |          0.006 |
| primary     | FLIM                 | all    | Poly-fix |      418 | 0.511 | 0.271 |   0.383 |            0.509 |              0.05  |            0.381 |              0.042 |            0.983 |              0.105 |        0.009 |          0.013 |
| primary     | FLIM                 | parse  | Mono-fix |      981 | 0.466 | 0.37  |   0.555 |            0.466 |            nan     |            0.37  |            nan     |            1     |              0.999 |        0.006 |          0.009 |
| primary     | FLIM                 | parse  | Poly-fix |      418 | 0.513 | 0.245 |   0.355 |            0.522 |              0     |            0.395 |              0     |            0.983 |              0.105 |        0.009 |          0.014 |
| primary     | HybridFLIM           | all    | Mono-fix |      981 | 0.445 | 0.349 |   0.538 |            0.445 |            nan     |            0.349 |            nan     |            1     |              0.999 |        0.004 |          0.006 |
| primary     | HybridFLIM           | all    | Poly-fix |      418 | 0.478 | 0.296 |   0.412 |            0.458 |              0.14  |            0.335 |              0.128 |            0.983 |              0.105 |        0.009 |          0.013 |
| primary     | HybridFLIM           | parse  | Mono-fix |      981 | 0.466 | 0.37  |   0.555 |            0.466 |            nan     |            0.37  |            nan     |            1     |              0.999 |        0.006 |          0.009 |
| primary     | HybridFLIM           | parse  | Poly-fix |      418 | 0.513 | 0.245 |   0.355 |            0.522 |              0     |            0.395 |              0     |            0.983 |              0.105 |        0.009 |          0.014 |
| primary     | HybridLocAgent       | all    | Mono-fix |      510 | 0.638 | 0.505 |   0.7   |            0.638 |            nan     |            0.505 |            nan     |            1     |              0.998 |        0.005 |          0.008 |
| primary     | HybridLocAgent       | all    | Poly-fix |      271 | 0.599 | 0.379 |   0.538 |            0.588 |              0.12  |            0.487 |              0.109 |            0.985 |              0.1   |        0.009 |          0.015 |
| primary     | HybridLocAgent       | parse  | Mono-fix |      510 | 0.656 | 0.524 |   0.711 |            0.656 |            nan     |            0.524 |            nan     |            1     |              0.998 |        0.008 |          0.011 |
| primary     | HybridLocAgent       | parse  | Poly-fix |      271 | 0.622 | 0.317 |   0.437 |            0.631 |              0     |            0.527 |              0     |            0.985 |              0.1   |        0.01  |          0.016 |
| primary     | HybridSweRank        | all    | Mono-fix |      510 | 0.661 | 0.509 |   0.648 |            0.661 |            nan     |            0.509 |            nan     |            1     |              0.998 |        0.005 |          0.008 |
| primary     | HybridSweRank        | all    | Poly-fix |      271 | 0.62  | 0.38  |   0.502 |            0.616 |              0.108 |            0.505 |              0.098 |            0.985 |              0.1   |        0.009 |          0.015 |
| primary     | HybridSweRank        | parse  | Mono-fix |      510 | 0.681 | 0.528 |   0.654 |            0.681 |            nan     |            0.528 |            nan     |            1     |              0.998 |        0.008 |          0.011 |
| primary     | HybridSweRank        | parse  | Poly-fix |      271 | 0.657 | 0.329 |   0.422 |            0.667 |              0     |            0.547 |              0     |            0.985 |              0.1   |        0.01  |          0.016 |
| primary     | LocAgent             | all    | Mono-fix |      510 | 0.687 | 0.457 |   0.557 |            0.687 |            nan     |            0.457 |            nan     |            1     |              0.998 |        0.005 |          0.008 |
| primary     | LocAgent             | all    | Poly-fix |      271 | 0.635 | 0.255 |   0.315 |            0.645 |              0.001 |            0.433 |              0.001 |            0.985 |              0.1   |        0.009 |          0.015 |
| primary     | LocAgent             | parse  | Mono-fix |      510 | 0.687 | 0.457 |   0.557 |            0.687 |            nan     |            0.457 |            nan     |            1     |              0.998 |        0.008 |          0.011 |
| primary     | LocAgent             | parse  | Poly-fix |      271 | 0.635 | 0.254 |   0.315 |            0.645 |              0     |            0.434 |              0     |            0.985 |              0.1   |        0.01  |          0.016 |
| primary     | LocAgentRep          | all    | Mono-fix |       45 | 0.758 | 0.502 |   0.563 |            0.758 |            nan     |            0.502 |            nan     |            1     |              1     |        0.004 |          0.005 |
| primary     | LocAgentRep          | all    | Poly-fix |       29 | 0.697 | 0.239 |   0.284 |            0.722 |              0.001 |            0.421 |              0.001 |            0.966 |              0.034 |        0.008 |          0.013 |
| primary     | LocAgentRep          | parse  | Mono-fix |       45 | 0.758 | 0.503 |   0.563 |            0.758 |            nan     |            0.503 |            nan     |            1     |              1     |        0.005 |          0.007 |
| primary     | LocAgentRep          | parse  | Poly-fix |       29 | 0.697 | 0.238 |   0.284 |            0.722 |              0     |            0.421 |              0     |            0.966 |              0.034 |        0.008 |          0.012 |
| primary     | SweRank              | all    | Mono-fix |      510 | 0.714 | 0.478 |   0.568 |            0.714 |            nan     |            0.478 |            nan     |            1     |              0.998 |        0.005 |          0.008 |
| primary     | SweRank              | all    | Poly-fix |      271 | 0.686 | 0.277 |   0.346 |            0.696 |              0.001 |            0.468 |              0.001 |            0.985 |              0.1   |        0.009 |          0.015 |
| primary     | SweRank              | parse  | Mono-fix |      510 | 0.714 | 0.478 |   0.568 |            0.714 |            nan     |            0.478 |            nan     |            1     |              0.998 |        0.008 |          0.011 |
| primary     | SweRank              | parse  | Poly-fix |      271 | 0.686 | 0.277 |   0.346 |            0.696 |              0     |            0.469 |              0     |            0.985 |              0.1   |        0.01  |          0.016 |
| primary     | SweRankAll           | all    | Mono-fix |      510 | 0.707 | 0.583 |   0.725 |            0.707 |            nan     |            0.583 |            nan     |            1     |              0.998 |        0.005 |          0.008 |
| primary     | SweRankAll           | all    | Poly-fix |      271 | 0.735 | 0.475 |   0.626 |            0.686 |              0.2   |            0.543 |              0.18  |            0.985 |              0.1   |        0.009 |          0.015 |
| primary     | SweRankAll           | parse  | Mono-fix |      510 | 0.716 | 0.594 |   0.739 |            0.716 |            nan     |            0.594 |            nan     |            1     |              0.998 |        0.008 |          0.011 |
| primary     | SweRankAll           | parse  | Poly-fix |      271 | 0.71  | 0.351 |   0.446 |            0.721 |              0     |            0.581 |              0     |            0.985 |              0.1   |        0.01  |          0.016 |
| primary     | SweRankEmbed         | all    | Mono-fix |      510 | 0.63  | 0.415 |   0.542 |            0.63  |            nan     |            0.415 |            nan     |            1     |              0.998 |        0.005 |          0.008 |
| primary     | SweRankEmbed         | all    | Poly-fix |      271 | 0.57  | 0.227 |   0.32  |            0.579 |              0.001 |            0.389 |              0.001 |            0.985 |              0.1   |        0.009 |          0.015 |
| primary     | SweRankEmbed         | parse  | Mono-fix |      510 | 0.63  | 0.415 |   0.542 |            0.63  |            nan     |            0.415 |            nan     |            1     |              0.998 |        0.008 |          0.011 |
| primary     | SweRankEmbed         | parse  | Poly-fix |      271 | 0.57  | 0.226 |   0.32  |            0.579 |              0     |            0.389 |              0     |            0.985 |              0.1   |        0.01  |          0.016 |
| primary     | SweRankEmbedAll      | all    | Mono-fix |      510 | 0.606 | 0.497 |   0.682 |            0.606 |            nan     |            0.497 |            nan     |            1     |              0.998 |        0.005 |          0.008 |
| primary     | SweRankEmbedAll      | all    | Poly-fix |      271 | 0.593 | 0.395 |   0.569 |            0.52  |              0.214 |            0.421 |              0.198 |            0.985 |              0.1   |        0.009 |          0.015 |
| primary     | SweRankEmbedAll      | parse  | Mono-fix |      510 | 0.629 | 0.522 |   0.704 |            0.629 |            nan     |            0.522 |            nan     |            1     |              0.998 |        0.008 |          0.011 |
| primary     | SweRankEmbedAll      | parse  | Poly-fix |      271 | 0.573 | 0.287 |   0.43  |            0.581 |              0     |            0.479 |              0     |            0.985 |              0.1   |        0.01  |          0.016 |
| primary     | SweRankEmbedAllCap10 | all    | Mono-fix |      510 | 0.605 | 0.482 |   0.668 |            0.605 |            nan     |            0.482 |            nan     |            1     |              0.998 |        0.005 |          0.008 |
| primary     | SweRankEmbedAllCap10 | all    | Poly-fix |      271 | 0.58  | 0.372 |   0.543 |            0.518 |              0.189 |            0.413 |              0.172 |            0.985 |              0.1   |        0.009 |          0.015 |
| primary     | SweRankEmbedAllCap10 | parse  | Mono-fix |      510 | 0.628 | 0.507 |   0.692 |            0.628 |            nan     |            0.507 |            nan     |            1     |              0.998 |        0.008 |          0.011 |
| primary     | SweRankEmbedAllCap10 | parse  | Poly-fix |      271 | 0.572 | 0.281 |   0.415 |            0.581 |              0     |            0.472 |              0     |            0.985 |              0.1   |        0.01  |          0.016 |
| primary     | SweRankEmbedNonPy    | all    | Mono-fix |      510 | 0.597 | 0.386 |   0.522 |            0.597 |            nan     |            0.386 |            nan     |            1     |              0.998 |        0.005 |          0.008 |
| primary     | SweRankEmbedNonPy    | all    | Poly-fix |      271 | 0.599 | 0.335 |   0.493 |            0.5   |              0.253 |            0.329 |              0.235 |            0.985 |              0.1   |        0.009 |          0.015 |
| primary     | SweRankEmbedNonPy    | parse  | Mono-fix |      510 | 0.629 | 0.415 |   0.542 |            0.629 |            nan     |            0.415 |            nan     |            1     |              0.998 |        0.008 |          0.011 |
| primary     | SweRankEmbedNonPy    | parse  | Poly-fix |      271 | 0.57  | 0.226 |   0.32  |            0.578 |              0     |            0.389 |              0     |            0.985 |              0.1   |        0.01  |          0.016 |
| primary     | SweRankEmbedPyTest   | all    | Mono-fix |      510 | 0.634 | 0.526 |   0.694 |            0.634 |            nan     |            0.526 |            nan     |            1     |              0.998 |        0.005 |          0.008 |
| primary     | SweRankEmbedPyTest   | all    | Poly-fix |      271 | 0.584 | 0.289 |   0.425 |            0.593 |              0.001 |            0.485 |              0.001 |            0.985 |              0.1   |        0.009 |          0.015 |
| primary     | SweRankEmbedPyTest   | parse  | Mono-fix |      510 | 0.634 | 0.526 |   0.694 |            0.634 |            nan     |            0.526 |            nan     |            1     |              0.998 |        0.008 |          0.011 |
| primary     | SweRankEmbedPyTest   | parse  | Poly-fix |      271 | 0.584 | 0.288 |   0.425 |            0.593 |              0     |            0.485 |              0     |            0.985 |              0.1   |        0.01  |          0.016 |

## Sensitivity — interaction estimate under each condition

|                                                                        |   P_behavioural |   P_test_only |   S1_no_tests |   S2_headline |   S2_strict |   S3_universe_T |   S4_untangled |   S5_fold1 |   S5_fold2 |   S6_kept+removed |   S6_removed |   primary |
|:-----------------------------------------------------------------------|----------------:|--------------:|--------------:|--------------:|------------:|----------------:|---------------:|-----------:|-----------:|------------------:|-------------:|----------:|
| ('BLAZE_ALL vs BLAZE (ablation)', 'ap')                                |         -0.044  |        0.0179 |       -0.0063 |        0.0048 |     -0.0176 |         -0.0183 |         0.0009 |     0.0009 |   nan      |            0.0092 |       0.033  |    0.0009 |
| ('BM25 vs CoChangeFLIM', 'ap')                                         |          0.0357 |       -0.0352 |        0.0162 |       -0.0139 |      0.0151 |         -0.0212 |        -0.0034 |    -0.0165 |     0.0166 |           -0.007  |      -0.0402 |   -0.0032 |
| ('BM25 vs CoChangeLocAgent', 'ap10')                                   |          0.1667 |       -0.0007 |        0.006  |        0.0735 |      0.0124 |          0.0669 |         0.0827 |     0.1264 |     0.0182 |            0.0784 |       0.1253 |    0.0827 |
| ('BM25 vs CoChangeSweRank', 'ap')                                      |          0.1457 |        0.0079 |        0.0148 |        0.0422 |     -0.0016 |          0.0529 |         0.055  |     0.0722 |     0.0458 |            0.0521 |       0.0813 |    0.055  |
| ('BM25 vs FLIM-fallback', 'ap')                                        |          0.1105 |        0.0612 |        0.0432 |        0.0763 |      0.0773 |          0.079  |         0.0789 |     0.0751 |     0.0834 |            0.0696 |       0.0292 |    0.0788 |
| ('BM25 vs FLIM-strict', 'ap')                                          |          0.138  |        0.0908 |        0.0468 |        0.1105 |      0.0956 |          0.1056 |         0.1078 |     0.1083 |     0.106  |            0.1016 |       0.0795 |    0.1075 |
| ('BM25 vs HybridFLIM', 'ap')                                           |          0.0662 |       -0.002  |        0.0362 |        0.0242 |      0.0517 |         -0.0217 |         0.0296 |     0.0172 |     0.0383 |            0.018  |      -0.0215 |    0.0296 |
| ('BM25 vs HybridLocAgent', 'ap10')                                     |          0.1528 |        0.0208 |        0.0363 |        0.0808 |      0.0327 |          0.0421 |         0.0748 |     0.1206 |     0.0277 |            0.0808 |       0.14   |    0.0748 |
| ('BM25 vs HybridSweRank', 'ap')                                        |          0.1498 |        0.0195 |        0.0429 |        0.0854 |      0.0512 |          0.0459 |         0.0848 |     0.0916 |     0.0746 |            0.0766 |       0.0735 |    0.0848 |
| ('BM25 vs LocAgent', 'ap10')                                           |          0.1824 |        0.0922 |        0.0621 |        0.1482 |      0.0283 |          0.1403 |         0.137  |     0.2105 |     0.0635 |            0.1348 |       0.1536 |    0.137  |
| ('BM25 vs SweRank', 'ap')                                              |          0.1772 |        0.0966 |        0.0607 |        0.1508 |      0.0368 |          0.1474 |         0.1431 |     0.1722 |     0.1131 |            0.1271 |       0.0947 |    0.1431 |
| ('BM25 vs SweRank (top-10)', 'ap10')                                   |          0.1782 |        0.0911 |        0.054  |        0.1469 |      0.0329 |          0.1435 |         0.1404 |     0.1703 |     0.1094 |            0.1249 |       0.0968 |    0.1404 |
| ('BM25 vs SweRankAll', 'ap')                                           |          0.0371 |       -0.0152 |       -0.0216 |        0.008  |      0      |          0.0208 |         0.0149 |     0.0313 |    -0.0149 |            0.0145 |       0.008  |    0.0149 |
| ('BM25 vs SweRankEmbedAll', 'ap')                                      |          0.088  |       -0.0062 |        0.0469 |        0.0226 |      0.057  |          0.0384 |         0.0328 |     0.0479 |     0.0248 |            0.0248 |      -0.0166 |    0.0328 |
| ('BM25 vs SweRankEmbedNonPy', 'ap')                                    |          0.0222 |       -0.0331 |        0.0348 |       -0.0125 |     -0.0354 |          0.0009 |        -0.0061 |     0.0084 |    -0.0234 |           -0.0367 |      -0.156  |   -0.0061 |
| ('BM25-parse vs FLIM-strict (control)', 'ap')                          |          0.0181 |       -0.0039 |        0.0094 |       -0.002  |      0.0331 |          0.0042 |         0.0046 |    -0.0243 |     0.0277 |           -0.0012 |      -0.0297 |    0.0043 |
| ('CoChangeFLIM vs FLIM-strict', 'ap')                                  |          0.1077 |        0.1081 |        0.0352 |        0.1191 |      0.0828 |          0.1279 |         0.1087 |     0.1242 |     0.0917 |            0.1106 |       0.1176 |    0.1081 |
| ('CoChangeLocAgent vs LocAgent', 'ap10')                               |          0.016  |        0.0962 |        0.0471 |        0.0853 |      0.0242 |          0.0716 |         0.0712 |     0.0919 |     0.0446 |            0.0646 |       0.0311 |    0.0712 |
| ('CoChangeSweRank vs SweRank', 'ap')                                   |          0.0319 |        0.1167 |        0.0526 |        0.112  |      0.0432 |          0.1028 |         0.0911 |     0.106  |     0.0716 |            0.0784 |       0.0184 |    0.0911 |
| ('HybridFLIM vs FLIM-strict', 'ap')                                    |          0.0739 |        0.0888 |        0.0144 |        0.0889 |      0.0446 |          0.1272 |         0.0822 |     0.0947 |     0.0669 |            0.0855 |       0.0992 |    0.0818 |
| ('HybridLocAgent vs LocAgent', 'ap10')                                 |          0.0298 |        0.0721 |        0.0288 |        0.0669 |     -0.0043 |          0.0993 |         0.0615 |     0.0872 |     0.0328 |            0.0534 |       0.0206 |    0.0615 |
| ('HybridSweRank vs SweRank', 'ap')                                     |          0.0273 |        0.0709 |        0.0108 |        0.0657 |     -0.0175 |          0.1053 |         0.0588 |     0.0773 |     0.0352 |            0.0486 |       0.0101 |    0.0588 |
| ('SweRankAll vs SweRank (corpus extension, reranked)', 'ap')           |          0.1397 |        0.1085 |        0.0862 |        0.1405 |      0.0294 |          0.1259 |         0.126  |     0.1319 |     0.1169 |            0.112  |       0.0694 |    0.126  |
| ('SweRankEmbed vs SweRank (reranker effect)', 'ap')                    |          0.0246 |       -0.014  |       -0.0105 |        0.0035 |     -0.0332 |          0.0016 |         0.0012 |    -0.0024 |    -0.0025 |            0.0059 |       0.0238 |    0.0012 |
| ('SweRankEmbed vs SweRankEmbedAll (corpus extension)', 'ap')           |          0.0652 |        0.1238 |        0.0314 |        0.1225 |      0.016  |          0.1078 |         0.1081 |     0.1212 |     0.0902 |            0.0953 |       0.0809 |    0.1081 |
| ('SweRankEmbedAllCap10 vs SweRankEmbedAll (10-chunk cap)', 'ap')       |         -0.0259 |        0.0018 |       -0.017  |       -0.0117 |      0.0045 |         -0.0088 |        -0.0089 |    -0.0109 |    -0.0049 |           -0.009  |      -0.0074 |   -0.0089 |
| ('SweRankEmbedNonPy vs SweRankEmbed (non-Python files added)', 'ap')   |          0.1305 |        0.1515 |        0.0472 |        0.1624 |      0.1007 |          0.1503 |         0.15   |     0.1549 |     0.1388 |            0.1615 |       0.211  |    0.15   |
| ('SweRankEmbedPyTest vs SweRankEmbed (Python test files added)', 'ap') |         -0.0764 |       -0.0211 |       -0.0011 |       -0.0334 |     -0.0829 |         -0.0397 |        -0.0396 |    -0.0241 |    -0.056  |           -0.0594 |      -0.1149 |   -0.0396 |

