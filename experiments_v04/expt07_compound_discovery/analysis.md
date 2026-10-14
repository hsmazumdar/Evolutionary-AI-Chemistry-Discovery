# Expt-07 analysis

Random 60/40 splits (mean of 10; 32.7 hidden compounds in the space; random expectation 0.08 @100, 0.79 @1000):
| method | @10 | @100 | @1000 | median rank |
|---|---|---|---|---|
| random | 0.0 | 0.0 | 0.0 | 17015 |
| charge balance only (prior) | 0.0 | 0.5 | 7.8 | 4880 |
| V03 analogy + GP_ox hull (recomputed; V03 reported 2.0 @100) | 0.8 | 1.9 | 7.8 | 18148 |
| PU-RF, element attributes only | 0.1 | 1.6 | 13.7 | 1549 |
| PU-RF + energy above training hull | 0.1 | 2.4 | **16.2** | 1110 |
| PU-RF + ox. features (prior) | 0.6 | 3.3 | 15.9 | **1072** |
| PU-RF(ox) within analogy templates | **1.2** | **5.9** | 13.6 | 1205 |

Group-held-out folds (16.2 hidden): PU-RF+ox 1.6 @100, 8.2 @1000, median rank 909, vs V03 analogy 0.0 / 0.4 / 27701.

Paired Wilcoxon over 10 splits: PU-RF (attributes only) vs V03: +5.9 hits@1000 [3.7, 8.3], p=0.002; median rank −16,600,
p=0.002; hits@100 n.s. (+0.3 ... −0.3). After Holm correction over all 36 tests the smallest adjusted p is 0.07 (10
pairs give a minimum Wilcoxon p of 0.002), so individual comparisons are not significant at 0.05 after correction even
where every split agrees.

## Interpretation
- A PU formulation is a clearly better *ranking* principle than predicted energy above a 55-compound hull: median rank
  improves ~15×, and the top-1000 contains ~half of the hidden compounds (vs ~quarter for V03).
- Precision at the very top remains low: best top-100 finds 5.9/32.7 (18%), ~75× random, and that variant relies on
  oxidation-state priors and V03 analogy templates. Without chemical priors: 1.6 @100.
- PU-RF does not use evolved rules at all; the gain is a discovery-protocol improvement, not evidence for the
  evolutionary knowledge architecture.
**Verdict H7: improved discovery protocol (PU) — supported descriptively; not attributable to evolutionary learning.**
