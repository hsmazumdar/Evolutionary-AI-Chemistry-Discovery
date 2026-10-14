# Expt-05 analysis (DFT Ef MAE)

Random splits (learning-curve mean MAE / final MAE at 40 labels): random 0.569 / 0.336; uncertainty 0.415 / 0.318;
uncertainty×reliability 0.419 / 0.307; diversity 0.406 / 0.312; **uncertainty+diversity 0.397 / 0.298**.
Group-held-out: random 0.450 / 0.358; diversity **0.384 / 0.308**; uncertainty 0.429 / 0.349; unc×rel 0.510 / 0.354.

Paired vs random (Holm over 16 tests): uncertainty+diversity learning-curve −0.172 (Holm p=0.001) and diversity −0.163
(Holm p=0.048) on random splits; final-MAE differences not significant after correction (best: unc+div −0.038, Holm 0.087).
Random-strategy curve mean is inflated by occasional catastrophic early GP fits (wide CI).

## Interpretation
Focused acquisition mostly helps by avoiding unstable early fits (diversity is the main driver); the reliability term adds
nothing. By 40 labels strategies converge. **Verdict H5: weak support for diversity-driven focusing; no support for
reliability/contradiction-driven focusing.**
