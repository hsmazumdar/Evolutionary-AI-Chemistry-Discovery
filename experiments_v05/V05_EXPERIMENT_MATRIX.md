# V05 Experiment Matrix
Concept and direction: Himanshu Mazumdar, R&D Centre, Dharmsinh Desai University · Code developed with AI assistance.

| ID | Question | Protocol | Systems / units | Methods / arms | Budget | Script | Output | Status |
|---|---|---|---|---|---|---|---|---|
| P1 | Does V04 reproduce? | re-run V04 | Fe-Na-O-P | all V04 expts | as V04 | (V04 scripts) | V04_REPRODUCTION_AUDIT.md | done |
| P2 | Dataset + QC | — | 9 systems, 1,250 formulas (756 observed) | — | — | scripts/build_dataset.py, dataset_qc.py | data/, results/dataset_qc.json | done |
| H1 | Discovery: EHP vs strongest PU baseline | A (5 random 60/40), B (5 family folds) | 9 systems × 5 splits × 2 | EHP + 11 baselines, nested inner selection | EHP 200×30, 5 bags | scripts/run_h1_discovery.py | results/h1/ | done (confirmatory) |
| H2 | Transfer | C (leave-one-system-out) × 5 splits | 9 targets | PU_RF, EHP (pooled vs target-only), template prior, zero-shot | RF 10 bags; EHP 200×30 | scripts/run_h2_transfer.py | results/h2/ | done (confirmatory) |
| H3 | Cumulative memory | D (3 stream orders) | 9 episodes × 3 orders | proposed + 5 controls | 200×30, 3 bags, identical per episode | scripts/run_h3_memory.py | results/h3/ | done (confirmatory) |
| E | Temporal hold-out | E | — | — | — | — | — | UNAVAILABLE: no publication dates in snapshot |
| X1 | EHP ablations | A | 9 × 5 | uniform weights, top-1, 3× gens, 3× bags, +template | — | scripts/run_exploratory.py | results/exploratory/ablation_metrics.csv | done (exploratory) |
| X2 | Contradiction diagnostics | 5-fold cross-fit + permutation null (20) | 9 systems | PU_RF | — | scripts/run_exploratory.py | results/exploratory/contradiction_*.csv | done (exploratory) |
| P8 | Regression baselines (DFT Ef) | C | 9 targets | mean, ridge, RF, GBR, V03 GP, PySR, Roost | see script | phase8/run_regression_benchmark.py | results/phase8/ | done (exploratory) |
| P9 | Statistics | — | system = unit | Wilcoxon, d_z, cluster bootstrap, Holm | 10k bootstrap | scripts/run_statistics.py | results/statistics.json, statistics_tables.md | done |
| P10 | Industrial case (Na-Fe-P-O) | full data | Fe-Na-O-P | template, PU_RF, rank-mean | — | scripts/run_industrial_case.py | results/industrial/ | done |
| — | Periodicity / embeddings | — | — | — | — | — | — | not run in V05 (exploratory only; out of time budget) |

Regenerate everything: `scripts/regenerate_all.sh` (`FULL=1` re-runs experiments). Compute: 8-core CPU box; wall-clock H1 309 s, H2 114 s, H3 36 s, Phase 8 409 s (Roost 1,476 CPU-s, PySR 325 CPU-s), exploratory 349 s.
