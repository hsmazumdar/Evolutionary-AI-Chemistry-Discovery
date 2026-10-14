# Expt-06 (Stage 1 core) — Baselines and ablations

Identical splits: 10 random 60/40, family-held-out, 5 V04 group folds, quaternary-held-out (17). Stochastic models: seeds 0–2.
Hyperparameters by 5-fold inner CV on the training partition only (GridSearchCV / RidgeCV / LassoCV).
Models: mean, ridge, sparse Lasso on degree-2 expanded features (SISSO/PySR-like sparse surrogate), random forest,
gradient boosting, MLP (32-32), V03 GP (pop 300, 40 gens), proposed two-population (Expt-01 config).
**Not run:** PySR (needs a Julia runtime, not available) and Roost (needs PyTorch + roost; not installed; also expected to
be data-starved with 55 training formulas). Documented as gaps, not silently dropped.
Ablations of Stage-1 components come from the same Expt-01 runs: `ablations_from_expt01.csv`.
