# Expt-07 — Hidden-compound discovery, positive-unlabelled protocol

**Question.** Can the system re-find experimentally known Fe-Na-O-P compounds that were hidden from it, among the 41,369
candidate formulas of the V03 space?
**PU protocol.** Training-partition compounds are positives; *all* other candidates are unlabelled (hidden compounds
are among them and never labelled as positive or negative — absence from the database is not evidence of
non-existence). PU bagging: 30 bags × RF(100 trees, min leaf 2) on all positives vs 5× as many random unlabelled
candidates; each candidate scored only by bags that did not train on it. Hyperparameters fixed a priori.
Variants: element-attribute features only; + RF-predicted energy above the training-only hull; + charge-balance
features (oxidation-state prior, flagged); PU(ox) restricted to V03 analogy templates. Baselines: random, charge-balance
only, V03 best (analogy templates ranked by GP_ox + training hull; recomputed). 10 random splits + 5 group folds.
Metrics: hits@k of hidden multi-element compounds in the ranking of unseen candidates, median rank.
