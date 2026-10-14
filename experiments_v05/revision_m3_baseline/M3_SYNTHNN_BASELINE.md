# M3 — SynthNN-style composition PU baseline (exploratory; added after results were seen)

## What it is (and is not)
A **faithful lightweight re-implementation of the SynthNN idea**, not the published SynthNN model or code:
composition fraction vector (over the elements of the selected systems: 27 in the decisive study, 38 in the replication) → learned linear atom-embedding layer (30-d,
atom2vec-like, trained end-to-end) → MLP (2 hidden ReLU layers) → P(synthesised). PU training: unlabelled compositions are
drawn from the enumerated candidate spaces and treated as negatives with class re-weighting (unlabelled:positive ratio 5 or 20), fresh draws per minibatch.
- **No pretrained weights.** Published SynthNN was trained on ICSD, which contains our test compounds (leakage).
- **Retrained from scratch for every split** (145 splits), on that split's information only:
  - SYNTHNN-POOL: positives = target training formulas + observed formulas of the other selected systems with the target's test formulas removed (exactly the information TPOOL uses).
  - SYNTHNN-TARGET: positives = target training formulas only.
- Per split, the width (64/128) and ratio (5/20) are chosen by inner validation on 25% of the target *training* positives (test never used).
- Budget: 1,500 Adam steps (batch 64 positives), CPU, ~10 min for all 29 systems. **Disclosure:** a first version (40 epochs ≈ 80 updates for target-only) was clearly under-trained (target-only recall@100 = 0.004) and was discarded before any comparison was written up. A 3,000-step version was stopped for runtime (est. > 2 h); its partial outputs were not used. No other variants were tried. A larger network, longer training, or the published architecture may do better; this is a baseline, not a tuned competitor.
Same splits, candidate pools, train-candidate removal and tie-fair recall (M1) as the frozen studies.

## Key numbers (tie-fair recall, per-system means)
| arm | decisive R@100 / R@500 | replication R@100 / R@500 | pooled 29 R@100 / R@500 |
|---|---|---|---|
| BLEND (RF + pooled template) | 0.379 / 0.696 | 0.430 / 0.754 | 0.414 / 0.736 |
| TPOOL (pooled template) | 0.336 / 0.621 | 0.403 / 0.644 | 0.382 / 0.637 |
| template target-only | 0.298 / 0.494 | 0.324 / 0.544 | 0.316 / 0.529 |
| RF alone (PU-bagged RF, primitive features) | 0.155 / 0.310 | 0.137 / 0.346 | 0.143 / 0.335 |
| **SYNTHNN-POOL** | 0.146 / 0.252 | 0.123 / 0.269 | **0.130 / 0.264** |
| **SYNTHNN-TARGET** | 0.136 / 0.285 | 0.115 / 0.283 | 0.122 / 0.284 |
| random | 0.002 / 0.013 | 0.002 / 0.011 | 0.002 / 0.012 |

Pooled 29 (two-sided Wilcoxon, bootstrap 95% CI):
- SYNTHNN-POOL − TPOOL: recall@100 −0.253 [−0.306, −0.197], 1/28 systems, p < 1e-5; recall@500 −0.373, 0/29
- SYNTHNN-POOL − BLEND: recall@100 −0.284 [−0.333, −0.234], 0/29
- SYNTHNN-POOL − RF alone: recall@100 −0.013 [−0.031, +0.004], n.s.; recall@500 −0.071, 2/25, p < 1e-4
- SYNTHNN-POOL − SYNTHNN-TARGET: recall@100 +0.008, n.s. (pooling other systems does not help this model)
- By arity (pooled 29, R@100): binary 0.193, ternary 0.025, quaternary 0.000 (TPOOL 0.541 / 0.189 / 0.000)

## Verdict
The SynthNN-style learned-embedding PU classifier is **far below the stoichiometric template rankers** (about one-third of
TPOOL's recall@100, losing in 28 of 29 systems) and roughly level with the PU random forest. The paper's statement that
template counting is the strongest ranker in this benchmark therefore holds against a task-matched, leakage-free modern
composition baseline, **with the caveat that it is a lightweight re-implementation with a small budget**. Like every other arm,
it finds no held-out quaternary in its top 100. Plausible reason (not tested): a fraction-vector model cannot easily represent
the integer stoichiometry "template" signal that dominates this task, especially for binaries.

Files: `run_m3.py`, `analyze_m3.py`, `results/metrics_m3_*.csv`, `results/per_test_m3_*.csv.gz`, `results/m3_stats.json`, `results/m3_tables.md`.
