# Expt-08 — Strategy evolution: NOT RUN (documented decision)

The assignment makes Expt-08 conditional on Expts 01–06 being stable and reproducible *and* justified.
Decision (2026-10-14, Stage 3): **skipped.**

Reasons, from the Stage-1/2 evidence:
1. The core mechanism that strategy evolution would tune — contradiction-driven specialist learning — showed no
   contradiction-specific benefit (Expt-01: proposed vs high-residual specialist +0.002 [−0.012, +0.016], p=0.90; ablating
   uncertainty, reliability or the validation gate changes nothing) and produced false discoveries in synthetic
   environments with no exception (40%).
2. Evolving meta-strategies over components whose individual effects are null would mostly search noise; with 91
   compounds and ~14-sample inner validation sets, a strategy-level search would overfit the selection procedure.
3. The two clearly active ingredients (charge-balance features, learned element embeddings) are feature choices that
   are better studied directly than through strategy evolution.

Preconditions to revisit: permutation-controlled specialist acceptance with demonstrated low false-discovery rate on
synthetic data; a contradiction component with a positive, significant ablation; a larger benchmark (≥ several hundred
compounds or multiple systems). No code or results are produced here on purpose.
