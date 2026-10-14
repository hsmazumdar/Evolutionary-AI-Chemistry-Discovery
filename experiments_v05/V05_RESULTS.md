# V05 Results
Concept and direction: Himanshu Mazumdar, R&D Centre, Dharmsinh Desai University · Code developed with AI assistance.

All numbers are means over systems (each system = mean over its splits) unless stated. "Observed" = an ICSD-linked
Materials Project entry exists (experimental structure). DFT energies are computed, never measured.
Full statistics: `V05_STATISTICAL_ANALYSIS.md`. Figures: `figures/`.

## Headline
**None of the three pre-registered hypotheses is supported.** The proposed evolutionary hypothesis-population ranker
(EHP) is far behind the strongest PU baseline: recall@100 0.036 vs 0.215, a difference of −0.179 (95% CI −0.215 to −0.143), 0 of 9 systems won.
The best ranker is a simple stoichiometry-template frequency prior. Following protocol §8, V05 is framed as a
**negative / benchmark study**.

## H1 Discovery, Protocol A (random 60/40, 5 splits, 9 systems; ~41,300 candidates per system)
| method | R@10 | R@50 | R@100 | R@500 | R@1000 | MRR | median rank | obs. precision@100 | enrichment@100 |
|---|---|---|---|---|---|---|---|---|---|
| template_prior | 0.070 | 0.153 | **0.229** | 0.355 | 0.563 | 0.029 | 912 | 0.067 | 94.6 |
| strongest PU baseline (inner-selected) | 0.057 | 0.135 | 0.215 | 0.371 | 0.554 | 0.025 | 904 | 0.063 | 88.7 |
| charge_balance (prior) | 0.057 | 0.090 | 0.122 | 0.271 | 0.312 | 0.030 | 7,794 | 0.036 | 50.3 |
| PU_RF_ox (prior) | 0.030 | 0.070 | 0.112 | 0.328 | 0.511 | 0.016 | 1,017 | 0.034 | 46.4 |
| PU_RF_leaf3 | 0.027 | 0.074 | 0.103 | 0.244 | 0.376 | 0.015 | 1,850 | 0.032 | 42.4 |
| PU_RF_embedding | 0.028 | 0.071 | 0.096 | 0.276 | 0.422 | 0.016 | 1,504 | 0.029 | 39.6 |
| PU_RF_leaf1 (primitive) | 0.027 | 0.063 | 0.089 | 0.253 | 0.391 | 0.014 | 1,663 | 0.027 | 36.7 |
| PU_GB | 0.022 | 0.060 | 0.088 | 0.242 | 0.394 | 0.009 | 1,722 | 0.027 | 36.4 |
| PU_logistic | 0.005 | 0.022 | 0.059 | 0.257 | 0.367 | 0.003 | 1,853 | 0.019 | 24.5 |
| nearest_positive | 0.010 | 0.033 | 0.042 | 0.219 | 0.360 | 0.005 | 2,131 | 0.013 | 17.3 |
| **EHP (proposed)** | 0.002 | 0.017 | 0.036 | 0.226 | 0.332 | 0.002 | 2,454 | 0.011 | 14.9 |
| random | 0.001 | 0.003 | 0.003 | 0.017 | 0.035 | 0.000 | 20,130 | 0.001 | 1.4 |

Inner selection picked template_prior in 35 of 45 splits (PU_RF_ox in 7).

## H1, Protocol B (held-out stoichiometry families)
EHP 0.039; PU_RF_ox 0.115; charge balance 0.128; template prior 0.000 (cannot score unseen families); the inner-selected
"strongest" baseline 0.022. Its inner validation is *not* family-grouped, so it picked template_prior in 38 of 45 folds.
This is a flaw in the nested-validation design (see Negative Results). So the nominal EHP > selected-baseline difference
here (+0.017, p=0.10) is an artefact, not evidence for EHP. EHP is below every learned PU baseline in Protocol B.

