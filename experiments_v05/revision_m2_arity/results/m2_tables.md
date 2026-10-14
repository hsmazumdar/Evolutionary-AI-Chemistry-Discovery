# M2 results: recall by formula arity (exploratory; data already seen)

Tie-fair expected recall (M1) unless marked 'stable'. Positives are test formulas of each split (40% of observed multi-element formulas).


## decisive (9 systems)

Distinct observed test formulas per system (union over 5 splits) by arity: binary median 31 (range 24–40, total 297), ternary median 24 (range 17–30, total 213), quaternary median 2 (range 0–4, total 15)

Systems with ≥5 distinct quaternary test formulas: 0 of 9. Share of all test positives (formula×split): binary 58%, ternary 40%, quaternary 2%


| method | binary R@100 / R@500 / MRR | ternary R@100 / R@500 / MRR | quaternary R@100 / R@500 / MRR |
|---|---|---|---|
| BLEND (RF + pooled template) | 0.555 / 0.799 / 0.094 | 0.155 / 0.595 / 0.007 | 0.000 / 0.031 / 0.001 |
| BLEND strict-leakage | 0.548 / 0.774 / 0.094 | 0.176 / 0.594 / 0.008 | 0.000 / 0.031 / 0.001 |
| RF alone | 0.254 / 0.482 / 0.037 | 0.008 / 0.066 / 0.001 | 0.000 / 0.000 / 0.000 |
| TPOOL (pooled template) | 0.462 / 0.691 / 0.054 | 0.192 / 0.572 / 0.006 | 0.000 / 0.000 / 0.000 |
| TPOOL + RF tie-break only | 0.465 / 0.691 / 0.099 | 0.195 / 0.574 / 0.006 | 0.000 / 0.000 / 0.000 |
| TPOOL strict-leakage | 0.447 / 0.679 / 0.053 | 0.197 / 0.581 / 0.006 | 0.000 / 0.000 / 0.000 |
| random | 0.003 / 0.014 / 0.000 | 0.000 / 0.011 / 0.000 | 0.000 / 0.016 / 0.000 |
| template target-only | 0.429 / 0.614 / 0.041 | 0.138 / 0.354 / 0.005 | 0.000 / 0.136 / 0.001 |

(n systems contributing: binary 9, ternary 9, quaternary 8)


BLEND − TPOOL by arity (paired over systems with ≥1 test formula of that arity, two-sided Wilcoxon, bootstrap 95% CI):

- binary recall@100: +0.093 [+0.023, +0.153], W/L 8/1 (n=9), p 0.0742
- binary recall@500: +0.108 [+0.051, +0.161], W/L 7/1 (n=9), p 0.0156
- ternary recall@100: -0.038 [-0.099, +0.025], W/L 2/6 (n=9), p 0.2500
- ternary recall@500: +0.023 [-0.080, +0.119], W/L 4/4 (n=9), p 0.8438
- quaternary recall@100: +0.000 [+0.000, +0.000], W/L 0/0 (n=8), p 1.0000
- quaternary recall@500: +0.031 [+0.000, +0.094], W/L 1/0 (n=8), p 1.0000

## replication (20 systems)

Distinct observed test formulas per system (union over 5 splits) by arity: binary median 29 (range 20–45, total 603), ternary median 20 (range 5–30, total 378), quaternary median 1 (range 0–11, total 31)

Systems with ≥5 distinct quaternary test formulas: 1 of 20. Share of all test positives (formula×split): binary 60%, ternary 37%, quaternary 3%


| method | binary R@100 / R@500 / MRR | ternary R@100 / R@500 / MRR | quaternary R@100 / R@500 / MRR |
|---|---|---|---|
| BLEND (RF + pooled template) | 0.616 / 0.890 / 0.101 | 0.156 / 0.571 / 0.007 | 0.000 / 0.026 / 0.001 |
| BLEND strict-leakage | 0.621 / 0.881 / 0.101 | 0.169 / 0.550 / 0.008 | 0.000 / 0.026 / 0.001 |
| RF alone | 0.192 / 0.440 / 0.025 | 0.035 / 0.180 / 0.002 | 0.000 / 0.005 / 0.000 |
| TPOOL (pooled template) | 0.576 / 0.777 / 0.060 | 0.187 / 0.513 / 0.005 | 0.000 / 0.000 / 0.000 |
| TPOOL + RF tie-break only | 0.584 / 0.777 / 0.105 | 0.198 / 0.516 / 0.005 | 0.000 / 0.000 / 0.000 |
| TPOOL strict-leakage | 0.573 / 0.771 / 0.060 | 0.191 / 0.521 / 0.005 | 0.000 / 0.000 / 0.000 |
| random | 0.001 / 0.006 / 0.000 | 0.003 / 0.019 / 0.000 | 0.000 / 0.000 / 0.000 |
| template target-only | 0.486 / 0.676 / 0.053 | 0.097 / 0.382 / 0.004 | 0.000 / 0.200 / 0.001 |

