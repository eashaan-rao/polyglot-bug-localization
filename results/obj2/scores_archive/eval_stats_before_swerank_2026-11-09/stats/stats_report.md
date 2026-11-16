# Objective 2 statistics (full)

Input: `/home/cs21d002_eashaan/PhD/Objective2/results/obj2/eval/per_bug.parquet`; bugs (seed-averaged rows): 45282

## RQ3 — class effect (Poly-fix minus Mono-fix), pooled model, primary condition

Primary outcome: AP (MAP); AP@10 for LocAgent.

| condition   | tech        | view   | outcome                 | model            |   n_bugs |   class_effect_poly |   ci_lo |   ci_hi |      p |
|:------------|:------------|:-------|:------------------------|:-----------------|---------:|--------------------:|--------:|--------:|-------:|
| primary     | BLAZE       | all    | ap                      | mixedlm_powell   |     1399 |             -0.0213 | -0.0593 |  0.0167 | 0.2711 |
| primary     | BLAZE       | all    | cfr10                   | mixedlm_powell   |     1399 |             -0.0103 | -0.063  |  0.0425 | 0.7031 |
| primary     | BLAZE       | all    | rr                      | mixedlm_powell   |     1399 |              0.0116 | -0.0382 |  0.0614 | 0.6473 |
| primary     | BLAZE       | all    | top10                   | mixedlm_powell   |     1399 |              0.0292 | -0.0335 |  0.0918 | 0.3617 |
| primary     | BLAZE       | all    | top10 (logit, log-odds) | logit_project_fe |     1399 |              0.1356 | -0.145  |  0.4161 | 0.3437 |
| primary     | BLAZE       | parse  | ap                      | mixedlm_powell   |     1399 |             -0.1029 | -0.1404 | -0.0654 | 0      |
| primary     | BLAZE       | parse  | cfr10                   | mixedlm_powell   |     1399 |             -0.1161 | -0.1667 | -0.0656 | 0      |
| primary     | BLAZE       | parse  | rr                      | mixedlm_powell   |     1399 |             -0.0229 | -0.074  |  0.0281 | 0.3783 |
| primary     | BLAZE       | parse  | top10                   | mixedlm_powell   |     1399 |             -0.0262 | -0.089  |  0.0366 | 0.4144 |
| primary     | BLAZE       | parse  | top10 (logit, log-odds) | logit_project_fe |     1399 |             -0.1049 | -0.3857 |  0.1759 | 0.4642 |
| primary     | BLAZE_ALL   | all    | ap                      | mixedlm_powell   |      691 |             -0.0307 | -0.0852 |  0.0238 | 0.2692 |
| primary     | BLAZE_ALL   | all    | cfr10                   | mixedlm_powell   |      691 |             -0.0603 | -0.1349 |  0.0143 | 0.1133 |
| primary     | BLAZE_ALL   | all    | rr                      | mixedlm_powell   |      691 |              0.0051 | -0.0949 |  0.105  | 0.9209 |
| primary     | BLAZE_ALL   | all    | top10                   | mixedlm_powell   |      691 |             -0.0494 | -0.1399 |  0.0411 | 0.2843 |
| primary     | BLAZE_ALL   | all    | top10 (logit, log-odds) | logit_project_fe |      691 |             -0.216  | -0.6262 |  0.1943 | 0.3021 |
| primary     | BLAZE_ALL   | parse  | ap                      | mixedlm_powell   |      691 |             -0.1081 | -0.1619 | -0.0542 | 0.0001 |
| primary     | BLAZE_ALL   | parse  | cfr10                   | mixedlm_powell   |      691 |             -0.1608 | -0.2335 | -0.0882 | 0      |
| primary     | BLAZE_ALL   | parse  | rr                      | mixedlm_powell   |      691 |             -0.0423 | -0.1186 |  0.0341 | 0.2777 |
| primary     | BLAZE_ALL   | parse  | top10                   | mixedlm_powell   |      691 |             -0.1198 | -0.2123 | -0.0272 | 0.0112 |
| primary     | BLAZE_ALL   | parse  | top10 (logit, log-odds) | logit_project_fe |      691 |             -0.536  | -0.9521 | -0.1198 | 0.0116 |
| primary     | BM25        | all    | ap                      | mixedlm_powell   |     1399 |             -0.026  | -0.0681 |  0.0161 | 0.2254 |
| primary     | BM25        | all    | cfr10                   | mixedlm_powell   |     1399 |             -0.0201 | -0.0728 |  0.0326 | 0.4543 |
| primary     | BM25        | all    | rr                      | mixedlm_powell   |     1399 |              0.0088 | -0.0435 |  0.0612 | 0.7403 |
| primary     | BM25        | all    | top10                   | mixedlm_powell   |     1399 |              0.0395 | -0.0222 |  0.1011 | 0.21   |
| primary     | BM25        | all    | top10 (logit, log-odds) | logit_project_fe |     1399 |              0.1719 | -0.1204 |  0.4642 | 0.2491 |
| primary     | BM25        | parse  | ap                      | mixedlm_powell   |     1399 |             -0.1293 | -0.1713 | -0.0873 | 0      |
| primary     | BM25        | parse  | cfr10                   | mixedlm_lbfgs    |     1399 |             -0.1566 | -0.207  | -0.1063 | 0      |
| primary     | BM25        | parse  | rr                      | mixedlm_lbfgs    |     1399 |             -0.0496 | -0.1036 |  0.0045 | 0.0721 |
| primary     | BM25        | parse  | top10                   | mixedlm_powell   |     1399 |             -0.0514 | -0.1119 |  0.0091 | 0.0962 |
| primary     | BM25        | parse  | top10 (logit, log-odds) | logit_project_fe |     1399 |             -0.2689 | -0.5643 |  0.0264 | 0.0743 |
| primary     | FLIM        | all    | ap                      | mixedlm_powell   |     1399 |             -0.1033 | -0.1446 | -0.0619 | 0      |
| primary     | FLIM        | all    | cfr10                   | mixedlm_powell   |     1399 |             -0.1359 | -0.1861 | -0.0857 | 0      |
| primary     | FLIM        | all    | rr                      | mixedlm_powell   |     1399 |             -0.027  | -0.08   |  0.0261 | 0.3197 |
| primary     | FLIM        | all    | top10                   | mixedlm_powell   |     1399 |             -0.0529 | -0.1104 |  0.0046 | 0.0713 |
| primary     | FLIM        | all    | top10 (logit, log-odds) | logit_project_fe |     1399 |             -0.2837 | -0.5956 |  0.0281 | 0.0746 |
| primary     | FLIM        | parse  | ap                      | mixedlm_powell   |     1399 |             -0.1335 | -0.1743 | -0.0928 | 0      |
| primary     | FLIM        | parse  | cfr10                   | mixedlm_powell   |     1399 |             -0.1781 | -0.2268 | -0.1293 | 0      |
| primary     | FLIM        | parse  | rr                      | mixedlm_lbfgs    |     1399 |             -0.033  | -0.0861 |  0.02   | 0.222  |
| primary     | FLIM        | parse  | top10                   | mixedlm_lbfgs    |     1399 |             -0.0665 | -0.1234 | -0.0097 | 0.0218 |
| primary     | FLIM        | parse  | top10 (logit, log-odds) | logit_project_fe |     1399 |             -0.3753 | -0.6915 | -0.0591 | 0.02   |
| primary     | LocAgent    | all    | ap10                    | mixedlm_powell   |      781 |             -0.1629 | -0.2113 | -0.1145 | 0      |
| primary     | LocAgent    | all    | cfr10                   | mixedlm_powell   |      781 |             -0.1852 | -0.2356 | -0.1348 | 0      |
| primary     | LocAgent    | all    | top10                   | mixedlm_powell   |      781 |             -0.0569 | -0.1239 |  0.01   | 0.0956 |
| primary     | LocAgent    | all    | rr10                    | mixedlm_powell   |      781 |             -0.0532 | -0.1235 |  0.0171 | 0.1383 |
| primary     | LocAgent    | all    | top10 (logit, log-odds) | logit_project_fe |      781 |             -0.3985 | -0.848  |  0.051  | 0.0823 |
| primary     | LocAgent    | parse  | ap10                    | mixedlm_powell   |      781 |             -0.1628 | -0.211  | -0.1145 | 0      |
| primary     | LocAgent    | parse  | cfr10                   | mixedlm_powell   |      781 |             -0.1846 | -0.2349 | -0.1344 | 0      |
| primary     | LocAgent    | parse  | top10                   | mixedlm_powell   |      781 |             -0.0569 | -0.1239 |  0.0102 | 0.0965 |
| primary     | LocAgent    | parse  | rr10                    | mixedlm_powell   |      781 |             -0.0539 | -0.1242 |  0.0163 | 0.1326 |
| primary     | LocAgent    | parse  | top10 (logit, log-odds) | logit_project_fe |      781 |             -0.3928 | -0.842  |  0.0563 | 0.0865 |
| primary     | LocAgentRep | all    | ap                      | mixedlm_lbfgs    |       74 |             -0.2864 | -0.4435 | -0.1293 | 0.0004 |
| primary     | LocAgentRep | all    | cfr10                   | mixedlm_lbfgs    |       74 |             -0.324  | -0.4671 | -0.1809 | 0      |
| primary     | LocAgentRep | all    | rr                      | mixedlm_powell   |       74 |             -0.1319 | -0.3758 |  0.1121 | 0.2894 |
| primary     | LocAgentRep | all    | top10                   | mixedlm_powell   |       74 |             -0.1546 | -0.3868 |  0.0775 | 0.1918 |
| primary     | LocAgentRep | all    | top10 (logit, log-odds) | logit_project_fe |       74 |             -1.9143 | -3.9465 |  0.1179 | 0.0649 |
| primary     | LocAgentRep | parse  | ap                      | mixedlm_lbfgs    |       74 |             -0.2907 | -0.4481 | -0.1334 | 0.0003 |
| primary     | LocAgentRep | parse  | cfr10                   | mixedlm_lbfgs    |       74 |             -0.327  | -0.4708 | -0.1832 | 0      |
| primary     | LocAgentRep | parse  | rr                      | mixedlm_powell   |       74 |             -0.1478 | -0.3874 |  0.0919 | 0.2269 |
| primary     | LocAgentRep | parse  | top10                   | mixedlm_powell   |       74 |             -0.1723 | -0.399  |  0.0544 | 0.1362 |
| primary     | LocAgentRep | parse  | top10 (logit, log-odds) | logit_project_fe |       74 |             -1.895  | -3.921  |  0.131  | 0.0668 |

