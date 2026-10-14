## Primary (Holm across 4 tests)
| test | n | mean A | mean B | diff | 95% CI | d_z | W/L | p (1-sided) | p Holm | supported |
|---|---|---|---|---|---|---|---|---|---|---|
| H1: EHP > strongest PU baseline (Protocol A) | 9 | 0.036 | 0.215 | -0.179 | [-0.215, -0.143] | -3.03 | 0/9 | 1.0000 | 1.0000 | no |
| H2a: PU_RF transfer > target-only (Protocol C) | 9 | 0.086 | 0.089 | -0.003 | [-0.017, +0.010] | -0.15 | 4/5 | 0.7148 | 1.0000 | no |
| H2b: EHP transfer > target-only (Protocol C) | 9 | 0.022 | 0.036 | -0.015 | [-0.042, +0.014] | -0.31 | 3/6 | 0.9121 | 1.0000 | no |
| H3: memory > every control (IUT, max p) | 9 | 0.042 | 0.045 | -0.003 | [-0.018, +0.013] | -0.13 | 3/5 | 0.7266 | 1.0000 | no |

## H3 sub-tests
| test | n | mean A | mean B | diff | 95% CI | d_z | W/L | p (1-sided) |
|---|---|---|---|---|---|---|---|---|
| H3 sub: memory > scratch | 9 | 0.042 | 0.045 | -0.003 | [-0.040, +0.036] | -0.04 | 4/3 | 0.4688 |
| H3 sub: memory > sequential_finetune | 9 | 0.042 | 0.051 | -0.010 | [-0.048, +0.024] | -0.17 | 5/4 | 0.5566 |
| H3 sub: memory > replay | 9 | 0.042 | 0.039 | +0.003 | [-0.018, +0.021] | +0.08 | 3/2 | 0.4062 |
| H3 sub: memory > V04_archive | 9 | 0.042 | 0.045 | -0.003 | [-0.018, +0.013] | -0.13 | 3/5 | 0.7266 |
| H3 sub: memory > full_data_retrain | 9 | 0.042 | 0.022 | +0.019 | [-0.002, +0.048] | +0.46 | 6/3 | 0.1055 |

## Forgetting (mean recall@100 drop, new→final)
- scratch: +0.020
- sequential_finetune: +0.004
- replay: -0.040
- V04_archive: -0.026
- full_data_retrain: +0.005
- proposed_versioned_memory: +0.000

## Sensitivity
| test | n | mean A | mean B | diff | 95% CI | d_z | W/L | p (1-sided) |
|---|---|---|---|---|---|---|---|---|
| H1 sensitivity Protocol B | 9 | 0.039 | 0.022 | +0.017 | [-0.010, +0.040] | +0.41 | 7/2 | 0.1016 |
| H1 sensitivity recall@50 | 9 | 0.017 | 0.135 | -0.118 | [-0.141, -0.098] | -3.26 | 0/9 | 1.0000 |
| H1 sensitivity recall@500 | 9 | 0.226 | 0.371 | -0.145 | [-0.210, -0.078] | -1.35 | 1/8 | 0.9980 |
| H1 sensitivity MRR | 9 | 0.002 | 0.025 | -0.023 | [-0.029, -0.018] | -2.42 | 0/9 | 1.0000 |
| H1 sensitivity excl. Fe-Na-O-P | 8 | 0.035 | 0.221 | -0.186 | [-0.224, -0.150] | -3.23 | 0/8 | 1.0000 |
| H1 sensitivity excl. H-containing | 7 | 0.035 | 0.213 | -0.179 | [-0.226, -0.134] | -2.65 | 0/7 | 1.0000 |

## Exploratory
| test | n | mean A | mean B | diff | 95% CI | d_z | W/L | p (1-sided) |
|---|---|---|---|---|---|---|---|---|
| Exploratory: strongest PU baseline > EHP (Protocol A) | 9 | 0.215 | 0.036 | +0.179 | [+0.143, +0.215] | +3.03 | 9/0 | 0.0020 |
| Exploratory (not pre-registered model): template prior pooled > target-only | 9 | 0.307 | 0.229 | +0.078 | [+0.054, +0.104] | +1.93 | 9/0 | 0.0020 |

## Phase 8 regression (DFT Ef, eV/atom, leave-one-system-out; exploratory, two-sided vs V03 GP)
| model | mean MAE | 95% CI | diff vs GP | p | runtime s |
|---|---|---|---|---|---|
| random_forest | 0.418 | [0.358, 0.488] | -0.082 | 0.0195 | 27 |
| Roost (matscholar embedding) | 0.423 | [0.281, 0.577] | -0.078 | 0.2500 | 1476 |
| gradient_boosting | 0.433 | [0.382, 0.495] | -0.068 | 0.0195 | 18 |
| PySR | 0.484 | [0.422, 0.554] | -0.016 | 0.4961 | 325 |
| V03_GP | 0.501 | [0.441, 0.568] | +0.000 | nan | 20 |
| ridge | 0.595 | [0.424, 0.822] | +0.095 | 0.6523 | 0 |
| mean | 0.860 | [0.680, 1.061] | +0.359 | 0.0039 | 0 |
