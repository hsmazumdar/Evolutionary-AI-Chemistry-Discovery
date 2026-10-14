# Independent MEASURED-property validation (kept separate from DFT)

Data: matminer `expt_formation_enthalpy_kingsbury` (measured formation enthalpy, eV/atom; 2010 unique formulas after
merging duplicates, 1726 with a reported uncertainty, median 0.019 eV/atom) and `expt_gap` (measured band gap, eV;
4492 unique formulas). Copied into `./data` with SHA-256 in config.yaml.
1. Cross-target check: Fe-Na-O-P-system compounds with measured enthalpy (14; 13 matched to an MP formula).
2. Learning measured enthalpy, 5-fold GroupKFold by chemical system (no system in both train and test).
3. Same for measured band gap. Models: mean, ridge, RF (seeds 0–2), GP (pop 200, 40 gens, seeds 0–2).
Note: V03 `featurize` propagates NaN if any element in a batch lacks an attribute; here features are computed per formula.
