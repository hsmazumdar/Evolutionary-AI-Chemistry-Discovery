# Expt-01 analysis (DFT formation energy, eV/atom)

Mean test MAE [95% bootstrap CI over splits]:

| method | random 60/40 (10 splits) | group held-out (6) | exceptional (rand) | ordinary (rand) |
|---|---|---|---|---|
| ordinary GP (40 g) | 0.310 [0.290, 0.332] | 0.328 [0.286, 0.370] | 0.487 | 0.251 |
| GP + extra generations | 0.304 [0.284, 0.325] | 0.335 [0.285, 0.381] | 0.488 | 0.242 |
| V03 contradiction weighting | 0.302 [0.281, 0.327] | 0.306 [0.271, 0.336] | 0.473 | 0.245 |
| specialist, random samples | 0.331 [0.293, 0.373] | 0.296 [0.269, 0.324] | 0.469 | 0.285 |
| specialist, high-residual samples | 0.287 [0.278, 0.298] | 0.278 [0.247, 0.310] | 0.447 | 0.234 |
| **proposed two-population** | 0.288 [0.267, 0.307] | 0.282 [0.256, 0.302] | 0.450 | 0.233 |
| **GP + charge-balance features (60 g)** | **0.229 [0.209, 0.252]** | 0.302 [0.239, 0.369] | **0.319** | **0.199** |

Paired tests, all 80 runs (proposed − control; Holm-adjusted within metric):
- vs ordinary GP: −0.031 [−0.050, −0.013], p=0.0004, d_z=−0.36, Holm p=0.004. Split-level: 13/16 splits better, p=0.009.
- vs GP + extra generations: −0.030 [−0.051, −0.009], p=0.002, Holm p=0.018.
- vs V03 weighting: −0.018 [−0.038, +0.001], p=0.06 (n.s.).
- vs random-sample specialist: −0.033 [−0.061, −0.009], Holm p=0.046.
- **vs high-residual specialist: +0.002 [−0.012, +0.016], p=0.90 — no difference.**
- **vs GP with the same charge-balance features: +0.029 [+0.005, +0.052], p=0.002 — proposed is WORSE.**
- Ablations: removing uncertainty (Δ −0.0004), reliability (+0.0005) or the validation gate (−0.0007) changes nothing;
  removing the missing-variable search costs 0.020 eV/atom (p=0.0004).

Other measurements: specialists accepted in 78% (random) / 83% (group) of runs; specialist size 7.5 nodes mean; total model
16–17 nodes vs 10–11 for plain GP. Applicability-domain precision for exceptional test items 0.37 (base rate 0.25),
recall 0.43. On the training contradictions themselves error falls 0.63 → 0.33 eV/atom, far more than on held-out
exceptions (0.487 → 0.450).

## Interpretation
1. The two-population structure gives a modest real out-of-sample gain over plain GP and over extra generations, on
   both exceptional and ordinary held-out items.
2. **The gain is not attributable to contradiction-specific information.** Selecting by plain residual gives the same
   result; calibrated uncertainty and reliability add nothing measurable. Random selection is worse, so *some* residual
   focusing matters.
3. **Most of the gain comes from the missing-variable search, i.e. from injecting tabulated oxidation-state (charge
   balance) features — chemical prior knowledge.** A plain GP given those features globally is better still. The
   specialist/domain mechanism is therefore an inferior way of using that variable.
4. Improvement concentrates on the training contradictions (overfitting signature).

**Verdict: hypothesis H1 (contradictions → better generalising specialists) NOT supported** in this setting. Limitations:
91 compounds, DFT target, small inner-validation sets (~14) make acceptance noisy; one specialist per run.
