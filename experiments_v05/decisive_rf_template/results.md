# Decisive experiment: results
Concept and direction: Himanshu Mazumdar, R&D Centre, Dharmsinh Desai University · Code developed with AI assistance.
Pre-registration: `PREREGISTRATION.md`, commit e799bda (2026-10-14 12:22 IST), made before any data was built or run.

## Verdict (confirmatory)
**HD is NOT supported under the pre-registered criterion.** The blend of PU random forest and the pooled template prior scores
recall@100 = 0.379, against 0.337 for the pooled template prior alone. The difference is **+0.042**, 95% system-cluster
bootstrap CI [−0.002, +0.085], with d_z = +0.59 and 6 wins / 3 losses over 9 systems. The one-sided Wilcoxon gives
**p = 0.0645, which is above alpha = 0.05**. The gain does meet the ≥ 0.02 margin, but success needed both conditions, so
the pre-registered outcome is failure. The direction is positive and the CI only just reaches 0. This is weak, inconclusive
evidence that the RF adds something, not a demonstration. Per the protocol, the work goes forward as a benchmark /
negative-result study.

## Systems and leakage audit
The selection rule reproduced the V05 nine exactly, and 9 fresh systems were eligible (no shortfall): Mn-Na-O-V, As-O-Sr-V,
Ba-Mn-O-Si, Cl-O-Pb-V, Cu-O-P-S, Li-O-Si-V, O-Rb-Se-V, Al-Ba-Ge-O, Cl-Hg-N-O. Sub-system overlap is substantial:
8–34 of each system's 63–69 observed multi-element formulas (mostly binary/ternary sub-system compounds) also occur in other
systems (`results/overlap_audit.csv`). Source formulas identical to a target test formula were removed as pre-registered. A stricter
sensitivity analysis removed every source formula inside the target's element sub-space; it gave the same conclusion
(+0.053 [+0.007, +0.097], two-sided p = 0.074). The dataset has its own SHA-256 manifest (`data/MANIFEST.json`).
Measured-enthalpy labels were not built for the fresh systems because this experiment does not use them.

## Primary (confirmatory)
BLEND 0.379 vs TPOOL 0.337: diff +0.042 [-0.002, +0.085], d_z +0.59, W/L 6/3, p (greater) 0.0645; **success = False**

## Secondary (exploratory)
- recall@10: -0.019 [-0.050, +0.016], d_z -0.35, W/L 3/6, p (two-sided) 0.2500
- recall@50: +0.023 [-0.009, +0.050], d_z +0.46, W/L 7/2, p (two-sided) 0.2031
- recall@500: +0.074 [+0.017, +0.135], d_z +0.77, W/L 6/3, p (two-sided) 0.0742
- recall@1000: +0.081 [+0.043, +0.120], d_z +1.30, W/L 8/1, p (two-sided) 0.0078
- MRR: +0.016 [+0.004, +0.029], d_z +0.81, W/L 7/2, p (two-sided) 0.0547
- strict-leakage recall@100: +0.053 [+0.007, +0.097], d_z +0.72, W/L 7/2, p (two-sided) 0.0742
- BLEND vs RF alone recall@100: +0.224 [+0.141, +0.309], d_z +1.65, W/L 9/0, p (two-sided) 0.0039

Chosen w (45 splits): {0.1: 20, 0.2: 8, 0.3: 8, 0.4: 3, 0.5: 3, 0.6: 1, 0.7: 1, 0.9: 1}

## All metrics (mean over systems)
| method                       |   recall@10 |   recall@50 |   recall@100 |   recall@500 |   recall@1000 |   MRR |   median_rank |   precision@100_observed |   enrichment@100 |
|:-----------------------------|------------:|------------:|-------------:|-------------:|--------------:|------:|--------------:|-------------------------:|-----------------:|
| BLEND strict-leakage         |       0.107 |       0.271 |        0.383 |        0.68  |         0.789 | 0.056 |       245     |                    0.097 |          158.358 |
| BLEND (RF + pooled template) |       0.101 |       0.267 |        0.379 |        0.696 |         0.805 | 0.056 |       230.478 |                    0.096 |          156.655 |
| TPOOL (pooled template)      |       0.12  |       0.245 |        0.337 |        0.621 |         0.724 | 0.039 |       344.2   |                    0.085 |          139.239 |
| TPOOL strict-leakage         |       0.12  |       0.245 |        0.33  |        0.621 |         0.723 | 0.039 |       339.389 |                    0.083 |          136.278 |
| template target-only         |       0.084 |       0.214 |        0.303 |        0.492 |         0.641 | 0.028 |       543.333 |                    0.076 |          125.11  |
| RF alone                     |       0.048 |       0.112 |        0.155 |        0.311 |         0.458 | 0.024 |      1295.79  |                    0.04  |           63.893 |
| random                       |       0.001 |       0.001 |        0.002 |        0.013 |         0.023 | 0     |     20481.1   |                    0     |            0.736 |

## Per-system recall@100 (mean of 5 splits)
| system     |   BLEND (RF + pooled template) |   TPOOL (pooled template) |   RF alone |   template target-only |   random |   BLEND−TPOOL |
|:-----------|-------------------------------:|--------------------------:|-----------:|-----------------------:|---------:|--------------:|
| Al-Ba-Ge-O |                          0.313 |                     0.322 |      0.035 |                  0.27  |    0     |        -0.009 |
| As-O-Sr-V  |                          0.4   |                     0.354 |      0.238 |                  0.308 |    0     |         0.046 |
| Ba-Mn-O-Si |                          0.492 |                     0.4   |      0.042 |                  0.3   |    0     |         0.092 |
| Cl-Hg-N-O  |                          0.408 |                     0.488 |      0.064 |                  0.544 |    0     |        -0.08  |
| Cl-O-Pb-V  |                          0.338 |                     0.292 |      0.208 |                  0.285 |    0.008 |         0.046 |
| Cu-O-P-S   |                          0.392 |                     0.269 |      0.062 |                  0.208 |    0     |         0.123 |
| Li-O-Si-V  |                          0.292 |                     0.233 |      0.283 |                  0.192 |    0.008 |         0.058 |
| Mn-Na-O-V  |                          0.422 |                     0.289 |      0.244 |                  0.304 |    0     |         0.133 |
| O-Rb-Se-V  |                          0.354 |                     0.385 |      0.215 |                  0.315 |    0     |        -0.031 |

## Exploratory reading (not confirmatory, uncorrected)
- The blend's advantage grows deeper in the ranking: recall@1000 +0.081 (8 of 9 systems, p = 0.008) and MRR +0.016. At the very top
  the blend is slightly worse: recall@10 −0.019.
- RF alone is weak (0.155). Pooled templates beat target-only templates (0.337 vs 0.303), which replicates the V05 exploratory finding on
  fresh systems.
- Inner validation mostly chose small RF weights (w = 0.1 in 20 of 45 splits).
- n = 9 means the smallest attainable one-sided p is 0.002. With the observed d_z ≈ 0.6, power is roughly 50%, so a replication with
  more systems would be needed to resolve this.

Runtime: 82 s on 8 CPU cores. Reproduce with `select_and_build.py`, then `run_decisive.py`, then `analyze.py`.
