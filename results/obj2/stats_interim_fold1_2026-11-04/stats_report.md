# Objective 2 statistics (full)

Input: `/home/cs21d002_eashaan/PhD/Objective2/results/obj2/eval/per_bug.parquet`; bugs (seed-averaged rows): 23454

## RQ3 — class effect (Poly-fix minus Mono-fix), pooled model, primary condition

Primary outcome: AP (MAP); AP@10 for LocAgent.

| condition   | tech      | view   | outcome                 | model              |   n_bugs |   class_effect_poly |   ci_lo |   ci_hi |      p |
|:------------|:----------|:-------|:------------------------|:-------------------|---------:|--------------------:|--------:|--------:|-------:|
| primary     | BLAZE     | all    | ap                      | mixedlm_lbfgs      |      691 |             -0.0326 | -0.0881 |  0.0229 | 0.2497 |
| primary     | BLAZE     | all    | cfr10                   | mixedlm_powell     |      691 |             -0.0716 | -0.1481 |  0.005  | 0.0671 |
| primary     | BLAZE     | all    | rr                      | mixedlm_powell     |      691 |              0.032  | -0.0409 |  0.1049 | 0.39   |
| primary     | BLAZE     | all    | top10                   | mixedlm_powell     |      691 |              0.0241 | -0.0674 |  0.1155 | 0.6059 |
| primary     | BLAZE     | all    | top10 (logit, log-odds) | logit_project_fe   |      691 |              0.1382 | -0.2715 |  0.5479 | 0.5086 |
| primary     | BLAZE     | parse  | ap                      | mixedlm_powell     |      691 |             -0.1192 | -0.1743 | -0.0642 | 0      |
| primary     | BLAZE     | parse  | cfr10                   | mixedlm_powell     |      691 |             -0.1487 | -0.2239 | -0.0736 | 0.0001 |
| primary     | BLAZE     | parse  | rr                      | mixedlm_powell     |      691 |             -0.0114 | -0.0862 |  0.0635 | 0.7662 |
| primary     | BLAZE     | parse  | top10                   | mixedlm_lbfgs      |      691 |             -0.0268 | -0.1192 |  0.0655 | 0.569  |
| primary     | BLAZE     | parse  | top10 (logit, log-odds) | logit_project_fe   |      691 |             -0.1042 | -0.5146 |  0.3063 | 0.6188 |
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
| primary     | BM25      | all    | ap                      | mixedlm_powell     |     1399 |             -0.026  | -0.0681 |  0.0161 | 0.2254 |
| primary     | BM25      | all    | cfr10                   | mixedlm_powell     |     1399 |             -0.0201 | -0.0728 |  0.0326 | 0.4543 |
| primary     | BM25      | all    | rr                      | mixedlm_powell     |     1399 |              0.0088 | -0.0435 |  0.0612 | 0.7403 |
| primary     | BM25      | all    | top10                   | mixedlm_powell     |     1399 |              0.0395 | -0.0222 |  0.1011 | 0.21   |
| primary     | BM25      | all    | top10 (logit, log-odds) | logit_project_fe   |     1399 |              0.1719 | -0.1204 |  0.4642 | 0.2491 |
| primary     | BM25      | parse  | ap                      | mixedlm_powell     |     1399 |             -0.1293 | -0.1713 | -0.0873 | 0      |
| primary     | BM25      | parse  | cfr10                   | mixedlm_lbfgs      |     1399 |             -0.1566 | -0.207  | -0.1063 | 0      |
| primary     | BM25      | parse  | rr                      | mixedlm_lbfgs      |     1399 |             -0.0496 | -0.1036 |  0.0045 | 0.0721 |
| primary     | BM25      | parse  | top10                   | mixedlm_powell     |     1399 |             -0.0514 | -0.1119 |  0.0091 | 0.0962 |
| primary     | BM25      | parse  | top10 (logit, log-odds) | logit_project_fe   |     1399 |             -0.2689 | -0.5643 |  0.0264 | 0.0743 |
| primary     | FLIM      | all    | ap                      | mixedlm_powell     |      691 |             -0.0797 | -0.1425 | -0.0169 | 0.0129 |
| primary     | FLIM      | all    | cfr10                   | mixedlm_powell     |      691 |             -0.0881 | -0.1629 | -0.0133 | 0.021  |
| primary     | FLIM      | all    | rr                      | mixedlm_powell     |      691 |              0.0326 | -0.0465 |  0.1116 | 0.4194 |
| primary     | FLIM      | all    | top10                   | mixedlm_powell     |      691 |              0.0196 | -0.0637 |  0.1028 | 0.6448 |
| primary     | FLIM      | all    | top10 (logit, log-odds) | logit_project_fe   |      691 |              0.0737 | -0.3985 |  0.5459 | 0.7596 |
| primary     | FLIM      | parse  | ap                      | mixedlm_lbfgs      |      691 |             -0.1153 | -0.1763 | -0.0543 | 0.0002 |
| primary     | FLIM      | parse  | cfr10                   | mixedlm_powell     |      691 |             -0.1546 | -0.2269 | -0.0822 | 0      |
| primary     | FLIM      | parse  | rr                      | mixedlm_powell     |      691 |              0.0285 | -0.051  |  0.1079 | 0.4824 |
| primary     | FLIM      | parse  | top10                   | mixedlm_lbfgs      |      691 |             -0.0075 | -0.0908 |  0.0759 | 0.8607 |
| primary     | FLIM      | parse  | top10 (logit, log-odds) | logit_project_fe   |      691 |             -0.0732 | -0.5468 |  0.4003 | 0.7618 |
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
| primary     | BM25 vs FLIM-strict                 | ap        | mixedlm_powell     |      691 |             0.0969 |  0.0341 |  0.1597 | 0.0025 |          -0.0446 |           0.0297 | True                |
| primary     | BM25 vs FLIM-strict                 | cfr10     | mixedlm_powell     |      691 |             0.1473 |  0.0673 |  0.2274 | 0.0003 |          -0.0601 |           0.0531 | True                |
| primary     | BM25 vs FLIM-strict                 | rr        | mixedlm_powell     |      691 |            -0.0123 | -0.0926 |  0.0679 | 0.7631 |          -0.0499 |          -0.1091 | False               |
| primary     | BM25 vs FLIM-strict                 | top10     | mixedlm_lbfgs      |      691 |             0.0465 | -0.0503 |  0.1432 | 0.3466 |          -0.069  |          -0.0798 | False               |
| primary     | BM25 vs FLIM-fallback               | ap        | mixedlm_powell     |      691 |             0.0643 |  0.0018 |  0.1267 | 0.0437 |          -0.0418 |          -0.0022 | False               |
| primary     | BM25 vs FLIM-fallback               | cfr10     | mixedlm_powell     |      691 |             0.0831 |  0.0021 |  0.1641 | 0.0443 |          -0.0518 |           0.0054 | True                |
| primary     | BM25 vs FLIM-fallback               | rr        | mixedlm_powell     |      691 |            -0.0103 | -0.0903 |  0.0697 | 0.8012 |          -0.0479 |          -0.1047 | False               |
| primary     | BM25 vs FLIM-fallback               | top10     | mixedlm_lbfgs      |      691 |             0.0252 | -0.071  |  0.1213 | 0.6078 |          -0.0607 |          -0.0845 | False               |
| primary     | BM25-parse vs FLIM-strict (control) | ap        | mixedlm_lbfgs      |      691 |            -0.0352 | -0.0962 |  0.0259 | 0.2588 |           0.0013 |          -0.0499 | False               |
| primary     | BM25-parse vs FLIM-strict (control) | cfr10     | mixedlm_powell     |      691 |            -0.0266 | -0.1042 |  0.0511 | 0.5024 |          -0.0194 |          -0.0581 | False               |
| primary     | BM25-parse vs FLIM-strict (control) | rr        | mixedlm_powell     |      691 |            -0.1017 | -0.1794 | -0.024  | 0.0103 |           0.005  |          -0.1255 | False               |
| primary     | BM25-parse vs FLIM-strict (control) | top10     | mixedlm_lbfgs      |      691 |            -0.0541 | -0.153  |  0.0448 | 0.2837 |          -0.0251 |          -0.1033 | False               |
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
| primary     | BLAZE     | all    | Mono-fix |      478 | 0.314 | 0.252 |   0.426 |            0.314 |            nan     |            0.252 |            nan     |            1     |              0.998 |        0.004 |          0.005 |
| primary     | BLAZE     | all    | Poly-fix |      213 | 0.4   | 0.232 |   0.341 |            0.369 |              0.106 |            0.278 |              0.1   |            0.981 |              0.108 |        0.008 |          0.011 |
| primary     | BLAZE     | parse  | Mono-fix |      478 | 0.335 | 0.273 |   0.442 |            0.335 |            nan     |            0.273 |            nan     |            1     |              0.998 |        0.005 |          0.007 |
| primary     | BLAZE     | parse  | Poly-fix |      213 | 0.395 | 0.18  |   0.294 |            0.402 |              0     |            0.307 |              0     |            0.981 |              0.108 |        0.008 |          0.012 |
| primary     | BLAZE_ALL | all    | Mono-fix |      103 | 0.178 | 0.12  |   0.195 |            0.178 |            nan     |            0.12  |            nan     |            1     |              1     |        0.001 |          0.001 |
| primary     | BLAZE_ALL | all    | Poly-fix |       21 | 0.228 | 0.079 |   0.121 |            0.152 |              0.102 |            0.067 |              0.099 |            1     |              0.143 |        0.002 |          0.002 |
| primary     | BLAZE_ALL | parse  | Mono-fix |      103 | 0.188 | 0.125 |   0.201 |            0.188 |            nan     |            0.125 |            nan     |            1     |              1     |        0.001 |          0.001 |
| primary     | BLAZE_ALL | parse  | Poly-fix |       21 | 0.157 | 0.054 |   0.08  |            0.157 |              0     |            0.072 |              0     |            1     |              0.143 |        0.001 |          0.002 |
| primary     | BM25      | all    | Mono-fix |      981 | 0.389 | 0.311 |   0.471 |            0.389 |            nan     |            0.311 |            nan     |            1     |              0.999 |        0.004 |          0.006 |
| primary     | BM25      | all    | Poly-fix |      418 | 0.436 | 0.274 |   0.401 |            0.357 |              0.185 |            0.277 |              0.167 |            0.983 |              0.105 |        0.009 |          0.013 |
| primary     | BM25      | parse  | Mono-fix |      981 | 0.449 | 0.36  |   0.515 |            0.449 |            nan     |            0.36  |            nan     |            1     |              0.999 |        0.006 |          0.009 |
| primary     | BM25      | parse  | Poly-fix |      418 | 0.445 | 0.219 |   0.32  |            0.453 |              0     |            0.351 |              0     |            0.983 |              0.105 |        0.009 |          0.014 |
| primary     | FLIM      | all    | Mono-fix |      478 | 0.462 | 0.376 |   0.553 |            0.462 |            nan     |            0.376 |            nan     |            1     |              0.998 |        0.004 |          0.005 |
| primary     | FLIM      | all    | Poly-fix |      213 | 0.56  | 0.299 |   0.43  |            0.566 |              0.047 |            0.431 |              0.045 |            0.981 |              0.108 |        0.008 |          0.011 |
| primary     | FLIM      | parse  | Mono-fix |      478 | 0.464 | 0.379 |   0.561 |            0.464 |            nan     |            0.379 |            nan     |            1     |              0.998 |        0.005 |          0.007 |
| primary     | FLIM      | parse  | Poly-fix |      213 | 0.564 | 0.267 |   0.383 |            0.575 |              0     |            0.441 |              0     |            0.981 |              0.108 |        0.008 |          0.012 |
| primary     | LocAgent  | all    | Mono-fix |       32 | 0.495 | 0.368 |   0.519 |            0.495 |            nan     |            0.368 |            nan     |            1     |              1     |        0.008 |          0.011 |
| primary     | LocAgent  | all    | Poly-fix |       55 | 0.538 | 0.174 |   0.223 |            0.538 |              0.001 |            0.255 |              0.001 |            1     |              0.127 |        0.013 |          0.021 |
| primary     | LocAgent  | parse  | Mono-fix |       32 | 0.495 | 0.369 |   0.519 |            0.495 |            nan     |            0.369 |            nan     |            1     |              1     |        0.011 |          0.017 |
| primary     | LocAgent  | parse  | Poly-fix |       55 | 0.538 | 0.173 |   0.223 |            0.538 |              0     |            0.256 |              0     |            1     |              0.127 |        0.013 |          0.021 |

