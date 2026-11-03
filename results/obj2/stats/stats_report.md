# Objective 2 statistics (full)

Input: `/home/cs21d002_eashaan/PhD/Objective2/results/obj2/eval/per_bug.parquet`; bugs (seed-averaged rows): 6768

## RQ3 — class effect (Poly-fix minus Mono-fix), pooled model, primary condition

Primary outcome: AP (MAP); AP@10 for LocAgent.

| condition   | tech      | view   | outcome                 | model              |   n_bugs |   class_effect_poly |   ci_lo |   ci_hi |      p |
|:------------|:----------|:-------|:------------------------|:-------------------|---------:|--------------------:|--------:|--------:|-------:|
| primary     | BLAZE     | all    | ap                      | ols_project_fe_hc3 |      211 |              0.0362 | -0.0492 |  0.1217 | 0.406  |
| primary     | BLAZE     | all    | cfr10                   | ols_project_fe_hc3 |      211 |             -0.0188 | -0.1383 |  0.1008 | 0.7585 |
| primary     | BLAZE     | all    | rr                      | ols_project_fe_hc3 |      211 |              0.1128 | -0.0166 |  0.2423 | 0.0876 |
| primary     | BLAZE     | all    | top10                   | ols_project_fe_hc3 |      211 |              0.0885 | -0.0806 |  0.2577 | 0.305  |
| primary     | BLAZE     | all    | top10 (logit, log-odds) | logit_project_fe   |      211 |              0.4318 | -0.3337 |  1.1972 | 0.2689 |
| primary     | BLAZE     | parse  | ap                      | ols_project_fe_hc3 |      211 |             -0.0293 | -0.108  |  0.0494 | 0.4659 |
| primary     | BLAZE     | parse  | cfr10                   | ols_project_fe_hc3 |      211 |             -0.0295 | -0.1424 |  0.0834 | 0.6082 |
| primary     | BLAZE     | parse  | rr                      | ols_project_fe_hc3 |      211 |              0.0869 | -0.046  |  0.2199 | 0.1999 |
| primary     | BLAZE     | parse  | top10                   | ols_project_fe_hc3 |      211 |              0.094  | -0.0711 |  0.2591 | 0.2645 |
| primary     | BLAZE     | parse  | top10 (logit, log-odds) | logit_project_fe   |      211 |              0.468  | -0.3048 |  1.2408 | 0.2352 |
| primary     | BLAZE_ALL | all    | ap                      | ols_project_fe_hc3 |      124 |             -0.0787 | -0.1706 |  0.0132 | 0.0932 |
| primary     | BLAZE_ALL | all    | cfr10                   | ols_project_fe_hc3 |      124 |             -0.1256 | -0.2518 |  0.0006 | 0.0511 |
| primary     | BLAZE_ALL | all    | rr                      | ols_project_fe_hc3 |      124 |             -0.039  | -0.2108 |  0.1329 | 0.6569 |
| primary     | BLAZE_ALL | all    | top10                   | ols_project_fe_hc3 |      124 |             -0.0758 | -0.3226 |  0.171  | 0.5473 |
| primary     | BLAZE_ALL | all    | top10 (logit, log-odds) | logit_project_fe   |      124 |             -0.3858 | -1.534  |  0.7624 | 0.5102 |
| primary     | BLAZE_ALL | parse  | ap                      | ols_project_fe_hc3 |      124 |             -0.1112 | -0.2033 | -0.0191 | 0.018  |
| primary     | BLAZE_ALL | parse  | cfr10                   | ols_project_fe_hc3 |      124 |             -0.1797 | -0.295  | -0.0644 | 0.0022 |
| primary     | BLAZE_ALL | parse  | rr                      | ols_project_fe_hc3 |      124 |             -0.1227 | -0.2862 |  0.0408 | 0.1412 |
| primary     | BLAZE_ALL | parse  | top10                   | ols_project_fe_hc3 |      124 |             -0.2185 | -0.4421 |  0.0051 | 0.0555 |
| primary     | BLAZE_ALL | parse  | top10 (logit, log-odds) | logit_project_fe   |      124 |             -1.1783 | -2.464  |  0.1074 | 0.0725 |
| primary     | BM25      | all    | ap                      | ols_project_fe_hc3 |      211 |              0.0651 | -0.0315 |  0.1618 | 0.1864 |
| primary     | BM25      | all    | cfr10                   | ols_project_fe_hc3 |      211 |              0.1679 |  0.0398 |  0.2959 | 0.0102 |
| primary     | BM25      | all    | rr                      | ols_project_fe_hc3 |      211 |              0.0444 | -0.0889 |  0.1778 | 0.5138 |
| primary     | BM25      | all    | top10                   | ols_project_fe_hc3 |      211 |              0.1987 |  0.0292 |  0.3681 | 0.0216 |
| primary     | BM25      | all    | top10 (logit, log-odds) | logit_project_fe   |      211 |              1.0165 |  0.2168 |  1.8162 | 0.0127 |
| primary     | BM25      | parse  | ap                      | ols_project_fe_hc3 |      211 |             -0.0252 | -0.11   |  0.0596 | 0.5605 |
| primary     | BM25      | parse  | cfr10                   | ols_project_fe_hc3 |      211 |              0.0273 | -0.0922 |  0.1468 | 0.6543 |
| primary     | BM25      | parse  | rr                      | ols_project_fe_hc3 |      211 |              0.0325 | -0.1033 |  0.1684 | 0.6386 |
| primary     | BM25      | parse  | top10                   | ols_project_fe_hc3 |      211 |              0.1321 | -0.0388 |  0.3029 | 0.1298 |
| primary     | BM25      | parse  | top10 (logit, log-odds) | logit_project_fe   |      211 |              0.7072 | -0.088  |  1.5025 | 0.0813 |
| primary     | FLIM      | all    | ap                      | ols_project_fe_hc3 |      211 |              0.0504 | -0.0419 |  0.1427 | 0.2847 |
| primary     | FLIM      | all    | cfr10                   | ols_project_fe_hc3 |      211 |              0.0182 | -0.1085 |  0.1449 | 0.7784 |
| primary     | FLIM      | all    | rr                      | ols_project_fe_hc3 |      211 |              0.1519 |  0.0056 |  0.2983 | 0.0419 |
| primary     | FLIM      | all    | top10                   | ols_project_fe_hc3 |      211 |              0.0921 | -0.0741 |  0.2582 | 0.2773 |
| primary     | FLIM      | all    | top10 (logit, log-odds) | logit_project_fe   |      211 |              0.5553 | -0.2732 |  1.3838 | 0.1889 |
| primary     | FLIM      | parse  | ap                      | ols_project_fe_hc3 |      211 |              0.013  | -0.0756 |  0.1015 | 0.7744 |
| primary     | FLIM      | parse  | cfr10                   | ols_project_fe_hc3 |      211 |             -0.0412 | -0.1637 |  0.0812 | 0.5094 |
| primary     | FLIM      | parse  | rr                      | ols_project_fe_hc3 |      211 |              0.1536 |  0.0076 |  0.2996 | 0.0392 |
| primary     | FLIM      | parse  | top10                   | ols_project_fe_hc3 |      211 |              0.0928 | -0.0733 |  0.2589 | 0.2734 |
| primary     | FLIM      | parse  | top10 (logit, log-odds) | logit_project_fe   |      211 |              0.5584 | -0.2705 |  1.3873 | 0.1867 |
| primary     | LocAgent  | all    | ap10                    | ols_project_fe_hc3 |       87 |             -0.1288 | -0.2565 | -0.0011 | 0.048  |
| primary     | LocAgent  | all    | cfr10                   | ols_project_fe_hc3 |       87 |             -0.202  | -0.3488 | -0.0553 | 0.007  |
| primary     | LocAgent  | all    | top10                   | ols_project_fe_hc3 |       87 |              0.0438 | -0.2245 |  0.3121 | 0.7489 |
| primary     | LocAgent  | all    | rr10                    | ols_project_fe_hc3 |       87 |              0.0603 | -0.1679 |  0.2885 | 0.6047 |
| primary     | LocAgent  | all    | top10 (logit, log-odds) | logit_project_fe   |       87 |              0.2247 | -0.8938 |  1.3432 | 0.6938 |
| primary     | LocAgent  | parse  | ap10                    | ols_project_fe_hc3 |       87 |             -0.1284 | -0.256  | -0.0009 | 0.0485 |
| primary     | LocAgent  | parse  | cfr10                   | ols_project_fe_hc3 |       87 |             -0.2014 | -0.3481 | -0.0547 | 0.0071 |
| primary     | LocAgent  | parse  | top10                   | ols_project_fe_hc3 |       87 |              0.0449 | -0.2232 |  0.313  | 0.7425 |
| primary     | LocAgent  | parse  | rr10                    | ols_project_fe_hc3 |       87 |              0.0606 | -0.1675 |  0.2886 | 0.6027 |
| primary     | LocAgent  | parse  | top10 (logit, log-odds) | logit_project_fe   |       87 |              0.2272 | -0.8914 |  1.3458 | 0.6906 |

