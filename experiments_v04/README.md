# experiments_v04 — Research assignment V04 (branch `research-v04`)

Contradiction-Driven Evolutionary Knowledge Discovery in Inorganic Chemistry.
Concept and direction: Himanshu Mazumdar, R&D Centre, Dharmsinh Desai University · Code developed with AI assistance.

**V03 is preserved unchanged** (`evochem/`, `data/`, `results/`, `run_demo.py`, `gui.py`); a test asserts this
against commit `a3b1daa`. All V04 code lives here and only *imports* V03 modules.

## Ground rules applied everywhere
- Target `formation_energy_per_atom_eV` is **DFT-computed (Materials Project)**, never a measured enthalpy. Measured
  enthalpies / band gaps are used only in `validation/measured_properties/` and kept separate.
- Test partitions are sealed: hyperparameters, fitness, contradiction thresholds, acceptance and rule selection use
  training data / inner validation only (a test poisons test labels and checks decisions do not change).
- Same splits for all methods: 10 V03 random 60/40 splits, the V03 family-held-out split, plus 5 V04 group folds
  (whole stoichiometry families held out, `shared/common.py:group_kfold_splits`) and the V03 quaternary split in Expt-06.
- Multiple evolutionary seeds per split. Matched GP budgets (documented per experiment). Negative results kept.

## Layout
| folder | content | stage |
|---|---|---|
| `validation/baseline_verification` | re-run of V03 benchmark vs committed results | 1 |
| `validation/synthetic` | SYNTHETIC controlled contradiction + corruption environments | 1 |
| `expt01_specialist_rules` | two-population G/S learner vs 7 controls + 4 ablations | 1 |
| `expt02_evolutionary_memory` | versioned competing-hypothesis memory, incremental episodes | 1 |
| `expt06_baselines_ablations` | ridge/RF/GBR/MLP/sparse-Lasso/V03-GP/proposed on identical splits | 1 |
| `expt03_chemical_transfer` | transfer to similar / dissimilar chemical systems | 2 |
| `expt04_emergent_periodicity` | periodicity robustness + downstream benefit | 2 |
| `expt05_statistical_focusing` | active observation strategies | 2 |
| `validation/measured_properties` | independent measured formation enthalpy / band gap | 2 |
| `expt07_compound_discovery` | hidden-compound discovery, PU protocol | 3 |
| `expt08_strategy_evolution` | conditional (see its README) | 3 |
| `reports/` | go/no-go reports per stage and the final research report | |

## Reproduce
```
pip install -r ../requirements.txt pyyaml pytest
python validation/baseline_verification/verify_v03.py
python validation/synthetic/reproduce.py
python expt01_specialist_rules/reproduce.py      # each experiment: python <dir>/reproduce.py [--quick]
python -m pytest -q tests
```
Each experiment writes `config.yaml` (frozen parameters + provenance: package versions, git commit, dataset SHA-256),
`metrics.csv`, `predictions.csv`, `rules.json` (where applicable), `figures/`, `summary.csv`, `paired_tests.csv`.
Statistics: bootstrap 95% CI over splits (seeds averaged within split), paired Wilcoxon signed-rank, Cohen's d_z,
Holm correction within each comparison family. Note: run-level tests pair (split, seed) runs, which are not fully
independent (seeds share a split); split-level tests are reported in the analyses where they matter.
