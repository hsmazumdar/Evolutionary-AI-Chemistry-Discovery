# M3 results: SynthNN-style composition PU baseline (exploratory)


## decisive (9 systems), tie-fair expected recall

| arm | R@10 | R@50 | R@100 | R@500 | R@1000 | MRR |
|---|---|---|---|---|---|---|
| BLEND (RF + pooled template) | 0.101 | 0.267 | 0.379 | 0.696 | 0.805 | 0.056 |
| TPOOL (pooled template) | 0.122 | 0.242 | 0.336 | 0.621 | 0.724 | 0.032 |
| SYNTHNN-POOL (composition PU, pooled) | 0.062 | 0.124 | 0.146 | 0.252 | 0.342 | 0.024 |
| SYNTHNN-TARGET (composition PU, target only) | 0.034 | 0.093 | 0.136 | 0.285 | 0.394 | 0.017 |
| template target-only | 0.084 | 0.210 | 0.298 | 0.494 | 0.637 | 0.025 |
| RF alone | 0.048 | 0.112 | 0.155 | 0.310 | 0.458 | 0.023 |
| random | 0.001 | 0.001 | 0.002 | 0.013 | 0.023 | 0.000 |

Paired comparisons (two-sided):
- SYNTHNN-POOL (composition PU, pooled) − TPOOL (pooled template), recall@100: -0.190 [-0.293, -0.090], W/L 1/8, p 0.0078
- SYNTHNN-POOL (composition PU, pooled) − TPOOL (pooled template), recall@500: -0.370 [-0.513, -0.224], W/L 0/9, p 0.0039
- SYNTHNN-POOL (composition PU, pooled) − BLEND (RF + pooled template), recall@100: -0.233 [-0.324, -0.146], W/L 0/9, p 0.0039
- SYNTHNN-POOL (composition PU, pooled) − BLEND (RF + pooled template), recall@500: -0.444 [-0.543, -0.345], W/L 0/9, p 0.0039
- SYNTHNN-POOL (composition PU, pooled) − SYNTHNN-TARGET (composition PU, target only), recall@100: +0.010 [-0.018, +0.038], W/L 4/5, p 0.5703
- SYNTHNN-POOL (composition PU, pooled) − SYNTHNN-TARGET (composition PU, target only), recall@500: -0.034 [-0.064, -0.003], W/L 3/6, p 0.1289
- SYNTHNN-POOL (composition PU, pooled) − RF alone, recall@100: -0.009 [-0.029, +0.012], W/L 3/6, p 0.4258
- SYNTHNN-POOL (composition PU, pooled) − RF alone, recall@500: -0.058 [-0.095, -0.027], W/L 1/7, p 0.0156
- SYNTHNN-TARGET (composition PU, target only) − template target-only, recall@100: -0.162 [-0.259, -0.084], W/L 0/9, p 0.0039
- SYNTHNN-TARGET (composition PU, target only) − template target-only, recall@500: -0.209 [-0.352, -0.066], W/L 1/8, p 0.0273

By arity (recall@100 / recall@500):

| arm | binary | ternary | quaternary |
|---|---|---|---|
| BLEND (RF + pooled template) | 0.555 / 0.799 | 0.155 / 0.595 | 0.000 / 0.031 |
| SYNTHNN-POOL (composition PU, pooled) | 0.234 / 0.345 | 0.011 / 0.122 | 0.000 / 0.000 |
| TPOOL (pooled template) | 0.462 / 0.691 | 0.192 / 0.572 | 0.000 / 0.000 |

## replication (20 systems), tie-fair expected recall

| arm | R@10 | R@50 | R@100 | R@500 | R@1000 | MRR |
|---|---|---|---|---|---|---|
| BLEND (RF + pooled template) | 0.123 | 0.315 | 0.430 | 0.754 | 0.852 | 0.063 |
| TPOOL (pooled template) | 0.133 | 0.313 | 0.403 | 0.644 | 0.770 | 0.037 |
| SYNTHNN-POOL (composition PU, pooled) | 0.040 | 0.093 | 0.123 | 0.269 | 0.387 | 0.016 |
| SYNTHNN-TARGET (composition PU, target only) | 0.026 | 0.077 | 0.115 | 0.283 | 0.402 | 0.013 |
| template target-only | 0.107 | 0.243 | 0.324 | 0.544 | 0.668 | 0.032 |
| RF alone | 0.035 | 0.097 | 0.137 | 0.346 | 0.528 | 0.017 |
| random | 0.001 | 0.001 | 0.002 | 0.011 | 0.022 | 0.000 |

Paired comparisons (two-sided):
- SYNTHNN-POOL (composition PU, pooled) − TPOOL (pooled template), recall@100: -0.281 [-0.338, -0.221], W/L 0/20, p 0.0000
- SYNTHNN-POOL (composition PU, pooled) − TPOOL (pooled template), recall@500: -0.375 [-0.453, -0.295], W/L 0/20, p 0.0000
- SYNTHNN-POOL (composition PU, pooled) − BLEND (RF + pooled template), recall@100: -0.307 [-0.364, -0.250], W/L 0/20, p 0.0000
- SYNTHNN-POOL (composition PU, pooled) − BLEND (RF + pooled template), recall@500: -0.485 [-0.537, -0.431], W/L 0/20, p 0.0000
- SYNTHNN-POOL (composition PU, pooled) − SYNTHNN-TARGET (composition PU, target only), recall@100: +0.007 [-0.011, +0.025], W/L 11/7, p 0.3491
- SYNTHNN-POOL (composition PU, pooled) − SYNTHNN-TARGET (composition PU, target only), recall@500: -0.014 [-0.039, +0.011], W/L 7/13, p 0.3300
- SYNTHNN-POOL (composition PU, pooled) − RF alone, recall@100: -0.014 [-0.040, +0.008], W/L 9/11, p 0.3488
- SYNTHNN-POOL (composition PU, pooled) − RF alone, recall@500: -0.077 [-0.107, -0.045], W/L 1/18, p 0.0006
- SYNTHNN-TARGET (composition PU, target only) − template target-only, recall@100: -0.209 [-0.262, -0.156], W/L 0/20, p 0.0000
- SYNTHNN-TARGET (composition PU, target only) − template target-only, recall@500: -0.261 [-0.342, -0.181], W/L 2/18, p 0.0000