## RQ4 — inversion test (d = A - B; interaction = Poly-fix minus Mono-fix difference)

| condition   | pair                                | outcome   | model              |   n_bugs |   interaction_poly |   ci_lo |   ci_hi |      p |   mean_diff_mono |   mean_diff_poly | inversion_pattern   |
|:------------|:------------------------------------|:----------|:-------------------|---------:|-------------------:|--------:|--------:|-------:|-----------------:|-----------------:|:--------------------|
| primary     | BM25 vs FLIM-strict                 | ap        | ols_project_fe_hc3 |      211 |             0.0529 | -0.0349 |  0.1407 | 0.2376 |          -0.0269 |           0.0237 | True                |
| primary     | BM25 vs FLIM-strict                 | cfr10     | ols_project_fe_hc3 |      211 |             0.2093 |  0.0799 |  0.3388 | 0.0015 |          -0.0773 |           0.0833 | True                |
| primary     | BM25 vs FLIM-strict                 | rr        | ols_project_fe_hc3 |      211 |            -0.1078 | -0.2381 |  0.0226 | 0.1052 |          -0.0275 |          -0.1541 | False               |
| primary     | BM25 vs FLIM-strict                 | top10     | ols_project_fe_hc3 |      211 |             0.1066 | -0.0689 |  0.2821 | 0.234  |          -0.0889 |          -0.0263 | False               |
| primary     | BM25 vs FLIM-fallback               | ap        | ols_project_fe_hc3 |      211 |             0.0148 | -0.0701 |  0.0996 | 0.7333 |          -0.0265 |          -0.0179 | False               |
| primary     | BM25 vs FLIM-fallback               | cfr10     | ols_project_fe_hc3 |      211 |             0.1497 |  0.0256 |  0.2738 | 0.018  |          -0.0773 |           0.0292 | True                |
| primary     | BM25 vs FLIM-fallback               | rr        | ols_project_fe_hc3 |      211 |            -0.1075 | -0.238  |  0.023  | 0.1064 |          -0.0274 |          -0.1536 | False               |
| primary     | BM25 vs FLIM-fallback               | top10     | ols_project_fe_hc3 |      211 |             0.1066 | -0.0689 |  0.2821 | 0.234  |          -0.0889 |          -0.0263 | False               |
| primary     | BM25-parse vs FLIM-strict (control) | ap        | ols_project_fe_hc3 |      211 |            -0.0381 | -0.1171 |  0.0408 | 0.3437 |          -0.0223 |          -0.0645 | False               |
| primary     | BM25-parse vs FLIM-strict (control) | cfr10     | ols_project_fe_hc3 |      211 |             0.0685 | -0.0481 |  0.1851 | 0.2493 |          -0.0718 |          -0.0338 | False               |
| primary     | BM25-parse vs FLIM-strict (control) | rr        | ols_project_fe_hc3 |      211 |            -0.1211 | -0.2414 | -0.0008 | 0.0486 |          -0.0221 |          -0.15   | False               |
| primary     | BM25-parse vs FLIM-strict (control) | top10     | ols_project_fe_hc3 |      211 |             0.0393 | -0.1258 |  0.2043 | 0.6411 |          -0.0815 |          -0.0395 | False               |
| primary     | BM25 vs LocAgent                    | ap10      | ols_project_fe_hc3 |       87 |             0.2915 |  0.1076 |  0.4755 | 0.0019 |          -0.0447 |           0.1992 | True                |
| primary     | BM25 vs LocAgent                    | cfr10     | ols_project_fe_hc3 |       87 |             0.467  |  0.2394 |  0.6947 | 0.0001 |          -0.0573 |           0.3323 | True                |
| primary     | BM25 vs LocAgent                    | top10     | ols_project_fe_hc3 |       87 |             0.1882 | -0.0816 |  0.458  | 0.1716 |          -0.0625 |           0.1273 | True                |
| primary     | BM25 vs LocAgent                    | rr10      | ols_project_fe_hc3 |       87 |             0.1138 | -0.1388 |  0.3664 | 0.3774 |          -0.0554 |           0.0213 | True                |
| primary     | BLAZE_ALL vs BLAZE (ablation)       | ap        | ols_project_fe_hc3 |      124 |             0.0018 | -0.0833 |  0.0868 | 0.9677 |          -0.0293 |           0.0075 | True                |
| primary     | BLAZE_ALL vs BLAZE (ablation)       | cfr10     | ols_project_fe_hc3 |      124 |             0.0168 | -0.1233 |  0.1569 | 0.8145 |          -0.0647 |           0.0176 | True                |
| primary     | BLAZE_ALL vs BLAZE (ablation)       | rr        | ols_project_fe_hc3 |      124 |            -0.002  | -0.1909 |  0.187  | 0.9838 |          -0.0242 |           0.0037 | True                |
| primary     | BLAZE_ALL vs BLAZE (ablation)       | top10     | ols_project_fe_hc3 |      124 |            -0.0419 | -0.3561 |  0.2722 | 0.7937 |          -0.0388 |           0      | True                |

