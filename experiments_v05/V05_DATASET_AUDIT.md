# V05 Dataset Audit (Phase 2)

**Selection (pre-registered rule, protocol §2):** anchor Fe-Na-O-P, then 4-element carbon-free systems by descending
number of experimentally observed formulas with complete properties, accepted if sharing ≤ 2 elements with every
system already selected. 9 systems, 1,250 reduced formulas, **756 experimentally observed**, 670 observed multi-element
formulas inside the discovery candidate space (a+b+c+d ≤ 30).

**Sources and provenance** (`data/MANIFEST.json`, SHA-256 of every file):
- Materials Project summary snapshot 2025-09-25 (CC-BY-4.0), `mp_inorganic_all.csv.gz`; every MP entry of each
  system is kept in `data/entries_<system>.csv` (material id, ICSD ids, DFT energy, E_hull, theoretical flag).
- Measured formation enthalpies: matminer `expt_formation_enthalpy_kingsbury`, joined by reduced composition.

**Label separation (never mixed):**
1. `experimentally_observed` — formula has ≥ 1 MP entry linked to an ICSD structure (experimental structure exists).
2. `dft_Ef_min_eV_atom` / `dft_Ef_observed_min_eV_atom` — DFT-computed formation energy (lowest polymorph).
3. `measured_dHf_eV_atom` — calorimetric/tabulated measured enthalpy, only 89 system-formula rows (71 unique formulas).

**Polymorphs:** unit = reduced formula; `n_polymorphs_mp`, `n_polymorphs_observed`, unique ICSD ids and all
material ids are stored. Polymorphs can never straddle a train/test split.

**Automated QC** (`scripts/dataset_qc.py`, also run in pytest/CI):
```
{
 "no_carbon": true,
 "unique_key_per_system": true,
 "observed_have_icsd": true,
 "theoretical_have_no_icsd": true,
 "dft_and_measured_columns_distinct": true,
 "observed_formulas_shared_by_>1_system": 68
}
```
|            |   formulas |   observed |   observed_multi_in_space |   observed_outside_space_or_unary |   polymorph_observed_mean |   max_polymorphs |   with_measured_dHf |   mean_abs_DFT_minus_measured |
|:-----------|-----------:|-----------:|--------------------------:|----------------------------------:|--------------------------:|-----------------:|--------------------:|------------------------------:|
| Fe-Na-O-P  |        191 |         91 |                        82 |                                 9 |                      1.88 |               30 |                  13 |                         0.08  |
| Ba-O-P-V   |        153 |         97 |                        89 |                                 8 |                      1.9  |               62 |                   8 |                         0.068 |
| K-O-S-V    |        132 |         94 |                        87 |                                 7 |                      1.99 |               62 |                   9 |                         0.051 |
| H-N-O-S    |        109 |         92 |                        85 |                                 7 |                      2.23 |               32 |                   0 |                       nan     |
| Al-Ca-O-Si |        140 |         79 |                        65 |                                14 |                      3.3  |              321 |                  13 |                         0.077 |
| K-Mo-O-P   |        126 |         77 |                        62 |                                15 |                      1.78 |               28 |                   9 |                         0.037 |
| B-H-Na-O   |         96 |         76 |                        68 |                                 8 |                      1.88 |               28 |                  13 |                         0.084 |
| Ba-Fe-O-S  |        132 |         75 |                        63 |                                12 |                      2.25 |               32 |                  10 |                         0.137 |
| Mn-O-P-Ti  |        171 |         75 |                        69 |                                 6 |                      1.95 |               46 |                  14 |                         0.124 |
{'n': 71, 'MAE': 0.0877}

DFT vs measured over the 71 unique formulas with both: MAE 0.088 eV/atom.

**Cross-system overlap:** 68 observed formulas (binaries/ternaries of shared element pairs, e.g. P–O, Na–O) appear in
more than one system. Leakage control for transfer (Protocol C) and memory (Protocol D): any source-system positive
whose reduced formula equals a target *test* positive is removed from the source data.

**Protocol E (temporal): UNAVAILABLE.** The snapshot provides ICSD ids but no ICSD collection or publication dates;
no proxy dates are invented. Not run.

**Known limitations:** "not observed" ≠ "does not exist" (PU setting); ICSD coverage biases toward well-studied
chemistries; formulas with > 30 atoms per reduced formula (80 observed) are outside the candidate space; H-N-O-S has
no measured enthalpies in the joined set.