(n systems contributing: binary 20, ternary 20, quaternary 15)


BLEND − TPOOL by arity (paired over systems with ≥1 test formula of that arity, two-sided Wilcoxon, bootstrap 95% CI):

- binary recall@100: +0.040 [+0.003, +0.075], W/L 14/6 (n=20), p 0.0328
- binary recall@500: +0.113 [+0.067, +0.164], W/L 18/1 (n=20), p 0.0005
- ternary recall@100: -0.031 [-0.102, +0.040], W/L 7/13 (n=20), p 0.4524
- ternary recall@500: +0.058 [-0.015, +0.129], W/L 13/6 (n=20), p 0.1474
- quaternary recall@100: +0.000 [+0.000, +0.000], W/L 0/0 (n=15), p 1.0000
- quaternary recall@500: +0.026 [+0.000, +0.068], W/L 2/0 (n=15), p 0.1797

## pooled29 (29 systems)

Distinct observed test formulas per system (union over 5 splits) by arity: binary median 31 (range 20–45, total 900), ternary median 21 (range 5–30, total 591), quaternary median 1 (range 0–11, total 46)

Systems with ≥5 distinct quaternary test formulas: 1 of 29. Share of all test positives (formula×split): binary 59%, ternary 38%, quaternary 3%


| method | binary R@100 / R@500 / MRR | ternary R@100 / R@500 / MRR | quaternary R@100 / R@500 / MRR |
|---|---|---|---|
| BLEND (RF + pooled template) | 0.597 / 0.862 / 0.099 | 0.156 / 0.579 / 0.007 | 0.000 / 0.028 / 0.001 |
| BLEND strict-leakage | 0.599 / 0.848 / 0.099 | 0.171 / 0.563 / 0.008 | 0.000 / 0.028 / 0.001 |
| RF alone | 0.211 / 0.453 / 0.029 | 0.027 / 0.145 / 0.002 | 0.000 / 0.003 / 0.000 |
| TPOOL (pooled template) | 0.541 / 0.750 / 0.058 | 0.189 / 0.532 / 0.005 | 0.000 / 0.000 / 0.000 |
| TPOOL + RF tie-break only | 0.547 / 0.751 / 0.103 | 0.197 / 0.534 / 0.006 | 0.000 / 0.000 / 0.000 |
| TPOOL strict-leakage | 0.534 / 0.743 / 0.058 | 0.193 / 0.539 / 0.005 | 0.000 / 0.000 / 0.000 |
| random | 0.001 / 0.009 / 0.000 | 0.002 / 0.017 / 0.000 | 0.000 / 0.005 / 0.000 |
| template target-only | 0.468 / 0.657 / 0.049 | 0.110 / 0.373 / 0.004 | 0.000 / 0.178 / 0.001 |

(n systems contributing: binary 29, ternary 29, quaternary 23)


BLEND − TPOOL by arity (paired over systems with ≥1 test formula of that arity, two-sided Wilcoxon, bootstrap 95% CI):

- binary recall@100: +0.056 [+0.022, +0.089], W/L 22/7 (n=29), p 0.0022
- binary recall@500: +0.111 [+0.074, +0.150], W/L 25/2 (n=29), p 0.0000
- ternary recall@100: -0.033 [-0.086, +0.020], W/L 9/19 (n=29), p 0.2188
- ternary recall@500: +0.047 [-0.013, +0.106], W/L 17/10 (n=29), p 0.1428
- quaternary recall@100: +0.000 [+0.000, +0.000], W/L 0/0 (n=23), p 1.0000
- quaternary recall@500: +0.028 [+0.000, +0.061], W/L 3/0 (n=23), p 0.1088