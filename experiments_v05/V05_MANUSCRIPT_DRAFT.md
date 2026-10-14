# Do evolved symbolic hypotheses help discover inorganic compounds? A pre-registered multi-system negative result
**Draft. Every claim is tied to V05 results; no claim goes beyond them.**
Concept and direction: Himanshu Mazumdar, R&D Centre, Dharmsinh Desai University · Code developed with AI assistance.

## Abstract
We tested, under a pre-registered protocol, whether a population of evolved symbolic scoring hypotheses (EHP), built only
from primitive element-attribute features, can prioritise experimentally observed compositions among ~41,000 candidate
formulas per chemical system, in a positive-unlabelled setting. We used nine carbon-free quaternary systems (756 ICSD-linked
formulas, Materials Project snapshot 2025-09-25). EHP reached a mean recall@100 of 0.036, against 0.215 for the strongest
nested-selected PU baseline (difference −0.179, 95% cluster-bootstrap CI −0.215 to −0.143; EHP lost on 9 of 9 systems). Neither
cross-system transfer (H2) nor a versioned hypothesis memory (H3) improved recall@100. A simple stoichiometric-template
frequency prior was the strongest single ranker (0.229), and pooling templates across systems raised it to 0.307
(exploratory). We release the benchmark, code and all negative results.

## 1. Introduction
Composition-level discovery engines are often reported on one system with post-hoc choices. Our V04 study (single system,
Fe-Na-O-P) motivated three hypotheses, which we registered before running experiments (H1 discovery, H2 transfer, H3 memory).

## 2. Data
Nine systems were chosen by a fixed greedy rule (≤2 shared elements). "Observed" means an ICSD-linked MP entry exists. DFT
formation energies (computed) and measured enthalpies (Kingsbury/matminer; 71 formulas; MAE vs DFT 0.088 eV/atom) are kept
as separate labels. Polymorphs are tracked per reduced formula. No publication dates are available, so there is no temporal split.

## 3. Methods
EHP: V03 genetic-programming trees fitted as class-balanced least-squares PU discriminants; the confidence of each tree is its
inner-validation AUC − 0.5; the final score is a confidence-weighted rank ensemble. Baselines: random, charge balance, template prior,
PU random forests (primitive, oxidation, embedding features), PU gradient boosting, PU logistic, nearest positive.
Protocols A (random), B (family hold-out), C (leave-one-system-out) and D (stream). Statistics: system as unit, Wilcoxon,
Holm, cluster bootstrap.

## 4. Results
See V05_RESULTS.md, Tables 1–4, and V05_STATISTICAL_ANALYSIS.md. H1, H2 and H3 are all unsupported (Holm p ≥ 0.71 for each).
On a DFT-Ef regression proxy, the V03 GP (MAE 0.501 eV/atom) trails RF (0.418) and does not significantly differ from PySR (0.484)
or Roost (0.423).

## 5. Discussion
Within this candidate space, the ranking signal is dominated by which stoichiometric templates recur among known compounds.
Symbolic attribute expressions capture little beyond that. Limitations: the observed-label precision is a lower bound;
the space caps at 30 atoms per formula; there are 9 systems; nested selection was not family-grouped in Protocol B; and there was no temporal validation.
The Na-Fe-P-O shortlist is offered only as computational hypotheses for DFT screening.

## 6. Data and code availability
Branch `research-v05`. Run `experiments_v05/scripts/regenerate_all.sh`. Lockfiles and CI are included.
