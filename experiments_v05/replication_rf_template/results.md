# Replication: results
Concept and direction: Himanshu Mazumdar, R&D Centre, Dharmsinh Desai University · Code developed with AI assistance.
Pre-registration: `PREREGISTRATION.md`, commit 4b0c1ae (2026-10-14 19:18 IST). It was committed before any system was selected,
data was built, or anything was run.

## Verdict (confirmatory)
**The pre-registered success rule is met, narrowly.**

| | BLEND | TPOOL |
|---|---|---|
| recall@100 | 0.430 | 0.407 |

- **Gain:** **+0.023**, just above the 0.02 margin.
- **Test:** one-sided Wilcoxon **p = 0.0468**, just below alpha 0.05.
- **Systems:** 14 wins, 4 losses, 2 exact ties. Under the default rule (scipy `wilcox`) the ties are dropped.
- **Under the formal rule, HR is supported.**

**This is a fragile pass, and it must be presented as such:**
- **Bootstrap CI:** the 95% system-cluster bootstrap CI of the gain is **[−0.008, +0.053]**, which **includes 0**. The
  pre-registration listed the CI as reported, not as part of the success rule. Read as an interval, the result is
  compatible with no effect.
- **Effect size:** d_z = +0.32 is about half the decisive experiment's 0.59. By the power note, this replication was
  under-powered for an effect this size (power ≈ 0.4).
- **Sensitivity to the test choice:**
  - p moves with the zero-handling convention: Pratt and zsplit give 0.035.
  - A paired t-test gives p = 0.082. This is not pre-registered and is shown only as a sensitivity check.
- **Margin:** the gain clears the 0.02 margin by only 0.003.
- **Decisive experiment:** the earlier 9-system decisive experiment failed the same rule (p = 0.0645).

**Honest summary:** adding a PU random forest to the pooled template prior gives a small positive recall@100 gain (about
+0.02 to +0.04). It is consistent in direction (positive in 2 of 2 studies, 20 of 27 non-tied systems across the two studies) but borderline in
significance. The gain is larger and robust deeper in the ranking (recall@500 and recall@1000, exploratory). The template
prior remains the dominant signal.

## Systems and leakage audit
- **Selection:** the rule reproduced the earlier 18 systems in order, and 20 new systems were eligible (no shortfall):
  B-H-Li-N, Fe-K-O-Se, Cs-O-Te-V, Fe-O-Si-Ti, N-O-U-V, O-P-Rb-W, Ca-Cu-O-V, Al-Mo-O-V, Na-O-S-Ti, As-Ca-Mn-O, Ca-Cr-O-P,
  Co-Nb-O-P, La-Ni-O-P, Al-Er-Ge-Ni, Cs-O-S-Sb, O-P-Pb-U, Ba-O-Sb-Ti, K-O-Te-U, Cs-Fe-Mo-O, Cu-La-Mo-O.
- **Overlap:** 1–39 of each system's 54–62 observed formulas are shared with other systems (`results/overlap_audit.csv`).
- **Template pool:** the 37 other systems. Test-identical formulas were removed.
- **Strict sensitivity:** with all source formulas inside the target's element sub-space removed, the gain is +0.031
  [+0.002, +0.061], two-sided p = 0.049. This CI excludes 0.
- **Element attributes:** none are missing for any of the elements used.

## Primary (confirmatory)
BLEND 0.430 vs TPOOL 0.407: diff +0.023 [-0.008, +0.053], d_z +0.32, W/L 14/4, p (greater) 0.0468; **success = True**

## Secondary (exploratory)
- recall@10: -0.011 [-0.038, +0.013], d_z -0.19, W/L 9/11, p (two-sided) 0.6274
- recall@50: -0.001 [-0.028, +0.024], d_z -0.02, W/L 12/7, p (two-sided) 0.8092
- recall@500: +0.110 [+0.067, +0.152], d_z +1.10, W/L 18/2, p (two-sided) 0.0001
- recall@1000: +0.083 [+0.050, +0.116], d_z +1.08, W/L 18/2, p (two-sided) 0.0007
- MRR: +0.014 [+0.005, +0.024], d_z +0.66, W/L 15/5, p (two-sided) 0.0073
- strict-leakage recall@100: +0.031 [+0.002, +0.061], d_z +0.46, W/L 14/5, p (two-sided) 0.0486
- BLEND vs RF alone recall@100: +0.292 [+0.228, +0.355], d_z +1.96, W/L 20/0, p (two-sided) 0.0001

Chosen w (100 splits): {0.1: 51, 0.2: 19, 0.3: 14, 0.4: 7, 0.5: 2, 0.6: 3, 0.7: 2, 0.8: 1, 0.9: 1}

