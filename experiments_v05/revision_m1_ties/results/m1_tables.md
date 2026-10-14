# M1 results: fair tie-breaking (exploratory sensitivity; pre-registered results unchanged)


## Study: decisive (9 systems)

Tie groups of test formulas: TPOOL median size 21 (mean 226.8), 100% of test formulas tied with ≥1 other candidate; BLEND median 1, 5% tied.


| scoring | k | BLEND | TPOOL | BLEND−TPOOL [95% CI], W/L/T, Wilcoxon p | 
|---|---|---|---|---|
| stable | 10 | 0.101 | 0.120 | -0.019 [-0.050, +0.016], W/L/T 3/6/0, p 0.2891 (two-sided) |
| stable | 50 | 0.267 | 0.245 | +0.023 [-0.009, +0.050], W/L/T 7/2/0, p 0.2031 (two-sided) |
| stable | 100 | 0.379 | 0.337 | +0.042 [-0.002, +0.085], W/L/T 6/3/0, p 0.0645 (greater) |
| stable | 500 | 0.696 | 0.621 | +0.074 [+0.017, +0.135], W/L/T 6/3/0, p 0.0742 (two-sided) |
| stable | 1000 | 0.805 | 0.724 | +0.081 [+0.043, +0.120], W/L/T 8/1/0, p 0.0078 (two-sided) |
| avgrank | 10 | 0.101 | 0.120 | -0.019 [-0.053, +0.019], W/L/T 3/6/0, p 0.4414 (two-sided) |
| avgrank | 50 | 0.267 | 0.239 | +0.028 [-0.008, +0.061], W/L/T 6/3/0, p 0.1641 (two-sided) |
| avgrank | 100 | 0.379 | 0.339 | +0.040 [-0.005, +0.084], W/L/T 6/3/0, p 0.0645 (greater) |
| avgrank | 500 | 0.696 | 0.621 | +0.074 [+0.017, +0.135], W/L/T 6/3/0, p 0.0742 (two-sided) |
| avgrank | 1000 | 0.805 | 0.722 | +0.083 [+0.043, +0.124], W/L/T 8/1/0, p 0.0078 (two-sided) |
| expected | 10 | 0.101 | 0.122 | -0.021 [-0.050, +0.012], W/L/T 3/6/0, p 0.3008 (two-sided) |
| expected | 50 | 0.267 | 0.242 | +0.025 [-0.008, +0.056], W/L/T 6/3/0, p 0.2031 (two-sided) |
| expected | 100 | 0.379 | 0.336 | +0.043 [-0.002, +0.086], W/L/T 6/3/0, p 0.0645 (greater) |
| expected | 500 | 0.696 | 0.621 | +0.074 [+0.017, +0.135], W/L/T 6/3/0, p 0.0742 (two-sided) |
| expected | 1000 | 0.805 | 0.724 | +0.081 [+0.043, +0.122], W/L/T 8/1/0, p 0.0078 (two-sided) |

**All arms, recall@100 (stable → expected under fair ties):**

- BLEND (RF + pooled template): 0.379 → 0.379
- BLEND strict-leakage: 0.383 → 0.383
- RF alone: 0.155 → 0.155
- TPOOL (pooled template): 0.337 → 0.336
- TPOOL + RF tie-break only: 0.339 → 0.339
- TPOOL strict-leakage: 0.330 → 0.329
- random: 0.002 → 0.002
- template target-only: 0.303 → 0.298

Exploratory control, TPOOL with RF used only as tie-breaker vs TPOOL (fair ties), recall@100: +0.003 [+0.001, +0.004], W/L/T 6/0/3, p 0.0312

BLEND vs TPOOL+RF-tie-break-only, recall@100 (fair ties): +0.040 [-0.005, +0.084], W/L/T 6/3/0, p 0.1289


**Random tie-breaking, 100 seeds:** recall@100 TPOOL 0.336 [0.333, 0.338], BLEND 0.379; diff +0.043 (seed 2.5–97.5%: +0.041 to +0.046); Wilcoxon p median-ish mean 0.064 (range 0.055–0.088); fraction of seeds meeting the pre-registered rule (p<0.05 and diff≥0.02): 0.02; p<0.05 alone: 0.02. recall@500 diff +0.074 (+0.073 to +0.075).