## H2 Transfer (leave-one-system-out; source positives with a target-test formula removed)
| method | R@100 | R@500 | R@1000 | MRR |
|---|---|---|---|---|
| PU_RF target-only | 0.089 | 0.253 | 0.391 | 0.014 |
| PU_RF pooled (source+target) | 0.086 | 0.272 | 0.440 | 0.014 |
| PU_RF source-only zero-shot | 0.077 | 0.236 | 0.333 | 0.011 |
| EHP target-only | 0.036 | 0.226 | 0.332 | 0.002 |
| EHP pooled | 0.022 | 0.235 | 0.354 | 0.002 |
| template prior target-only | 0.229 | 0.355 | 0.563 | 0.029 |
| template prior pooled (not pre-registered as H2 model) | **0.307** | 0.509 | 0.623 | 0.037 |
Transfer of learned models does not help recall@100 (it helps slightly at R@1000 for PU_RF). Pooling stoichiometry
templates across systems does help: +0.078 [+0.054, +0.104], 9 of 9 systems. This is an exploratory finding.

## H3 Cumulative memory (3 stream orders, recall@100 on each new system)
| arm | R@100 new | R@500 new | mean forgetting (R@100 drop) |
|---|---|---|---|
| sequential_finetune | 0.051 | 0.239 | +0.004 |
| scratch | 0.045 | 0.244 | +0.020 |
| V04_archive | 0.045 | 0.278 | −0.026 |
| **proposed_versioned_memory** | 0.042 | 0.268 | +0.000 |
| replay | 0.039 | 0.265 | −0.040 |
| full_data_retrain | 0.022 | 0.264 | +0.005 |
The proposed memory meets the forgetting criterion (≤0.02) but does not beat the controls on new systems. All arms sit
near EHP's low level.

## Exploratory
- **EHP ablations (Protocol A, R@100):** top-1 hypothesis 0.029; as H1 0.036; uniform weights 0.036; 3× generations 0.040;
  3× bags 0.052. More compute helps a little but stays far below 0.2. **PU_RF + template rank-mean: 0.256 (best overall)**;
  EHP + template 0.231; template alone 0.229. The template prior carries almost all of the signal.
- **Contradiction diagnostics:** 11 of 670 observed formulas (1.6%) are ranked below the median unlabelled candidate when
  cross-fitted, against a null of 48–50% for random pseudo-positives (permutation p = 0.048 per system, the floor for 20
  permutations). 5 of the 11 are in H-N-O-S (molecular/acid chemistry, e.g. HNO3, HSNO4). There is no consistent
  association with DFT E_hull, polymorph count or ICSD count (Spearman between −0.47 and +0.38, signs vary by system).
  Diagnostic value is unproven.
- **Phase 8, DFT formation-energy regression (leave-one-system-out, MAE eV/atom):** RF 0.418 [0.358, 0.488]; Roost
  (matscholar embedding, external prior) 0.423 [0.281, 0.577]; GBR 0.433; PySR 0.484; V03 GP 0.501 [0.441, 0.568];
  ridge 0.595; mean 0.860. RF and GBR beat the V03 GP (two-sided p = 0.020); PySR and Roost do not differ significantly from it.

## Phase 10 industrial case: Na-Fe-P-O (Na-ion cathode family)
Fe-Na-O-P candidates were ranked by the rank-mean of template prior and PU_RF (exploratory best), trained on all 82 observed
formulas. Top quaternary candidates (`results/industrial/quaternary_top50.csv`): Fe3Na3O12P2, Fe3Na4O16P3, FeNaO5P,
Fe2Na3O12P4, Fe4Na3O16P3, FeNa2O7P, ... **None of the top 25 has a Materials Project entry. All are computational
hypotheses only, with no DFT or experimental support in this dataset.** Many fail the V03 charge-balance feature (imbalance ≠ 0).
The method's best measured hit rate (observed-label precision@100 ≈ 0.06–0.07 in Protocol A) means most
top-ranked candidates should be expected to be false. Use: a prioritised list for DFT screening, not a synthesis recommendation.