By arity (recall@100 / recall@500):

| arm | binary | ternary | quaternary |
|---|---|---|---|
| BLEND (RF + pooled template) | 0.616 / 0.890 | 0.156 / 0.571 | 0.000 / 0.026 |
| SYNTHNN-POOL (composition PU, pooled) | 0.175 / 0.306 | 0.031 / 0.210 | 0.000 / 0.011 |
| TPOOL (pooled template) | 0.576 / 0.777 | 0.187 / 0.513 | 0.000 / 0.000 |

## pooled29 (29 systems), tie-fair expected recall

| arm | R@10 | R@50 | R@100 | R@500 | R@1000 | MRR |
|---|---|---|---|---|---|---|
| BLEND (RF + pooled template) | 0.116 | 0.300 | 0.414 | 0.736 | 0.838 | 0.061 |
| TPOOL (pooled template) | 0.129 | 0.291 | 0.382 | 0.637 | 0.756 | 0.036 |
| SYNTHNN-POOL (composition PU, pooled) | 0.047 | 0.102 | 0.130 | 0.264 | 0.373 | 0.018 |
| SYNTHNN-TARGET (composition PU, target only) | 0.029 | 0.082 | 0.122 | 0.284 | 0.400 | 0.014 |
| template target-only | 0.100 | 0.233 | 0.316 | 0.529 | 0.658 | 0.030 |
| RF alone | 0.039 | 0.101 | 0.143 | 0.335 | 0.506 | 0.019 |
| random | 0.001 | 0.001 | 0.002 | 0.012 | 0.022 | 0.000 |

Paired comparisons (two-sided):
- SYNTHNN-POOL (composition PU, pooled) − TPOOL (pooled template), recall@100: -0.253 [-0.306, -0.197], W/L 1/28, p 0.0000
- SYNTHNN-POOL (composition PU, pooled) − TPOOL (pooled template), recall@500: -0.373 [-0.443, -0.302], W/L 0/29, p 0.0000
- SYNTHNN-POOL (composition PU, pooled) − BLEND (RF + pooled template), recall@100: -0.284 [-0.333, -0.234], W/L 0/29, p 0.0000
- SYNTHNN-POOL (composition PU, pooled) − BLEND (RF + pooled template), recall@500: -0.472 [-0.520, -0.422], W/L 0/29, p 0.0000
- SYNTHNN-POOL (composition PU, pooled) − SYNTHNN-TARGET (composition PU, target only), recall@100: +0.008 [-0.007, +0.023], W/L 15/12, p 0.2796
- SYNTHNN-POOL (composition PU, pooled) − SYNTHNN-TARGET (composition PU, target only), recall@500: -0.020 [-0.040, +0.000], W/L 10/19, p 0.0724
- SYNTHNN-POOL (composition PU, pooled) − RF alone, recall@100: -0.013 [-0.031, +0.004], W/L 12/17, p 0.2297
- SYNTHNN-POOL (composition PU, pooled) − RF alone, recall@500: -0.071 [-0.096, -0.047], W/L 2/25, p 0.0000
- SYNTHNN-TARGET (composition PU, target only) − template target-only, recall@100: -0.194 [-0.243, -0.148], W/L 0/29, p 0.0000
- SYNTHNN-TARGET (composition PU, target only) − template target-only, recall@500: -0.245 [-0.317, -0.174], W/L 3/26, p 0.0000

By arity (recall@100 / recall@500):

| arm | binary | ternary | quaternary |
|---|---|---|---|
| BLEND (RF + pooled template) | 0.597 / 0.862 | 0.156 / 0.579 | 0.000 / 0.028 |
| SYNTHNN-POOL (composition PU, pooled) | 0.193 / 0.318 | 0.025 / 0.183 | 0.000 / 0.007 |
| TPOOL (pooled template) | 0.541 / 0.750 | 0.189 / 0.532 | 0.000 / 0.000 |

Inner-validation choices (hidden width, unlabelled ratio), count over splits:

|                                                           |   n |
|:----------------------------------------------------------|----:|
| ('SYNTHNN-POOL (composition PU, pooled)', 64, 5)          |  90 |
| ('SYNTHNN-POOL (composition PU, pooled)', 64, 20)         |  22 |
| ('SYNTHNN-POOL (composition PU, pooled)', 128, 5)         |  18 |
| ('SYNTHNN-POOL (composition PU, pooled)', 128, 20)        |  15 |
| ('SYNTHNN-TARGET (composition PU, target only)', 64, 5)   |  89 |
| ('SYNTHNN-TARGET (composition PU, target only)', 64, 20)  |  31 |
| ('SYNTHNN-TARGET (composition PU, target only)', 128, 5)  |  17 |
| ('SYNTHNN-TARGET (composition PU, target only)', 128, 20) |   8 |