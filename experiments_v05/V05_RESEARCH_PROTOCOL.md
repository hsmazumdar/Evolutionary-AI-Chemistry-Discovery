# V05 Research Protocol (PRE-REGISTERED)

Registered before any principal V05 experiment was run. The git commit that adds this file (branch `research-v05`,
parent `e2caa6f`) is the timestamp. Any later deviation must be listed in `V05_NEGATIVE_RESULTS.md` § Deviations.
Concept and direction: Himanshu Mazumdar, R&D Centre, Dharmsinh Desai University · Code developed with AI assistance.

## 1. Confirmatory hypotheses
- **H1 (discovery, principal).** For held-out experimentally observed formulas, the evolutionary hypothesis-population
  ranker (EHP) achieves higher recall@100 than the strongest PU baseline, where "strongest" means the baseline with
  the best *inner-validation* recall@100. Unit of analysis: the system (9 systems), using each system's mean over its
  splits.
- **H2 (transfer).** For a held-out system, ranking with knowledge learned on the other 8 systems (plus target training
  positives) achieves higher recall@100 than target-only learning with the same model class (leave-one-system-out).
- **H3 (cumulative memory).** When systems arrive sequentially, the versioned hypothesis memory achieves higher mean
  recall@100 on each new system, without loss on earlier systems (forgetting ≤ 0.02), compared with 5 controls at
  matched budgets: scratch, sequential fine-tune, replay buffer, V04 HypothesisMemory-style archive, full-data retrain.
- **Exploratory only** (no confirmatory claims): redesigned contradiction diagnostics; emergent periodicity / element
  embeddings.

## 2. Data (selection rule fixed in advance)
Source: Materials Project summary snapshot (2025-09-25, CC-BY-4.0, `mp_inorganic_all.csv.gz` in the V03 data folder).
Systems: anchor Fe-Na-O-P (V04 comparability), then 4-element, carbon-free systems in descending order of
`n_expt_formulas_complete_props` in `feasibility_ranking_all.csv` (ties alphabetical), greedily accepted if they share
≤ 2 elements with every system already accepted, until 9 systems. Result of the rule:
Fe-Na-O-P, Ba-O-P-V, K-O-S-V, H-N-O-S, Al-Ca-O-Si, K-Mo-O-P, B-H-Na-O, Ba-Fe-O-S, Mn-O-P-Ti (756 observed formulas).
Units of record: reduced formula (polymorphs tracked: count, ICSD ids, lowest-energy polymorph's DFT energy).
Labels kept distinct: (a) *experimental structure exists* (ICSD-linked MP entry); (b) *DFT formation energy* (computed);
(c) *measured formation enthalpy* (Kingsbury/matminer, only where available, never mixed with b).

## 3. Protocols
- **A** random 60/40 of observed formulas within each system, 5 seeds.
- **B** stoichiometry-family held-out (formula_anonymous), 5 group folds per system.
- **C** leave-one-system-out (H2).
- **D** sequential system stream, 3 fixed random orders (H3).
- **E** temporal (train on earlier publication dates). Requires real ICSD/publication dates; if unavailable in the
  data, E is marked UNAVAILABLE — no proxy dates will be invented.

## 4. Discovery task and metrics
Candidates per system: all reduced formulas A_aB_bC_cD_d, 2–4 elements, a+b+c+d ≤ 30 (V03 space). Positives =
training-split observed formulas; everything else unlabelled (PU). Test = held-out observed formulas in the space.
Metrics: recall@10/50/100/500/1000 (fraction of held-out positives in top k of unseen candidates), observed-label
precision@100 (lower bound on true precision), enrichment@100 = recall@100 / (100/N), median rank, MRR. Primary:
recall@100.

## 5. Methods
- **EHP (proposed):** population of symbolic scoring hypotheses (GP trees over *primitive* features only: element
  attribute statistics; no oxidation states, no charge balance, no templates), fitness = inner-validation
  rank-AUC of held-in positives vs unlabelled, PU-bagged; final score = confidence-weighted ensemble of the archive.
- **Baselines:** random; charge-balance (chemistry prior); stoichiometry-template frequency prior; PU-RF on primitive
  features (V04 best attribute-only); PU-RF + oxidation features; PU-RF + learned element embedding; PU gradient
  boosting; PU logistic; nearest-positive similarity; PySR/Roost if installable (else documented).
- Hyperparameters: chosen by nested inner validation (inner 3-fold on training positives) from small pre-declared grids.
  Tests frozen: test positives never enter any fit or selection.

## 6. Budgets
EHP: population 200 × 30 generations per fit. Memory arms in H3: identical generations per system episode.
All runs on the 8-core box; wall-clock and CPU time reported.

## 7. Statistics
Unit = system (n=9) for H1/H2; system × order for H3 with system-cluster bootstrap. Paired Wilcoxon signed-rank
(one-sided in the hypothesised direction for confirmatory tests, two-sided for others), Cohen's d_z, cluster bootstrap
95% CI (resample systems). Holm correction across H1–H3 primary tests. Success: Holm-adjusted p < 0.05 **and** mean
recall@100 gain ≥ 0.02 absolute. Sensitivity: recall@50/@500, protocol B, excluding Fe-Na-O-P, excluding H-containing systems.

## 8. Stopping rules
If H1 fails, the manuscript must be framed as a negative/benchmark study. No hypothesis is redefined after results.
