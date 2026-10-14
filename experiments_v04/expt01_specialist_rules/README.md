# Expt-01 — Contradiction-driven specialist rule evolution

**Hypothesis.** Reliable contradictions to a general rule carry information that supports specialist rules with better
*out-of-sample* generalisation.

**Method** (`shared/twopop.py`). Training partition → inner fit (75%) / inner validation (25%).
Population G: V03 GP, pop 200, 40 generations on inner-fit. Archive = 10 best distinct rules; per-sample uncertainty
σ_i = std of archive predictions, calibrated as σ̂_i = sqrt(s0² + (c σ_i)²) with (s0, c) maximising Gaussian likelihood
on inner validation. Contradiction priority p_i = (|r_i| / σ̂_i) × reliability_i, where reliability = 1 − exp(−n_eff/1.5),
n_eff = distinct observed polymorphs + 0.25·log(1 + extra ICSD records) (duplicate records of one structure are not
independent confirmations; dataset already has one row per reduced formula). Top 15% (≥4) = contradiction set C.
Population S: applicability domain = depth-2 decision tree separating C from the rest; S evolves (pop 200, 10 gens on base
features + 10 gens on base + candidate missing variables `charge_balanced`, `charge_imbalance`) on inner-fit samples in the
domain. Combination mode (replace / blend) and feature set chosen on inner validation; specialist **accepted only if it
lowers inner-validation MAE by > 0.005 eV/atom**. Final coefficients re-scaled on the whole training partition.

**Controls (matched budget = 60 generations × pop 200 unless noted):** ordinary GP (40 gens, reference), GP + 20 extra
generations, V03 contradiction weighting (×3), specialist on random samples, specialist on high-residual samples,
**GP 60 gens with the same charge-balance features** (added after the first analysis revealed the confound; kept).
Ablations: no uncertainty, no reliability, no validation gate, no missing-variable search.

**Exceptional vs ordinary test items** are defined independently of every method: top-quartile |residual| of a ridge
reference model fitted on the training partition (evaluation-only label).

Splits: 10 random + family-held-out + 5 group folds = 16; evolutionary seeds 0–4 → 80 runs per method.

Run: `python reproduce.py` (~45 s on 8 cores) or `--quick`.
