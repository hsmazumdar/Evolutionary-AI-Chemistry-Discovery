# Contradiction-Driven Evolutionary Knowledge Discovery with Revisable Rule Memory for Inorganic Materials

**Research report V04 — evaluation of a hypothesis, with predominantly negative findings**

Concept and direction: Himanshu Mazumdar, R&D Centre, Dharmsinh Desai University · Code developed with AI assistance.
Repository: https://github.com/hsmazumdar/Evolutionary-AI-Chemistry-Discovery (branch `research-v04`; tags
`stage1-checkpoint`, `stage2-checkpoint`, `stage3-checkpoint`). Date: 14 Oct 2026.

> **Status statement.** This report does *not* claim a positive methodological contribution. The central hypothesis —
> that reliable contradictions drive the evolution of specialist rules that generalise better — was not supported.
> Results are reported in full, including negative ones, as required by the assignment (rule A8, stopping rule E).

## Abstract
We implemented and tested a two-population genetic-programming system in which a general population G learns
formation-energy rules and a specialist population S learns rules for contradictions of G within learned applicability
domains, together with a versioned competing-hypothesis memory. On 91 experimentally observed Fe-Na-O-P compounds with
DFT-computed (Materials Project) formation energies, 16 fixed splits and 5 evolutionary seeds, the two-population
system improved on plain GP (−0.031 eV/atom, Holm p=0.004) but was indistinguishable from a specialist trained on
plain high-residual samples (+0.002, p=0.90), and was worse than plain GP given the same oxidation-state features
(+0.029, p=0.002). Ablating calibrated uncertainty, evidence reliability or the validation gate had no effect. In
synthetic environments with known exception domains, the proposed priority under-performed plain residual selection
and accepted spurious specialists in 40% of environments without any exception. The revisable memory did not reduce
forgetting relative to replay. All GP variants were significantly less accurate than ridge, MLP, gradient boosting
and random forests. Positive findings are narrower: (i) emergent periodicity from compound co-occurrence is robust
(ARI 0.50 ± 0.03 under subsampling, null 95th percentile 0.03) and learned element embeddings reduce GP error from
0.320 to 0.210 eV/atom, although random embeddings recover most of this; (ii) evolved rule structures act as a useful
low-data prior for chemically similar systems; (iii) a positive-unlabelled discovery protocol ranks hidden compounds far
better than V03's hull-based ranking (median rank 18,148 → 1,549 of ~41k).

## 1. Problem and data
- Compounds: 91 distinct reduced formulas in Fe-Na-O-P with ICSD experimental observation (existence is experimental);
  formation energies are **DFT-computed** (MP GGA/GGA+U/r2SCAN mixing), never treated as measured enthalpies.
- Measured data used separately: 2010 measured formation enthalpies (Kingsbury/matminer) and 4492 measured band gaps.
- Splits: 10 V03 random 60/40; V03 family-held-out; 5 V04 group folds holding out whole stoichiometry families; V03
  quaternary-held-out (Expt-06). Dataset SHA-256 recorded in every `config.yaml`.

## 2. Formal definitions
Let T be the training partition, split by a seeded permutation into inner-fit F (75%) and inner-validation V (25%).
Features x ∈ R^22 are composition-weighted mean/deviation/range of seven element attributes plus element count.
- **General rule** g(x) = a + b·φ_G(x), φ_G an expression tree; (a, b) by least squares; fitness = MAE + 0.003·|φ_G|.
- **Archive** A = 10 best distinct trees of G's final population (each with its own scaling).
- **Calibrated uncertainty** σ̂(x) = sqrt(s0² + (c·sd_{h∈A} h(x))²), with (s0, c) = argmax Σ_{i∈V} log N(r_i; 0, σ̂(x_i)²).
- **Evidence reliability** ρ_i = 1 − exp(−n_eff,i/1.5), n_eff = (# distinct observed polymorphs) + 0.25·log(1 + extra ICSD
  records). Repeated records of one structure are not counted as independent confirmations.
