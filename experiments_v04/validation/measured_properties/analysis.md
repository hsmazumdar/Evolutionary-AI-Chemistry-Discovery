# Measured-property validation — analysis

**DFT vs measured inside Fe-Na-O-P (13 formulas):** MP DFT Ef vs measured ΔHf MAE = 0.080 eV/atom (largest: FeO 0.34,
P2O5 0.22). Models trained on the 91 DFT values score 0.180 (ridge) and 0.295 (GP) against measured values — i.e.
model error is 2–4× the DFT–experiment gap, so our DFT-trained conclusions are limited by model error, not by the DFT target.

**Measured formation enthalpy, chemical-system-grouped 5-fold CV (2010 formulas):** RF 0.192 [0.182, 0.200],
GP 0.323 [0.300, 0.345], ridge 0.316 [0.308, 0.323], mean 0.770. GP − RF +0.131 (5/5 folds worse).
**Measured band gap (4492):** RF 0.543, ridge 0.909, GP 0.942, mean 1.200.

## Interpretation
On large measured datasets the evolved symbolic regressor performs like a linear model and is clearly worse than a
random forest. These numbers are on measured targets and must not be pooled with the DFT results.
