# V04 Reproduction and Integrity Audit (V05 Phase 1)

Audited commit: `e2caa6f` (research-v04 head). Method: clean `git worktree` of `e2caa6f`; every V04 `reproduce.py`
re-run in the documented order on the 8-core box (Python 3.13, numpy 2.5.4, pandas 3.0.6, scipy 1.18.1,
scikit-learn 1.9.1); outputs compared with the committed files (`git diff`).

## 1. Re-run results
| artefact | result |
|---|---|
| V04 pytest (8 tests) | 8 passed |
| synthetic, Expt-03, -04, -05, -07 (metrics, summaries, paired tests) | byte-identical |
| Expt-01, -02, -06 `metrics.csv` | identical except the `runtime_s` column (max numeric diff in MAE columns 0.0) |
| Expt-01, -02, -06 `summary.csv` | differ only in runtime columns |
| all `paired_tests.csv` | byte-identical |
| measured-property `metrics.csv` / `results.json` | max diff 1.1e-16 (floating-point summation order) |
| `config.yaml` files | differ only in provenance (git commit/dirty flag) |
**Verdict: every V04 table value reproduces.** No discrepancy in any reported number.

## 2. Integrity audit
| check | finding | severity |
|---|---|---|
| Train/test disjointness (all V03/V04 splits) | verified (also a V04 unit test) | OK |
| Test-label leakage into decisions | V04 unit test poisons test labels; decisions unchanged | OK |
| Duplicate formulas (Fe-Na-O-P table) | 0 duplicate formulas, 0 duplicate reduced compositions | OK |
| Polymorphs | DFT Ef of each formula = minimum over observed polymorphs (verified, max diff 0.0); polymorph count stored; polymorphs never split across train/test because the unit is the formula | OK |
| Hyperparameters | Expt-01 thresholds fixed a priori, **but** (i) reliability formula changed after first look (log1p → 0.25·log1p), (ii) a charge-balance control was added after the first analysis. Both disclosed in V04; both changed results against the hypothesis, not for it | Minor, disclosed |
| Independence of statistical units | V04 run-level tests pair (split, seed) runs; seeds share splits and the 10 random splits overlap heavily (60% train), so p-values are optimistic. V04 reported split-level tests for key comparisons | Moderate |
| Single-system generalisation | All V04 confirmatory evidence is from one system (91 formulas) | Major (addressed by V05 multi-system design) |
| Expt-03 transfer leakage | target sets excluded compounds inside Fe-Na-O-P; subsystem compounds shared between targets and source (e.g. Fe–O, Fe–P binaries) were removed. OK | OK |
| Expt-04 embedding leakage | embedding excluded compounds whose elements ⊆ {Fe,Na,O,P}; for transfer, also ⊆ target. OK | OK |
| Expt-07 "V03 recomputed" | recomputed V03 analogy+GP_ox recall@100 1.9 vs 2.0 reported by V03 (different GP run, same method) — disclosed | Minor |
| Candidate-space coverage | formulas with total atoms > 30 are outside the space and silently never discoverable (V05 reports the count) | Minor |
| Holm families | Holm applied within metric families, not across the whole report | Minor |

## 3. Consequences for V05
Unit of analysis becomes the chemical system (9 systems); p-values computed over systems; seeds/splits averaged within
system; cluster bootstrap over systems; Holm across the pre-registered primary tests.