## Decomposition (primary condition)

| condition   | tech      | view   | class    |   n_bugs |   MRR |   MAP |   CFR10 |   MRR_primary_gt |   MRR_secondary_gt |   MAP_primary_gt |   MAP_secondary_gt |   reach_at_parse |   all_gt_parseable |   random_MRR |   random_top10 |
|:------------|:----------|:-------|:---------|---------:|------:|------:|--------:|-----------------:|-------------------:|-----------------:|-------------------:|-----------------:|-------------------:|-------------:|---------------:|
| primary     | BLAZE     | all    | Mono-fix |      135 | 0.229 | 0.173 |   0.321 |            0.229 |            nan     |            0.173 |            nan     |                1 |              1     |        0.003 |          0.004 |
| primary     | BLAZE     | all    | Poly-fix |       76 | 0.432 | 0.253 |   0.363 |            0.417 |              0.093 |            0.298 |              0.089 |                1 |              0.132 |        0.01  |          0.015 |
| primary     | BLAZE     | parse  | Mono-fix |      135 | 0.244 | 0.184 |   0.321 |            0.244 |            nan     |            0.184 |            nan     |                1 |              1     |        0.004 |          0.005 |
| primary     | BLAZE     | parse  | Poly-fix |       76 | 0.43  | 0.199 |   0.345 |            0.43  |              0     |            0.31  |              0     |                1 |              0.132 |        0.01  |          0.016 |
| primary     | BLAZE_ALL | all    | Mono-fix |      103 | 0.178 | 0.12  |   0.195 |            0.178 |            nan     |            0.12  |            nan     |                1 |              1     |        0.001 |          0.001 |
| primary     | BLAZE_ALL | all    | Poly-fix |       21 | 0.228 | 0.079 |   0.121 |            0.152 |              0.102 |            0.067 |              0.099 |                1 |              0.143 |        0.002 |          0.002 |
| primary     | BLAZE_ALL | parse  | Mono-fix |      103 | 0.188 | 0.125 |   0.201 |            0.188 |            nan     |            0.125 |            nan     |                1 |              1     |        0.001 |          0.001 |
| primary     | BLAZE_ALL | parse  | Poly-fix |       21 | 0.157 | 0.054 |   0.08  |            0.157 |              0     |            0.072 |              0     |                1 |              0.143 |        0.001 |          0.002 |
| primary     | BM25      | all    | Mono-fix |      135 | 0.353 | 0.252 |   0.364 |            0.353 |            nan     |            0.252 |            nan     |                1 |              1     |        0.003 |          0.004 |
| primary     | BM25      | all    | Poly-fix |       76 | 0.481 | 0.326 |   0.484 |            0.42  |              0.21  |            0.306 |              0.193 |                1 |              0.132 |        0.01  |          0.015 |
| primary     | BM25      | parse  | Mono-fix |      135 | 0.359 | 0.256 |   0.369 |            0.359 |            nan     |            0.256 |            nan     |                1 |              1     |        0.004 |          0.005 |
| primary     | BM25      | parse  | Poly-fix |       76 | 0.486 | 0.238 |   0.366 |            0.486 |              0     |            0.358 |              0     |                1 |              0.132 |        0.01  |          0.016 |
| primary     | FLIM      | all    | Mono-fix |      135 | 0.381 | 0.278 |   0.441 |            0.381 |            nan     |            0.278 |            nan     |                1 |              1     |        0.003 |          0.004 |
| primary     | FLIM      | all    | Poly-fix |       76 | 0.635 | 0.344 |   0.454 |            0.635 |              0.047 |            0.46  |              0.048 |                1 |              0.132 |        0.01  |          0.015 |
| primary     | FLIM      | parse  | Mono-fix |      135 | 0.381 | 0.279 |   0.441 |            0.381 |            nan     |            0.279 |            nan     |                1 |              1     |        0.004 |          0.005 |
| primary     | FLIM      | parse  | Poly-fix |       76 | 0.635 | 0.302 |   0.4   |            0.635 |              0     |            0.462 |              0     |                1 |              0.132 |        0.01  |          0.016 |
| primary     | LocAgent  | all    | Mono-fix |       32 | 0.495 | 0.368 |   0.519 |            0.495 |            nan     |            0.368 |            nan     |                1 |              1     |        0.008 |          0.011 |
| primary     | LocAgent  | all    | Poly-fix |       55 | 0.538 | 0.174 |   0.223 |            0.538 |              0.001 |            0.255 |              0.001 |                1 |              0.127 |        0.013 |          0.021 |
| primary     | LocAgent  | parse  | Mono-fix |       32 | 0.495 | 0.369 |   0.519 |            0.495 |            nan     |            0.369 |            nan     |                1 |              1     |        0.011 |          0.017 |
| primary     | LocAgent  | parse  | Poly-fix |       55 | 0.538 | 0.173 |   0.223 |            0.538 |              0     |            0.256 |              0     |                1 |              0.127 |        0.013 |          0.021 |