## Sensitivity — interaction estimate under each condition

|                                               |   P_behavioural |   P_test_only |   S1_no_tests |   S2_headline |   S2_strict |   S3_universe_T |   S4_untangled |   S5_fold1 |   S6_kept+removed |   S6_removed |   primary |
|:----------------------------------------------|----------------:|--------------:|--------------:|--------------:|------------:|----------------:|---------------:|-----------:|------------------:|-------------:|----------:|
| ('BLAZE_ALL vs BLAZE (ablation)', 'ap')       |        nan      |        0.0113 |        0.0208 |       -0.0123 |    nan      |          0.0074 |         0.0018 |     0.0018 |            0.0185 |     nan      |    0.0018 |
| ('BM25 vs FLIM-fallback', 'ap')               |          0.0958 |        0.0388 |        0.0234 |        0.0547 |      0.0607 |          0.069  |         0.0643 |     0.0643 |            0.0485 |      -0.0125 |    0.0643 |
| ('BM25 vs FLIM-strict', 'ap')                 |          0.117  |        0.0788 |        0.0272 |        0.0916 |      0.0773 |          0.099  |         0.0969 |     0.0969 |            0.0878 |       0.0617 |    0.0969 |
| ('BM25 vs LocAgent', 'ap10')                  |        nan      |        0.335  |       -0.079  |        0.2915 |    nan      |          0.3274 |         0.2915 |     0.2915 |            0.3218 |     nan      |    0.2915 |
| ('BM25-parse vs FLIM-strict (control)', 'ap') |         -0.0432 |       -0.0351 |       -0.0419 |       -0.0464 |     -0.0005 |         -0.0352 |        -0.0352 |    -0.0352 |           -0.0386 |      -0.0425 |   -0.0352 |

