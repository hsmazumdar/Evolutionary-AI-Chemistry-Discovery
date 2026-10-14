# Replication: pre-registration (committed BEFORE system selection, data building or any run)
Concept and direction: Himanshu Mazumdar, R&D Centre, Dharmsinh Desai University · Code developed with AI assistance.
PI-approved on 2026-10-14 after the decisive experiment (`decisive_rf_template/`, +0.042 [−0.002, +0.085], p = 0.0645, criterion not met).

## Hypothesis (one confirmatory test, identical to the decisive experiment)
**HR:** On new fresh systems, `BLEND` (PU random forest + pooled template prior) has higher recall@100 than `TPOOL` (pooled template prior alone).

## Systems
- **Rule:** the V05 rule, continued. Take 4-element, carbon-free systems from `feasibility_ranking_all.csv` in descending
  `n_expt_formulas_complete_props` order (ties alphabetical). Accept a system greedily if it shares ≤ 2 elements with every
  system accepted so far, starting from Fe-Na-O-P.
- **Excluded as targets:** the first 18 accepted systems (9 V05 + 9 decisive). They still count as accepted for the overlap rule.
- **Count:** the next **20** accepted systems are the targets.
- **Checks:** the script must reproduce the 18 earlier systems in order, otherwise the experiment stops. If fewer than 20 are
  eligible, all eligible systems are used and the shortfall is reported.

## Leakage
- **Template pool:** for target t, the pool is the observed multi-element formulas of all other 37 systems.
- **Removal (pre-registered):** source formulas identical (same reduced formula) to any of t's held-out test formulas are removed.
- **Strict sensitivity:** additionally remove every source formula lying within t's element sub-space.
- **Audit:** per system, count the observed formulas shared with earlier systems and with the other replication systems.

## Protocol (frozen, identical to the decisive experiment's code)
- Protocol A: 5 random 60/40 splits (seeds 0–4), with frozen test sets. The unit is the system (mean over its 5 splits).
- RF = PU_RF_leaf1: primitive features, 10 bags, unlabelled ratio 5.
- TPOOL = template prior using pooled counts.
- BLEND = w·rank(RF) + (1−w)·rank(TPOOL), with average ranks normalised to [0, 1] and w ∈ {0.1, …, 0.9}.
- The blend weight w is chosen **only on inner validation**: 3 folds of the outer-training positives, grouped by
  stoichiometry family (`formula_anonymous`). Ties go to the smaller w.
- Reference arms: random, RF alone, template target-only.

## Decisive test
- **Metric:** recall@100.
- **Test:** paired one-sided Wilcoxon signed-rank (BLEND > TPOOL) across systems, alpha = 0.05.
- **Success:** p < 0.05 **and** mean gain ≥ 0.02.
- **Confidence interval:** 95% system-cluster bootstrap percentile CI (10,000 resamples, seed 0); d_z is also reported.
- Everything else is exploratory (two-sided, uncorrected): recall@10/50/500/1000, MRR, the strict-leakage variant, the chosen w,
  and a pooled 29-system analysis (decisive + replication).

## Power note
The decisive experiment gave d_z ≈ 0.59. For n = 20 and one-sided alpha = 0.05, the paired t-test power at d_z = 0.59 is
≈ 0.82, so Wilcoxon power is ≈ 0.78–0.80 (ARE ≈ 0.95). The decisive estimate is noisy, and the true effect may be smaller.
At d_z = 0.4, power is ≈ 0.50. A failure here would therefore argue against an effect of the size seen before, but would not
exclude a small one.
