# Expt-03 analysis (target MAE, eV/atom, DFT; mean over targets of each class)

| class / shots | GP src refit | GP src+offset | GP target-only | ridge target-only | ridge pooled | RF src zero-shot | GP src zero-shot |
|---|---|---|---|---|---|---|---|
| similar 5 | 0.404 | 0.353 | 11.8 (unstable) | 0.600 | 0.401 | **0.318** | 0.387 |
| similar 10 | 0.354 | 0.343 | 0.482 | 0.406 | 0.395 | **0.310** | 0.379 |
| similar 20 | 0.325 | 0.317 | 0.312 | 0.328 | **0.288** | 0.320 | 0.393 |
| dissimilar 5 | 0.771 | 0.774 | 1.106 | 1.384 | 0.834 | **0.732** | 1.038 |
| dissimilar 10 | 0.588 | 0.742 | 0.768 | **0.551** | 0.585 | 0.728 | 1.043 |
| dissimilar 20 | 0.556 | 0.724 | **0.369** | 0.431 | 0.431 | 0.726 | 1.026 |

Paired (target×draw×seed; Holm over 30 tests): refit-source-structure beats target-only GP at 10 shots on similar
targets (−0.128, Holm p=0.024) and target-only ridge at 5 shots (−0.196, Holm p<1e-4). At 20 shots on dissimilar targets
it is *worse* than target-only GP (+0.188, Holm p<1e-4) and target-only ridge (+0.125, Holm p=0.012).

## Interpretation
- Transfer works as a **low-data prior**: with 5–10 labels, reusing an evolved structure is much more stable than
  evolving from scratch (scratch GP on 5 points can extrapolate catastrophically).
- The benefit is larger and lasts longer for similar chemistry, and reverses for dissimilar chemistry by 20 labels —
  the expected pattern for a genuine but narrow prior.
- A random forest trained on Fe-Na-O-P is as good or better zero-shot on similar systems, so the transferable content
  is not specific to evolved symbolic rules.
**Verdict H3: partially supported (low-shot, similar systems), not as a symbolic-rule advantage.**