## RQ4 — inversion test (d = A - B; interaction = Poly-fix minus Mono-fix difference)

| condition   | pair                                | outcome   | model              |   n_bugs |   interaction_poly |   ci_lo |   ci_hi |      p |   mean_diff_mono |   mean_diff_poly | inversion_pattern   |
|:------------|:------------------------------------|:----------|:-------------------|---------:|-------------------:|--------:|--------:|-------:|-----------------:|-----------------:|:--------------------|
| primary     | BM25 vs FLIM-strict                 | ap        | mixedlm_lbfgs      |     1399 |             0.1075 |  0.0676 |  0.1473 | 0      |          -0.0586 |           0.0289 | True                |
| primary     | BM25 vs FLIM-strict                 | cfr10     | mixedlm_lbfgs      |     1399 |             0.1501 |  0.099  |  0.2012 | 0      |          -0.0841 |           0.0457 | True                |
| primary     | BM25 vs FLIM-strict                 | rr        | mixedlm_powell     |     1399 |             0.0402 | -0.0128 |  0.0932 | 0.1368 |          -0.0769 |          -0.0773 | False               |
| primary     | BM25 vs FLIM-strict                 | top10     | mixedlm_lbfgs      |     1399 |             0.0961 |  0.0305 |  0.1617 | 0.0041 |          -0.0992 |          -0.0423 | False               |
| primary     | BM25 vs FLIM-fallback               | ap        | mixedlm_powell     |     1399 |             0.0788 |  0.0396 |  0.118  | 0.0001 |          -0.054  |           0.0024 | True                |
| primary     | BM25 vs FLIM-fallback               | cfr10     | mixedlm_powell     |     1399 |             0.1109 |  0.0599 |  0.1618 | 0      |          -0.0739 |           0.018  | True                |
| primary     | BM25 vs FLIM-fallback               | rr        | mixedlm_powell     |     1399 |             0.038  | -0.015  |  0.091  | 0.1602 |          -0.0729 |          -0.0752 | False               |
| primary     | BM25 vs FLIM-fallback               | top10     | mixedlm_powell     |     1399 |             0.0879 |  0.0229 |  0.1529 | 0.0081 |          -0.0866 |          -0.0375 | False               |
| primary     | BM25-parse vs FLIM-strict (control) | ap        | mixedlm_lbfgs      |     1399 |             0.0043 | -0.0348 |  0.0434 | 0.8294 |          -0.0093 |          -0.0258 | False               |
| primary     | BM25-parse vs FLIM-strict (control) | cfr10     | mixedlm_powell     |     1399 |             0.0172 | -0.0319 |  0.0663 | 0.4916 |          -0.0408 |          -0.0349 | False               |
| primary     | BM25-parse vs FLIM-strict (control) | rr        | ols_project_fe_hc3 |     1399 |            -0.018  | -0.0734 |  0.0375 | 0.5258 |          -0.0171 |          -0.0674 | False               |
| primary     | BM25-parse vs FLIM-strict (control) | top10     | mixedlm_powell     |     1399 |             0.0088 | -0.054  |  0.0716 | 0.7838 |          -0.0483 |          -0.0614 | False               |
| primary     | BM25 vs LocAgent                    | ap10      | mixedlm_powell     |      781 |             0.137  |  0.0753 |  0.1988 | 0      |          -0.1141 |           0.0365 | True                |
| primary     | BM25 vs LocAgent                    | cfr10     | mixedlm_powell     |      781 |             0.1466 |  0.0738 |  0.2194 | 0.0001 |          -0.0073 |           0.1431 | True                |
| primary     | BM25 vs LocAgent                    | top10     | mixedlm_powell     |      781 |             0.0804 | -0.008  |  0.1687 | 0.0745 |          -0.1255 |          -0.0258 | False               |
| primary     | BM25 vs LocAgent                    | rr10      | mixedlm_powell     |      781 |             0.0967 |  0.0157 |  0.1777 | 0.0193 |          -0.246  |          -0.1442 | False               |
| primary     | BLAZE_ALL vs BLAZE (ablation)       | ap        | mixedlm_powell     |      691 |             0.0009 | -0.0459 |  0.0477 | 0.9711 |          -0.0104 |          -0.0061 | False               |
| primary     | BLAZE_ALL vs BLAZE (ablation)       | cfr10     | ols_project_fe_hc3 |      691 |             0.0033 | -0.0569 |  0.0635 | 0.9152 |          -0.0307 |          -0.0059 | False               |
| primary     | BLAZE_ALL vs BLAZE (ablation)       | rr        | mixedlm_powell     |      691 |            -0.0236 | -0.09   |  0.0427 | 0.4852 |          -0.0034 |          -0.0126 | False               |
| primary     | BLAZE_ALL vs BLAZE (ablation)       | top10     | ols_project_fe_hc3 |      691 |            -0.0934 | -0.1872 |  0.0004 | 0.051  |          -0.0028 |          -0.0563 | False               |