## Study: replication (20 systems)

Tie groups of test formulas: TPOOL median size 12 (mean 137.3), 100% of test formulas tied with ≥1 other candidate; BLEND median 1, 4% tied.


| scoring | k | BLEND | TPOOL | BLEND−TPOOL [95% CI], W/L/T, Wilcoxon p | 
|---|---|---|---|---|
| stable | 10 | 0.123 | 0.134 | -0.011 [-0.038, +0.013], W/L/T 9/11/0, p 0.6274 (two-sided) |
| stable | 50 | 0.315 | 0.316 | -0.001 [-0.028, +0.024], W/L/T 12/7/1, p 0.8092 (two-sided) |
| stable | 100 | 0.430 | 0.407 | +0.023 [-0.008, +0.053], W/L/T 14/4/2, p 0.0468 (greater) |
| stable | 500 | 0.754 | 0.644 | +0.110 [+0.067, +0.152], W/L/T 18/2/0, p 0.0001 (two-sided) |
| stable | 1000 | 0.852 | 0.769 | +0.083 [+0.050, +0.116], W/L/T 18/2/0, p 0.0008 (two-sided) |
| avgrank | 10 | 0.123 | 0.126 | -0.003 [-0.030, +0.021], W/L/T 11/8/1, p 0.9039 (two-sided) |
| avgrank | 50 | 0.315 | 0.318 | -0.003 [-0.031, +0.023], W/L/T 11/8/1, p 0.9359 (two-sided) |
| avgrank | 100 | 0.430 | 0.403 | +0.027 [-0.005, +0.057], W/L/T 13/4/3, p 0.0564 (greater) |
| avgrank | 500 | 0.754 | 0.644 | +0.110 [+0.067, +0.153], W/L/T 18/2/0, p 0.0001 (two-sided) |
| avgrank | 1000 | 0.852 | 0.768 | +0.084 [+0.051, +0.118], W/L/T 18/2/0, p 0.0008 (two-sided) |
| expected | 10 | 0.123 | 0.133 | -0.010 [-0.036, +0.014], W/L/T 10/10/0, p 0.6477 (two-sided) |
| expected | 50 | 0.315 | 0.313 | +0.002 [-0.025, +0.027], W/L/T 12/8/0, p 0.6742 (two-sided) |
| expected | 100 | 0.430 | 0.403 | +0.027 [-0.005, +0.057], W/L/T 14/5/1, p 0.0418 (greater) |
| expected | 500 | 0.754 | 0.644 | +0.110 [+0.067, +0.152], W/L/T 18/2/0, p 0.0001 (two-sided) |
| expected | 1000 | 0.852 | 0.770 | +0.082 [+0.049, +0.116], W/L/T 18/2/0, p 0.0008 (two-sided) |

**All arms, recall@100 (stable → expected under fair ties):**

- BLEND (RF + pooled template): 0.430 → 0.430
- BLEND strict-leakage: 0.439 → 0.439
- RF alone: 0.138 → 0.137
- TPOOL (pooled template): 0.407 → 0.403
- TPOOL + RF tie-break only: 0.412 → 0.412
- TPOOL strict-leakage: 0.408 → 0.403
- random: 0.002 → 0.002
- template target-only: 0.326 → 0.324

Exploratory control, TPOOL with RF used only as tie-breaker vs TPOOL (fair ties), recall@100: +0.009 [+0.004, +0.014], W/L/T 16/1/3, p 0.0004

BLEND vs TPOOL+RF-tie-break-only, recall@100 (fair ties): +0.018 [-0.012, +0.047], W/L/T 12/4/4, p 0.1627


**Random tie-breaking, 100 seeds:** recall@100 TPOOL 0.403 [0.400, 0.406], BLEND 0.430; diff +0.027 (seed 2.5–97.5%: +0.024 to +0.030); Wilcoxon p median-ish mean 0.043 (range 0.030–0.060); fraction of seeds meeting the pre-registered rule (p<0.05 and diff≥0.02): 0.77; p<0.05 alone: 0.77. recall@500 diff +0.110 (+0.109 to +0.111).


