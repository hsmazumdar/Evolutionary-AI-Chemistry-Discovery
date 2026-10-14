# Decisive experiment: pre-registration (written and committed BEFORE data building or any run)
Concept and direction: Himanshu Mazumdar, R&D Centre, Dharmsinh Desai University · Code developed with AI assistance.
Approved by the PI on 2026-10-14 as the "smallest decisive next experiment" named in V05_Q1_READINESS_AUDIT.md.

## Hypothesis (one confirmatory test)
**HD:** On fresh systems, the blend of PU random forest and the pooled template prior (`BLEND`) achieves higher recall@100
than the pooled template prior alone (`TPOOL`).

## Systems (rule fixed in advance = V05 rule, continued)
The V05 rule is: from `feasibility_ranking_all.csv`, take 4-element carbon-free systems in descending
`n_expt_formulas_complete_props` order (ties alphabetical), and accept a system greedily if it shares ≤ 2 elements with
every accepted system, starting from Fe-Na-O-P. Here the rule continues past the 9 V05 systems, which stay in the accepted
set for the overlap check but are excluded as targets, until 9 fresh systems are accepted. The selection script must reproduce
the V05 nine exactly; otherwise the experiment stops. If fewer than 9 exist, all that exist are used and the shortfall is reported.

## Data and leakage audit
- Same MP snapshot (2025-09-25) and the same builder logic as V05. "Observed" means an ICSD-linked entry exists.
- Audit to report: the number of observed fresh-system formulas whose reduced formula also occurs in a V05 system or in another
  fresh system. These are shared sub-system formulas such as binary oxides.
- **Pooled templates for target t** come from the observed multi-element formulas of all other 17 systems (9 V05 + 8 fresh).
  Any source formula whose reduced formula equals one of t's held-out **test** formulas is removed first.
  Sensitivity analysis (not confirmatory): a stricter variant that removes every source formula lying inside t's element
  sub-space.

## Protocol
- Outer: Protocol A, 5 random 60/40 splits per system (seeds 0–4), with the test set frozen. Unit = system (mean of 5 splits).
- `RF` = V05 PU_RF_leaf1: primitive features, 100 trees, min_samples_leaf 1, 10 PU bags, unlabelled ratio 5.
- `TPOOL` = V05 template prior with the pooled counts (target training positives + source).
- `BLEND` = w · rank(RF) + (1 − w) · rank(TPOOL), where rank is the average rank normalised to [0, 1].
  w ∈ {0.1, 0.2, …, 0.9} is **chosen on inner validation only**. Inner validation uses 3 folds of the outer training positives,
  **grouped by stoichiometry family** (`formula_anonymous`). In each inner fold, RF and TPOOL are refit on the inner-train
  positives, and recall@100 is computed on the inner-held positives with the inner-train ones excluded. The w with the highest
  mean inner recall@100 is chosen; ties go to the smaller w. That w is then refit on all outer training positives and scored
  once on the test set.
- Reference arms (descriptive, not tested): random, RF alone, template prior target-only.

## Statistics and decision
- Primary metric: recall@100.
- Test: paired one-sided Wilcoxon signed-rank (BLEND > TPOOL) across the 9 systems, alpha = 0.05. This is the only
  confirmatory test, so no multiplicity correction is applied.
- Effect: mean paired difference with a 95% system-cluster bootstrap percentile CI (10,000 resamples, seed 0), plus Cohen's d_z.
- **Success = p < 0.05 AND mean gain ≥ 0.02.** Anything else counts as failure: no learned component adds value beyond template
  counting, and the work goes forward as a benchmark / negative-result study.
- Secondary (exploratory, two-sided, uncorrected): recall@10/50/500/1000, MRR, median rank, the stricter-leakage variant, and
  the distribution of chosen w.
