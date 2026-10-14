# M1 — Fair tie-breaking for template rankings (exploratory sensitivity analysis)

Status: **post hoc sensitivity analysis**, conceived after both pre-registered results were known. The pre-registered results
(decisive: FAIL, p = 0.0645; replication: PASS, +0.023, p = 0.0468) are **unchanged** and remain the confirmatory record.

## Why
`template_prior` gives every element assignment of the same anonymous stoichiometry and atom count an identical score, and
`rank_metrics` breaks ties with a stable `argsort`, i.e. by candidate enumeration order. BLEND averages ranks with a continuous RF
score, so part of the BLEND − TPOOL gain could have been "RF breaks TPOOL's ties better than enumeration order".

## What was done
1. `rescore.py` re-ran the frozen job functions (imported unchanged from `run_decisive.py` / `run_replication.py`; same seeds,
   splits, candidate pools, w-selection) and saved, for every test formula and arm, its stable rank, the number of candidates
   scoring strictly higher, and the size of its tie group. Re-run check: all 315 + 700 (system, split, arm) metric rows match
   the archived `metrics.csv` to ≤ 1.1e-16 (`results/rerun_check_*.json`).
2. `analyze_m1.py` re-scored recall@10/50/100/500/1000 three ways: **avgrank** (mean rank of the tie group), **expected**
   (exact expectation under uniform random tie-breaking) and **random** (100 seeds, joint random permutation inside each tie
   group). Same per-system averaging, bootstrap CI (10,000 resamples), Wilcoxon (scipy default zero_method) as pre-registered.
3. One added exploratory control: **TPOOL + RF tie-break only** (TPOOL order kept exactly; RF used only inside TPOOL tie groups).

## Ties are real
Every TPOOL test formula sits in a tie group (median size 21 decisive, 12 replication; mean 227 / 137). BLEND has almost none (4–5% of test formulas tied).

## Key numbers (recall@100, BLEND − TPOOL, per-system paired)
| study | stable (pre-registered rule) | expected under fair ties | random ties, 100 seeds |
|---|---|---|---|
| decisive (9) | +0.042 [−0.002, +0.085], 6/3, p = 0.0645 | +0.043 [−0.002, +0.086], 6/3, p = 0.0645 | +0.043 (seed range +0.041…+0.046), p 0.055–0.088; rule met in 2/100 seeds |
| replication (20) | +0.023 [−0.008, +0.053], 14/4/2, p = 0.0468 | +0.027 [−0.005, +0.057], 14/5/1, p = 0.0418 | +0.027 (+0.024…+0.030), p 0.030–0.060; rule met in 77/100 seeds |
| pooled 29 (two-sided) | +0.029 [+0.004, +0.054], 20/7/2, p = 0.029 | +0.032 [+0.006, +0.057], 20/8/1, p = 0.026 | +0.032 (+0.030…+0.034), p 0.019–0.034 |

Fair ties lower TPOOL slightly (replication 0.407 → 0.403; decisive 0.337 → 0.336) and do not change BLEND. recall@500 and
recall@1000 are unaffected (replication +0.110 and +0.083 under every scoring); recall@10 and recall@50 stay ≈ 0.

**RF as pure tie-breaker** explains only a small part of the gain: TPOOL + RF-tie-break vs TPOOL (fair ties), recall@100
+0.009 [+0.004, +0.014] (replication), +0.003 (decisive), +0.007 (pooled 29). BLEND vs that control: +0.018 replication
(p = 0.16), +0.025 pooled 29 (p = 0.058). So most of BLEND's top-100 gain comes from RF re-ordering *across* template levels, not from tie-breaking.

## Verdict
**The BLEND gain survives fair tie-breaking; the enumeration-order tie rule did not inflate it — it slightly favoured TPOOL.**
The honest description is unchanged and, if anything, marginally stronger: a small, borderline recall@100 increment
(+0.027 replication, +0.032 pooled 29 under fair ties) and a robust recall@500/1000 increment. It remains borderline: under
random tie-breaking the replication's pre-registered rule would have been met in 77% of seeds, the decisive study's in 2%.
Recommended Methods/ESI text: report the tie rule, and this sensitivity table next to the pre-registered numbers.

Files: `rescore.py`, `analyze_m1.py`, `results/per_test_{decisive,replication}.csv.gz`, `results/m1_stats.json`, `results/m1_tables.md`, `results/rerun_check_*.json`.