## Decomposition (primary condition)

| condition   | tech        | view   | class    |   n_bugs |   MRR |   MAP |   CFR10 |   MRR_primary_gt |   MRR_secondary_gt |   MAP_primary_gt |   MAP_secondary_gt |   reach_at_parse |   all_gt_parseable |   random_MRR |   random_top10 |
|:------------|:------------|:-------|:---------|---------:|------:|------:|--------:|-----------------:|-------------------:|-----------------:|-------------------:|-----------------:|-------------------:|-------------:|---------------:|
| primary     | BLAZE       | all    | Mono-fix |      981 | 0.329 | 0.255 |   0.412 |            0.329 |            nan     |            0.255 |            nan     |            1     |              0.999 |        0.004 |          0.006 |
| primary     | BLAZE       | all    | Poly-fix |      418 | 0.396 | 0.244 |   0.363 |            0.361 |              0.114 |            0.279 |              0.109 |            0.983 |              0.105 |        0.009 |          0.013 |
| primary     | BLAZE       | parse  | Mono-fix |      981 | 0.348 | 0.273 |   0.43  |            0.348 |            nan     |            0.273 |            nan     |            1     |              0.999 |        0.006 |          0.009 |
| primary     | BLAZE       | parse  | Poly-fix |      418 | 0.395 | 0.191 |   0.292 |            0.402 |              0     |            0.315 |              0     |            0.983 |              0.105 |        0.009 |          0.014 |
| primary     | BLAZE_ALL   | all    | Mono-fix |      478 | 0.314 | 0.244 |   0.396 |            0.314 |            nan     |            0.244 |            nan     |            1     |              0.998 |        0.004 |          0.005 |
| primary     | BLAZE_ALL   | all    | Poly-fix |      213 | 0.389 | 0.227 |   0.335 |            0.36  |              0.104 |            0.269 |              0.097 |            0.981 |              0.108 |        0.008 |          0.011 |
| primary     | BLAZE_ALL   | parse  | Mono-fix |      478 | 0.334 | 0.26  |   0.406 |            0.334 |            nan     |            0.26  |            nan     |            1     |              0.998 |        0.005 |          0.007 |
| primary     | BLAZE_ALL   | parse  | Poly-fix |      213 | 0.383 | 0.178 |   0.265 |            0.39  |              0     |            0.297 |              0     |            0.981 |              0.108 |        0.008 |          0.012 |
| primary     | BM25        | all    | Mono-fix |      981 | 0.389 | 0.311 |   0.471 |            0.389 |            nan     |            0.311 |            nan     |            1     |              0.999 |        0.004 |          0.006 |
| primary     | BM25        | all    | Poly-fix |      418 | 0.436 | 0.274 |   0.401 |            0.357 |              0.185 |            0.277 |              0.167 |            0.983 |              0.105 |        0.009 |          0.013 |
| primary     | BM25        | parse  | Mono-fix |      981 | 0.449 | 0.36  |   0.515 |            0.449 |            nan     |            0.36  |            nan     |            1     |              0.999 |        0.006 |          0.009 |
| primary     | BM25        | parse  | Poly-fix |      418 | 0.445 | 0.219 |   0.32  |            0.453 |              0     |            0.351 |              0     |            0.983 |              0.105 |        0.009 |          0.014 |
| primary     | FLIM        | all    | Mono-fix |      981 | 0.462 | 0.365 |   0.545 |            0.462 |            nan     |            0.365 |            nan     |            1     |              0.999 |        0.004 |          0.006 |
| primary     | FLIM        | all    | Poly-fix |      418 | 0.511 | 0.271 |   0.383 |            0.509 |              0.05  |            0.381 |              0.042 |            0.983 |              0.105 |        0.009 |          0.013 |
| primary     | FLIM        | parse  | Mono-fix |      981 | 0.466 | 0.37  |   0.555 |            0.466 |            nan     |            0.37  |            nan     |            1     |              0.999 |        0.006 |          0.009 |
| primary     | FLIM        | parse  | Poly-fix |      418 | 0.513 | 0.245 |   0.355 |            0.522 |              0     |            0.395 |              0     |            0.983 |              0.105 |        0.009 |          0.014 |
| primary     | LocAgent    | all    | Mono-fix |      510 | 0.687 | 0.457 |   0.557 |            0.687 |            nan     |            0.457 |            nan     |            1     |              0.998 |        0.005 |          0.008 |
| primary     | LocAgent    | all    | Poly-fix |      271 | 0.635 | 0.255 |   0.315 |            0.645 |              0.001 |            0.433 |              0.001 |            0.985 |              0.1   |        0.009 |          0.015 |
| primary     | LocAgent    | parse  | Mono-fix |      510 | 0.687 | 0.457 |   0.557 |            0.687 |            nan     |            0.457 |            nan     |            1     |              0.998 |        0.008 |          0.011 |
| primary     | LocAgent    | parse  | Poly-fix |      271 | 0.635 | 0.254 |   0.315 |            0.645 |              0     |            0.434 |              0     |            0.985 |              0.1   |        0.01  |          0.016 |
| primary     | LocAgentRep | all    | Mono-fix |       45 | 0.758 | 0.502 |   0.563 |            0.758 |            nan     |            0.502 |            nan     |            1     |              1     |        0.004 |          0.005 |
| primary     | LocAgentRep | all    | Poly-fix |       29 | 0.697 | 0.239 |   0.284 |            0.722 |              0.001 |            0.421 |              0.001 |            0.966 |              0.034 |        0.008 |          0.013 |
| primary     | LocAgentRep | parse  | Mono-fix |       45 | 0.758 | 0.503 |   0.563 |            0.758 |            nan     |            0.503 |            nan     |            1     |              1     |        0.005 |          0.007 |
| primary     | LocAgentRep | parse  | Poly-fix |       29 | 0.697 | 0.238 |   0.284 |            0.722 |              0     |            0.421 |              0     |            0.966 |              0.034 |        0.008 |          0.012 |

