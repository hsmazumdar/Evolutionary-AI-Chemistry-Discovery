# Stage 3 go/no-go report (V04) — tag `stage3-checkpoint`

- **Expt-07 (PU discovery):** PU bagging with element attributes only raises hidden compounds in the top 1000 from 7.8
  (V03 best, recomputed) to 13.7 of 32.7 (paired p=0.002 over 10 splits; Holm-adjusted 0.07), median rank 18,148 → 1,549.
  Best top-100: 5.9 (PU + ox. prior + analogy templates). Group-held-out folds show the same ordering.
  Verdict: GO for PU as the discovery protocol; the gain does not come from evolutionary rules.
- **Expt-08 (strategy evolution): NOT RUN.** Preconditions not met (core contradiction mechanism null; false
  discoveries in synthetic tests). See `expt08_strategy_evolution/README.md`.

Overall: the assignment's central hypothesis is not supported by these data; see `reports/research_report_v04.md`.
