# Synthetic validation — analysis (SYNTHETIC; no chemical claim)

Overall (75 paired environment×seed runs): proposed − GP(60 gens) = +0.002 [−0.004, +0.009] (p=0.64); proposed −
high-residual specialist = **+0.009 [+0.004, +0.015], p=0.004** (proposed worse, 19 vs 40 wins).

Selected environments (mean of 5 seeds; test MAE vs noise-free truth / MAE inside D / acceptance / domain precision):
- default (freq 0.15): GP 0.158/0.566; high-residual 0.147/0.372, acc 1.0, prec 0.60; proposed 0.160/0.498, acc 0.8, prec 0.50.
- freq 0.30: GP 0.234; high-residual 0.177 (prec 0.76); proposed 0.220 (prec 0.68).
- noise 0.01: high-residual 0.125 (prec 0.83, used hidden variable x4 in 4/5 seeds); proposed 0.150.
- **no exceptions (freq 0): both specialist methods accepted a spurious specialist in 2/5 seeds (false discovery 0.4)
  and were worse than plain GP (0.062 vs 0.037).**
- corruption only (freq 0, 15% corrupted): false discovery 0.4–0.6; contradiction sets were 88–93% corrupted points.
- corruption 15% with exceptions: contradiction sets contained 61% (proposed) vs 83% (high-residual) corrupted points —
  the reliability term does help separate measurement errors from reproducible exceptions — but this did not translate
  into lower test error (0.179 vs 0.180).
- domain overlap 0.15: domain precision ≤0.39 for all; no gain over GP.

## Interpretation
- The architecture *can* recover a hidden exception domain and the missing variable under low noise and hard boundaries,
  but the plain high-residual specialist does so more reliably than the uncertainty×reliability prioritisation.
- Calibrated uncertainty shrinks priority exactly where exceptions live (archive rules disagree there), which plausibly
  explains why the proposed priority under-selects true exceptions.
- The inner-validation acceptance gate does not prevent false discoveries (rate ~0.2 overall, 0.4 when no exception
  exists). This is a falsification failure that must be fixed (e.g. permutation-based acceptance) before any claim.
- Reliability weighting has a measurable, narrow benefit: rejecting corrupted observations from the contradiction set.