## All metrics (mean over systems)
| method                       |   recall@10 |   recall@50 |   recall@100 |   recall@500 |   recall@1000 |   MRR |   median_rank |   precision@100_observed |   enrichment@100 |
|:-----------------------------|------------:|------------:|-------------:|-------------:|--------------:|------:|--------------:|-------------------------:|-----------------:|
| BLEND strict-leakage         |       0.124 |       0.319 |        0.439 |        0.745 |         0.849 | 0.063 |       176.46  |                    0.096 |          181.461 |
| BLEND (RF + pooled template) |       0.123 |       0.315 |        0.43  |        0.754 |         0.852 | 0.063 |       179.295 |                    0.094 |          177.78  |
| TPOOL strict-leakage         |       0.135 |       0.316 |        0.408 |        0.641 |         0.77  | 0.049 |       287.035 |                    0.089 |          168.463 |
| TPOOL (pooled template)      |       0.134 |       0.316 |        0.407 |        0.644 |         0.769 | 0.049 |       290.035 |                    0.089 |          168.264 |
| template target-only         |       0.107 |       0.245 |        0.326 |        0.544 |         0.672 | 0.04  |       518.29  |                    0.071 |          134.888 |
| RF alone                     |       0.035 |       0.097 |        0.138 |        0.346 |         0.528 | 0.018 |      1035.2   |                    0.03  |           56.927 |
| random                       |       0.001 |       0.001 |        0.002 |        0.011 |         0.022 | 0     |     20386.8   |                    0     |            0.743 |

## Per-system recall@100 (mean of 5 splits)
| system      |   BLEND (RF + pooled template) |   TPOOL (pooled template) |   RF alone |   template target-only |   random |   BLEND−TPOOL |
|:------------|-------------------------------:|--------------------------:|-----------:|-----------------------:|---------:|--------------:|
| Al-Er-Ge-Ni |                          0.5   |                     0.5   |      0.064 |                  0.518 |    0.009 |         0     |
| Al-Mo-O-V   |                          0.39  |                     0.381 |      0.381 |                  0.286 |    0     |         0.01  |
| As-Ca-Mn-O  |                          0.609 |                     0.482 |      0.027 |                  0.4   |    0     |         0.127 |
| B-H-Li-N    |                          0.208 |                     0.2   |      0.158 |                  0.225 |    0     |         0.008 |
| Ba-O-Sb-Ti  |                          0.52  |                     0.45  |      0.17  |                  0.42  |    0     |         0.07  |
| Ca-Cr-O-P   |                          0.291 |                     0.427 |      0.064 |                  0.345 |    0.009 |        -0.136 |
| Ca-Cu-O-V   |                          0.409 |                     0.304 |      0.287 |                  0.191 |    0     |         0.104 |
| Co-Nb-O-P   |                          0.486 |                     0.467 |      0.057 |                  0.381 |    0     |         0.019 |
| Cs-Fe-Mo-O  |                          0.389 |                     0.368 |      0.137 |                  0.274 |    0     |         0.021 |
| Cs-O-S-Sb   |                          0.4   |                     0.491 |      0     |                  0.382 |    0     |        -0.091 |
| Cs-O-Te-V   |                          0.383 |                     0.4   |      0.175 |                  0.25  |    0     |        -0.017 |
| Cu-La-Mo-O  |                          0.459 |                     0.424 |      0.094 |                  0.235 |    0     |         0.035 |
| Fe-K-O-Se   |                          0.4   |                     0.375 |      0.033 |                  0.25  |    0     |         0.025 |
| Fe-O-Si-Ti  |                          0.461 |                     0.539 |      0.157 |                  0.461 |    0.009 |        -0.078 |
| K-O-Te-U    |                          0.495 |                     0.419 |      0.095 |                  0.324 |    0     |         0.076 |
| La-Ni-O-P   |                          0.443 |                     0.443 |      0.087 |                  0.383 |    0     |         0     |
| N-O-U-V     |                          0.375 |                     0.342 |      0.317 |                  0.283 |    0     |         0.033 |
| Na-O-S-Ti   |                          0.452 |                     0.383 |      0.122 |                  0.357 |    0     |         0.07  |
| O-P-Pb-U    |                          0.5   |                     0.336 |      0.1   |                  0.282 |    0.009 |         0.164 |
| O-P-Rb-W    |                          0.43  |                     0.41  |      0.23  |                  0.28  |    0     |         0.02  |

## Exploratory: pooled 29 systems (decisive + replication), two-sided
recall@100 diff +0.029 [+0.004, +0.054], d_z +0.41, W/L 20/7, p (two-sided) 0.0288

## Notes
- **Exploratory pooled analysis:** combining the decisive and replication experiments (29 systems, two-sided) gives
  +0.029 [+0.004, +0.054], d_z +0.41, p = 0.029. This analysis is exploratory, not pre-registered as decisive.
- **Chosen blend weight:** small RF weights dominate (w = 0.1 in 51 of 100 splits).
- **Code:** identical to the decisive experiment except for the system lists (`diff` checked).
- **Runtime:** 174 s on 8 CPU cores.
- **Reproduce:** run `select_and_build.py`, then `run_replication.py`, then `analyze.py`.