## Sensitivity — interaction estimate under each condition

|                                               |   P_behavioural |   P_test_only |   S1_no_tests |   S2_headline |   S2_strict |   S3_universe_T |   S4_untangled |   S5_fold1 |   S5_fold2 |   S6_kept+removed |   S6_removed |   primary |
|:----------------------------------------------|----------------:|--------------:|--------------:|--------------:|------------:|----------------:|---------------:|-----------:|-----------:|------------------:|-------------:|----------:|
| ('BLAZE_ALL vs BLAZE (ablation)', 'ap')       |         -0.044  |        0.0179 |       -0.0063 |        0.0048 |     -0.0176 |         -0.0183 |         0.0009 |     0.0009 |   nan      |            0.0092 |       0.033  |    0.0009 |
| ('BM25 vs FLIM-fallback', 'ap')               |          0.1105 |        0.0612 |        0.0432 |        0.0763 |      0.0773 |          0.079  |         0.0789 |     0.0751 |     0.0834 |            0.0696 |       0.0292 |    0.0788 |
| ('BM25 vs FLIM-strict', 'ap')                 |          0.138  |        0.0908 |        0.0468 |        0.1105 |      0.0956 |          0.1056 |         0.1078 |     0.1083 |     0.106  |            0.1016 |       0.0795 |    0.1075 |
| ('BM25 vs LocAgent', 'ap10')                  |          0.1824 |        0.0922 |        0.0621 |        0.1482 |      0.0283 |          0.1403 |         0.137  |     0.2105 |     0.0635 |            0.1348 |       0.1536 |    0.137  |
| ('BM25-parse vs FLIM-strict (control)', 'ap') |          0.0181 |       -0.0039 |        0.0094 |       -0.002  |      0.0331 |          0.0042 |         0.0046 |    -0.0243 |     0.0277 |           -0.0012 |      -0.0297 |    0.0043 |