- **Contradiction**: i ∈ F with priority π_i = (|r_i|/σ̂(x_i))·ρ_i among the top 15% (≥4) of F.
- **Applicability domain** D = {x : τ(x) = 1}, τ a depth-2 decision tree separating contradictions from other F samples.
- **Specialist** s(x) = a' + b'·φ_S(x'), x' = x or x ⊕ (charge-balanced, charge-imbalance) (missing-variable search).
- **Combined prediction** ŷ(x) = g(x) if x ∉ D, else s(x) (replace) or (g+s)/2 (blend); mode chosen on V.
- **Acceptance**: specialist accepted iff MAE_V(ŷ) < MAE_V(g) − 0.005 and |V ∩ D| ≥ 1.
- **Rule confidence (memory)**: w_h ∝ exp(−MAE_h/τ), τ = median active MAE; hypotheses retired when
  MAE_h > 1.5·min MAE or outside the top 5; revisions = coefficient changes > 0.02.

## 3. Algorithms
```
TWO-POPULATION(T):
  F, V ← inner_split(T)
  G ← GP(pop 200).evolve(F, 40 gens)                 # Population G
  A ← archive(G); (s0,c) ← calibrate(A, V)
  π ← surprise(F)·reliability(F); C ← top-q(π)
  τ ← DecisionTree(depth 2).fit(F, 1[C]); D_F ← τ(F)
  for feature set in {base, base+candidate variables}:  # missing-variable search
      S ← GP(pop 200).evolve(F ∩ D_F, 10 gens)       # Population S
      for mode in {replace, blend}: score on V
  accept best (S, mode) iff it beats G on V by margin
  rescale (a,b) of G and S on T; return model

MEMORY-EPISODE(memory M, population P, new data E, buffer B):
  P.evolve(E ∪ B, 20 gens); B ← reservoir(B ∪ E, 12)
  for h in M.active: refit (a,b) on E ∪ B; log revision if changed
  add archive(P) as new hypotheses; retire dominated; recompute confidences
  predict = confidence-weighted mean of top-3; sd = spread ⊕ 1.25·best MAE
```
**Complexity.** One GP generation costs O(N_pop · n · L) (L = tree size ≤ 2^6); a two-population run costs
O(N_pop · L · (40·|F| + 20·|F∩D|)) plus O(|F| log |F|) for the tree, i.e. no more than the matched 60-generation control.
Calibration is a 25×7 grid, O(175·|V|). Memory update per episode is O(K · (|E|+|B|) · L) for K stored hypotheses.

## 4. Protocols and leakage controls
Test partitions are used only after all decisions are frozen; a unit test poisons test labels (1e6) and asserts the
learned rule and acceptance decision are unchanged. Exceptional/ordinary test labels (for evaluation only) come from a
ridge reference model fit on T. Matched budgets: 60 generations × pop 200 for all Expt-01 conditions except the
40-generation reference. Statistics: bootstrap 95% CI over splits (seeds averaged within split); paired Wilcoxon;
Cohen's d_z; Holm within comparison families. Run-level tests (80 runs) treat seeds within a split as separate pairs,
which overstates independence; split-level tests (16) are reported for the key comparisons.

## 5. Results
### 5.1 V03 reproduction
All V03 outputs reproduced byte-for-byte or to ≤3.3e-16 (only runtime/timestamps differ).

### 5.2 Synthetic controlled contradictions (SYNTHETIC)
Proposed − high-residual specialist +0.009 [+0.004, +0.015] (p=0.004, 75 environment×seed pairs). Under low noise
(σ=0.01) the high-residual specialist found the hidden variable in 4/5 seeds (domain precision 0.83); the proposed
priority, which divides by archive disagreement — largest exactly inside exception domains — selected fewer true
exceptions. False discoveries: 0.4 with no exceptions, 0.4–0.6 with corruption only. Reliability reduced the share of
corrupted points in contradiction sets (61% vs 83%) without improving test error.

### 5.3 Expt-01 (DFT Ef, eV/atom)
Random splits: ordinary GP 0.310, +extra generations 0.304, V03 weighting 0.302, random specialist 0.331, high-residual
specialist 0.287, **proposed 0.288 [0.267, 0.307]**, GP + charge-balance features 0.229 [0.209, 0.252].
Key paired results in the abstract. Specialists accepted in ~80% of runs, 7.5 nodes; domain precision for held-out
exceptions 0.37 (base rate 0.25). Error on training contradictions fell 0.63 → 0.33, on held-out exceptions only
0.49 → 0.45. Ablations: only the missing-variable search matters (−0.020, Holm p=0.003).

### 5.4 Expt-02 memory
Chemical stream (binaries → ternaries → quaternaries) final MAE: proposed 0.399, replay 0.432 (n.s.), scratch 0.311,
V03 archive 0.286 (proposed worse, Holm p<1e-4), sequential 0.813. Forgetting on binaries: proposed 0.35 vs V03 archive
0.06. 90% interval coverage 0.63 under shift. The memory halves stored items vs full-data methods but does not deliver
its accuracy.

### 5.5 Expt-06 baselines (16 splits)
Ridge 0.197, MLP 0.217, GBR 0.232, RF 0.243, proposed 0.277, V03 GP 0.290, sparse Lasso on expanded features 0.314.
Proposed vs ridge +0.068 (Holm p=0.004, d_z 1.33). PySR and Roost not run (no Julia / PyTorch on the compute box).

### 5.6 Expt-03 transfer
With 5–10 target labels, reusing the evolved structure beats evolving from scratch on similar systems (−0.128 at 10
shots, Holm p=0.024); on dissimilar systems the advantage reverses by 20 shots (+0.188, Holm p<1e-4). A random forest
trained on Fe-Na-O-P is equally good zero-shot on similar systems.

### 5.7 Expt-04 periodicity
Robust emergent grouping (above). Downstream: GP 0.320 → 0.210 with learned embedding (Holm p=0.0003) vs 0.231 with a
random embedding (difference n.s. after correction) and 0.271 with an element-shuffled embedding (Holm p=0.0015).
No benefit for ridge.

### 5.8 Expt-05 focusing
Uncertainty + diversity acquisition lowers learning-curve MAE (−0.17, Holm p=0.001), mainly by avoiding unstable early
fits; final MAE differences n.s.; reliability-weighted acquisition gives nothing.

### 5.9 Measured-property validation (separate from DFT)
MP DFT vs measured ΔHf for 13 Fe-Na-O-P formulas: MAE 0.080 eV/atom. Measured ΔHf, system-grouped 5-fold CV (2010
formulas): RF 0.192, ridge 0.316, GP 0.323. Measured band gap: RF 0.54, ridge 0.91, GP 0.94 eV.

### 5.10 Expt-07 discovery (PU)
Hits among 32.7 hidden compounds: PU-RF (attributes only) 1.6 @100 / 13.7 @1000 / median rank 1,549 vs V03 1.9 / 7.8 /
18,148; best top-100 5.9 with oxidation priors + analogy templates (random expectation 0.08).

### 5.11 Expt-08
Not run; preconditions unmet (documented).

## 6. Interpretability and chemical case study
Typical accepted specialist (split seed0, seed 0): domain = mean Pauling EN > 2.51 and valence-electron range ≤ 0.60,
i.e. oxygen-rich formulas; `Ef_S = −1.381 + 1.716·(−0.15/sqrt|dev_mass| + charge_imbalance)` blended with G.
The most frequently flagged contradictions over all runs were Na5P3O10, FePO6, Fe3(PO8)2, P2O5, Na3PO4, Fe4O13, P2O9,
Na4P2O7, NaO3, NaO2. Several are oxygen-excess or peroxo/superoxo-type formulas (FePO6, Fe4O13, P2O9, NaO3) whose
database entries deserve scrutiny; the specialist effectively learns "charge imbalance under normal oxidation states
→ less stable", which is textbook chemistry and is learned better by giving the general GP those features directly.

## 7. Failure analysis
1. **Uncertainty works against the hypothesis**: archive disagreement is high where exceptions are, so surprise =
   |r|/σ̂ down-weights the very samples that should be specialised.
2. **Acceptance gate too weak**: ~14 validation samples, 0–3 inside the domain; improvements of 0.005 eV/atom are
   noise. Synthetic false-discovery rates 0.2–0.6.
3. **Confounded improvement**: gains came from the missing-variable channel (oxidation-state priors).
4. **Overfitting to contradictions**: training-contradiction error halves, held-out exceptional error improves ~8%.
5. **Small data**: 91 compounds (no 3–4 element system has ≥100 confirmed compounds), DFT target.
6. **GP accuracy ceiling**: symbolic GP is ~0.07–0.09 eV/atom behind linear/ensemble baselines.

## 8. Reproducibility
`python experiments_v04/<expt>/reproduce.py` per experiment (all finish in < 2 min on 8 CPU cores), `pytest
experiments_v04/tests` (8 tests incl. V03-unchanged and test-label-poisoning). Each `config.yaml` stores Python and
package versions (numpy 2.5.4, pandas 3.0.6, scipy 1.18.1, scikit-learn 1.9.1, matplotlib 3.11.2), git commit, dataset
hashes and seeds. Predictions are saved with sample and split IDs.

## 9. Limitations and future work
Required before any Q1 submission on this idea: (i) permutation-null specialist acceptance with measured false-discovery
control; (ii) contradiction scores that do not shrink at exceptions (e.g. leave-one-out residuals, conformal scores);
(iii) multiple chemical systems or a pooled multi-system benchmark of ≥ several hundred compounds; (iv) controls with
identical feature sets everywhere; (v) PySR/SISSO and Roost/CrabNet baselines on a GPU machine; (vi) measured targets as
primary endpoints. The most promising leads from V04 are the PU discovery protocol and learned element embeddings as
GP inputs — both should be framed as their own, modest contributions rather than as evidence for contradiction-driven
discovery.
