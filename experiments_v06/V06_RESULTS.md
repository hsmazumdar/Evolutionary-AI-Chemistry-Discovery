# V06 confirmatory results (single pre-registered run)

Pre-registration: PREREG_V06.md (release research-v06-prereg-ea74493). Analysis: frozen `analyze_v06.py` (commit d1a43cb), run once on E1+E2 (logs/analyze.log). 80 new systems (#39-118). Deviations: DEVIATIONS.md (entry 10: E2 seed overflow fix, mod 2**32; E1 not re-run).
Support rule: adjusted p < 0.05, mean gain >= 0.02 in hypothesis direction, bootstrap 95% CI excluding 0. H6.1-H6.4 Holm-adjusted as one family; H6.5 separate family (own alpha).

| Hyp | Comparison | n systems | mean diff | 95% CI | W/L/T | adj. p | Outcome |
|---|---|---|---|---|---|---|---|
| H6.1 | BLEND - TPOOL, recall@100 (all) | 80 | +0.033 | [+0.018, +0.049] | 45/23/12 | 0.0014 (Holm) | SUPPORTED |
| H6.2 | BLEND - TPOOL, recall@500 (all) | 80 | +0.028 | [+0.014, +0.043] | 44/25/11 | 0.0014 (Holm) | SUPPORTED |
| H6.3 | BEST-LEARNED - TPOOL, recall@100 (TPOOL >= best learned) | 80 | -0.340 | [-0.372, -0.305] | 4/76/0 | 3.9e-14 (Holm) | SUPPORTED |
| H6.4 | BLEND - TPOOL, recall@500, novel-only | 80 eligible | -0.022 | [-0.049, +0.003] | 27/38/15 | 0.92 (Holm) | NOT SUPPORTED (point estimate favours TPOOL) |
| H6.5 | BLEND - TPOOL, recall@100, temporal split (<=2010 -> 2011-2025) | 3 eligible | +0.067 | [0.000, +0.200] | 1/0/2 | 0.50 | NOT SUPPORTED (underpowered: only 3 systems had >=5 test positives) |

## Key arm means, E1 (80 systems)
all recall@100: BLEND 0.474, Magpie-GB blend 0.472, Roost blend 0.458, TPOOL 0.441, template target-only 0.391, best single learned (Magpie-GB PU) 0.114, PU-RF 0.111, Roost-style PU 0.082, SynthNN-style 0.082, random 0.002.
Novel-only recall@500: TPOOL 0.520, BLEND 0.498; Roost blend 0.543 and Magpie blend 0.524 (exploratory, not pre-registered tests). Domain-knowledge ablation C1 (charge-neutral first) is much higher on novel compounds (R@100 0.427) but lower overall (0.284).
Full tables: results/e1_arms.csv, results/e2_arms.csv, results/hypotheses.json.

## Honest reading
The V05 BLEND gain replicates on 80 fresh systems, now clearly (p ~ 0.001, CI above zero), and pooled templates beat every learned composition model by a wide margin. But the gain does not extend to genuinely novel compounds, where the blend is slightly worse than TPOOL, and the temporal test could not be evaluated meaningfully (3 eligible systems). Claims of "discovery" beyond template reuse are not supported.
