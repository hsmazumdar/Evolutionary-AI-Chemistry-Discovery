# Decisive experiment: results
Concept and direction: Himanshu Mazumdar, R&D Centre, Dharmsinh Desai University · Code developed with AI assistance.
Pre-registration: `PREREGISTRATION.md`, commit e799bda (2026-10-14 12:22 IST), made before any data was built or run.

## Verdict (confirmatory)
**HD is NOT supported under the pre-registered criterion.** The blend of PU random forest and the pooled template prior scores
recall@100 = 0.379, against 0.337 for the pooled template prior alone. The difference is **+0.042**, 95% system-cluster
bootstrap CI [−0.002, +0.085], with d_z = +0.59 and 6 wins / 3 losses over 9 systems. The one-sided Wilcoxon gives
**p = 0.0645, which is above alpha = 0.05**. The gain does meet the ≥ 0.02 margin, but success needed both conditions, so
the pre-registered outcome is failure. The direction is positive and the CI only just reaches 0. This is weak, inconclusive
evidence that the RF adds something, not a demonstration. Per the protocol, the work goes forward as a benchmark /
negative-result study.

## Systems and leakage audit
The selection rule reproduced the V05 nine exactly, and 9 fresh systems were eligible (no shortfall): Mn-Na-O-V, As-O-Sr-V,
Ba-Mn-O-Si, Cl-O-Pb-V, Cu-O-P-S, Li-O-Si-V, O-Rb-Se-V, Al-Ba-Ge-O, Cl-Hg-N-O. Sub-system overlap is substantial:
8–34 of each system's 63–69 observed multi-element formulas (mostly binary/ternary sub-system compounds) also occur in other
systems (`results/overlap_audit.csv`). Source formulas identical to a target test formula were removed as pre-registered. A stricter
sensitivity analysis removed every source formula inside the target's element sub-space; it gave the same conclusion
(+0.053 [+0.007, +0.097], two-sided p = 0.074). The dataset has its own SHA-256 manifest (`data/MANIFEST.json`).
Measured-enthalpy labels were not built for the fresh systems because this experiment does not use them.


## Exploratory reading (not confirmatory, uncorrected)
- The blend's advantage grows deeper in the ranking: recall@1000 +0.081 (8 of 9 systems, p = 0.008) and MRR +0.016. At the very top
  the blend is slightly worse: recall@10 −0.019.
- RF alone is weak (0.155). Pooled templates beat target-only templates (0.337 vs 0.303), which replicates the V05 exploratory finding on
  fresh systems.
- Inner validation mostly chose small RF weights (w = 0.1 in 20 of 45 splits).
- n = 9 means the smallest attainable one-sided p is 0.002. With the observed d_z ≈ 0.6, power is roughly 50%, so a replication with
  more systems would be needed to resolve this.

Runtime: 82 s on 8 CPU cores. Reproduce with `select_and_build.py`, then `run_decisive.py`, then `analyze.py`.
