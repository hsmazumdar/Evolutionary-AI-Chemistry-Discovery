# M2 — Recall by formula arity (exploratory; data already seen)

Status: exploratory. Uses the per-test-formula ranks of M1 (identical re-run of the frozen jobs) and tie-fair expected recall.
Per system, recall for an arity = hits / test formulas of that arity pooled over the 5 splits; paired tests over systems with ≥1 such formula.

## What the benchmark contains
| study | binary test positives | ternary | quaternary | systems with ≥5 distinct quaternary test formulas |
|---|---|---|---|---|
| decisive (9) | 58% (median 31 distinct/system) | 40% (median 24) | 2% (median 2, total 15) | 0 of 9 |
| replication (20) | 60% (median 29) | 37% (median 20) | 3% (median 1, total 31) | 1 of 20 |
| pooled 29 | 59% | 38% | 3% (46 distinct formulas in total) | 1 of 29 |

## Recall@100 / recall@500 by arity, pooled 29 systems (fair ties)
| arm | binary | ternary | quaternary |
|---|---|---|---|
| BLEND (RF + pooled template) | 0.597 / 0.862 | 0.156 / 0.579 | 0.000 / 0.028 |
| TPOOL (pooled template) | 0.541 / 0.750 | 0.189 / 0.532 | 0.000 / 0.000 |
| TPOOL + RF tie-break only | 0.547 / 0.751 | 0.197 / 0.534 | 0.000 / 0.000 |
| template target-only | 0.468 / 0.657 | 0.110 / 0.373 | 0.000 / 0.178 |
| RF alone | 0.211 / 0.453 | 0.027 / 0.145 | 0.000 / 0.003 |
| random | 0.001 / 0.009 | 0.002 / 0.017 | 0.000 / 0.005 |
(Per-study tables, MRR and strict-leakage arms in `results/m2_tables.md`.)

## BLEND − TPOOL by arity (pooled 29, two-sided Wilcoxon)
- binary: recall@100 +0.056 [+0.022, +0.089], 22/7, p = 0.002; recall@500 +0.111 [+0.074, +0.150], 25/2, p < 0.0001
- ternary: recall@100 −0.033 [−0.086, +0.020], 9/19, p = 0.22; recall@500 +0.047 [−0.013, +0.106], 17/10, p = 0.14
- quaternary: recall@100 0 for both (no arm finds any quaternary in the top 100 of any system/split); recall@500 +0.028, 3/0, p = 0.11
The same pattern holds in each study separately (binary gain; ternary loss at top-100, n.s.).

## Verdict
1. **No arm re-finds a single held-out quaternary in its top 100**, in any of the 29 systems. The benchmark at k = 100 measures
   re-finding binary and (much less so) ternary sub-system compounds. Nothing can be claimed about discovering new 4-element chemistry.
2. **The BLEND gain is entirely a binary-compound effect.** For ternaries RF blending tends to *hurt* at top-100 (19 of 29 systems
   worse, n.s.). This must be stated in the paper.
3. Pooled templates beat target-only templates on binaries and ternaries; target-only templates are the only arm with non-trivial
   quaternary recall@500 (0.178), because pooled counts from other systems push rare 4-element templates down.
4. Only 1 of 29 systems has ≥5 quaternary test formulas, so per-system quaternary estimates are not interpretable.

Files: `analyze_m2.py`, `results/m2_stats.json`, `results/m2_tables.md`.