## Sensitivity — interaction estimate under each condition

|                                               |   P_test_only |   S1_no_tests |   S2_headline |   S3_universe_T |   S4_untangled |   S5_fold1 |   S6_kept+removed |   primary |
|:----------------------------------------------|--------------:|--------------:|--------------:|----------------:|---------------:|-----------:|------------------:|----------:|
| ('BLAZE_ALL vs BLAZE (ablation)', 'ap')       |        0.0113 |        0.0208 |       -0.0123 |          0.0074 |         0.0018 |     0.0018 |            0.0185 |    0.0018 |
| ('BM25 vs FLIM-fallback', 'ap')               |        0.0135 |       -0.0659 |        0.0101 |          0.035  |         0.0148 |     0.0148 |            0.0333 |    0.0148 |
| ('BM25 vs FLIM-strict', 'ap')                 |        0.0527 |       -0.0618 |        0.0506 |          0.0732 |         0.0529 |     0.0529 |            0.0694 |    0.0529 |
| ('BM25 vs LocAgent', 'ap10')                  |        0.335  |       -0.079  |        0.2915 |          0.3274 |         0.2915 |     0.2915 |            0.3218 |    0.2915 |
| ('BM25-parse vs FLIM-strict (control)', 'ap') |       -0.0431 |       -0.0466 |       -0.041  |         -0.0388 |        -0.0381 |    -0.0381 |           -0.0153 |   -0.0381 |