## Study: pooled29 (29 systems)

Tie groups of test formulas: TPOOL median size 12 (mean 167.9), 100% of test formulas tied with ≥1 other candidate; BLEND median 1, 4% tied.


| scoring | k | BLEND | TPOOL | BLEND−TPOOL [95% CI], W/L/T, Wilcoxon p | 
|---|---|---|---|---|
| stable | 10 | 0.116 | 0.130 | -0.014 [-0.034, +0.006], W/L/T 12/17/0, p 0.2654 (two-sided) |
| stable | 50 | 0.300 | 0.294 | +0.006 [-0.015, +0.026], W/L/T 19/9/1, p 0.3869 (two-sided) |
| stable | 100 | 0.414 | 0.385 | +0.029 [+0.004, +0.054], W/L/T 20/7/2, p 0.0288 (two-sided) |
| stable | 500 | 0.736 | 0.637 | +0.099 [+0.064, +0.134], W/L/T 24/5/0, p 0.0000 (two-sided) |
| stable | 1000 | 0.838 | 0.755 | +0.082 [+0.057, +0.108], W/L/T 26/3/0, p 0.0000 (two-sided) |
| avgrank | 10 | 0.116 | 0.124 | -0.008 [-0.029, +0.013], W/L/T 14/14/1, p 0.6164 (two-sided) |
| avgrank | 50 | 0.300 | 0.294 | +0.006 [-0.017, +0.028], W/L/T 17/11/1, p 0.3869 (two-sided) |
| avgrank | 100 | 0.414 | 0.383 | +0.031 [+0.005, +0.056], W/L/T 19/7/3, p 0.0339 (two-sided) |
| avgrank | 500 | 0.736 | 0.637 | +0.099 [+0.064, +0.134], W/L/T 24/5/0, p 0.0000 (two-sided) |
| avgrank | 1000 | 0.838 | 0.754 | +0.084 [+0.058, +0.110], W/L/T 26/3/0, p 0.0000 (two-sided) |
| expected | 10 | 0.116 | 0.129 | -0.013 [-0.033, +0.006], W/L/T 13/16/0, p 0.2843 (two-sided) |
| expected | 50 | 0.300 | 0.291 | +0.009 [-0.013, +0.030], W/L/T 18/11/0, p 0.2843 (two-sided) |
| expected | 100 | 0.414 | 0.382 | +0.032 [+0.006, +0.057], W/L/T 20/8/1, p 0.0256 (two-sided) |
| expected | 500 | 0.736 | 0.637 | +0.099 [+0.064, +0.134], W/L/T 24/5/0, p 0.0000 (two-sided) |
| expected | 1000 | 0.838 | 0.756 | +0.082 [+0.056, +0.108], W/L/T 26/3/0, p 0.0000 (two-sided) |

**All arms, recall@100 (stable → expected under fair ties):**

- BLEND (RF + pooled template): 0.414 → 0.414
- BLEND strict-leakage: 0.422 → 0.422
- RF alone: 0.143 → 0.143
- TPOOL (pooled template): 0.385 → 0.382
- TPOOL + RF tie-break only: 0.389 → 0.389
- TPOOL strict-leakage: 0.383 → 0.380
- random: 0.002 → 0.002
- template target-only: 0.319 → 0.316

Exploratory control, TPOOL with RF used only as tie-breaker vs TPOOL (fair ties), recall@100: +0.007 [+0.003, +0.011], W/L/T 22/1/6, p 0.0000

BLEND vs TPOOL+RF-tie-break-only, recall@100 (fair ties): +0.025 [+0.000, +0.050], W/L/T 18/7/4, p 0.0578


**Random tie-breaking, 100 seeds:** recall@100 TPOOL 0.382 [0.380, 0.385], BLEND 0.414; diff +0.032 (seed 2.5–97.5%: +0.030 to +0.034); Wilcoxon p median-ish mean 0.025 (range 0.019–0.034); fraction of seeds meeting the pre-registered rule (p<0.05 and diff≥0.02): 1.00; p<0.05 alone: 1.00. recall@500 diff +0.099 (+0.098 to +0.100).
