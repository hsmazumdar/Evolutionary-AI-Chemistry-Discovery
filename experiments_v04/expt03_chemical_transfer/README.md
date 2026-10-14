# Expt-03 — Chemical transfer

**Hypothesis.** Rules evolved on Fe-Na-O-P carry transferable chemistry: they predict, or adapt quickly to, other systems,
more so for chemically similar systems.

Source: all 91 Fe-Na-O-P formulas (DFT Ef). Targets: experimentally observed MP compounds (repo file
`data/mp_expt_observed_subset.csv.gz`, one row per reduced formula, lowest DFT Ef) of K-Fe-O-P (n=40), Li-Fe-O-P (24), Na-Mn-O-P (44) (similar), Na-Fe-O-S (46), Ba-Ti-O-Si (68), Al-Mg-O-Si (48), H-N-O-S (91); counts after removing Fe-Na-O-P-internal compounds. Na-Fe-O-S = intermediate; last three = dissimilar. Shots k ∈ {0,5,10,20} random target labels (5 draws), evaluated on the remaining target compounds.
GP pop 200, 60 gens, seeds 0–2. Methods: GP/ridge/RF source zero-shot; GP source structure with coefficients refit on
shots; GP source + offset; GP target-only from scratch; ridge target-only; ridge pooled source+target; shot mean.
