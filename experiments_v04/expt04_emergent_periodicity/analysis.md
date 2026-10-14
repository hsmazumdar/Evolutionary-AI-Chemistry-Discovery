# Expt-04 analysis

**Robustness.** Full data ARI 0.528 (null 95th pct 0.029). 80% subsamples: ARI 0.500 ± 0.034 (min 0.433), nearest
neighbour in same group 0.50 ± 0.03. Dimension: 4 → 0.36, 8 → 0.49, 12 → 0.53, 24 → 0.55. The emergent grouping is
stable and far above chance.

**Downstream on Fe-Na-O-P (DFT Ef MAE, 16 splits, 95% CI):**
| features | GP | ridge |
|---|---|---|
| base only | 0.320 [0.298, 0.345] | 0.205 [0.183, 0.228] |
| + learned embedding | **0.210 [0.191, 0.231]** | 0.208 [0.186, 0.234] |
| + random Gaussian embedding | 0.231 [0.208, 0.257] | 0.209 |
| + element-shuffled embedding | 0.271 [0.251, 0.293] | 0.210 |

GP: learned − base −0.110 (Holm p=0.0003); learned − shuffled −0.061 (Holm p=0.0015); learned − random −0.021
(p=0.029, Holm 0.23, n.s.). Ridge: no differences.

**Transfer (ridge, 7 targets):** zero-shot learned − none −0.22 (p=0.006, Holm 0.057), learned − random −1.59
(Holm p<1e-4); pooled 10-shot: no significant differences.

## Interpretation
- The learned embedding gives the GP its largest single improvement in V04 (0.320 → 0.210, now on par with ridge),
  and beats an element-shuffled embedding, so *which* element gets which vector matters.
- But a random embedding recovers most of the gain (0.231), so much of the effect is extra element-identity capacity
  for the GP, not periodic-table structure per se. Ridge gains nothing.
- Periodicity itself is robust; its downstream value is real but modest and model-dependent.
**Verdict H4: periodicity robust (supported); downstream benefit beyond capacity effects weak/not significant.**
