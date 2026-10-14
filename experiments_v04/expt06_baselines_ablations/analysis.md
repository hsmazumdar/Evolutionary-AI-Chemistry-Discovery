# Expt-06 analysis (DFT formation energy MAE, eV/atom; 95% CI over splits)

| model | random 60/40 (10) | group held-out (6) | quaternary (1) | runtime s |
|---|---|---|---|---|
| ridge | **0.197 [0.186, 0.208]** | 0.217 [0.163, 0.272] | **0.204** | 0.01 |
| MLP | 0.217 [0.201, 0.232] | **0.215 [0.184, 0.243]** | 0.217 | 2.7 |
| gradient boosting | 0.232 [0.210, 0.257] | 0.232 [0.202, 0.262] | 0.502 | 3.3 |
| random forest | 0.243 [0.218, 0.269] | 0.226 [0.193, 0.261] | 0.520 | 6.0 |
| proposed two-population | 0.277 [0.258, 0.294] | 0.267 [0.244, 0.290] | 0.363 | 0.6 |
| V03 GP | 0.290 [0.275, 0.307] | 0.330 [0.280, 0.391] | 0.318 | 0.6 |
| sparse Lasso expanded | 0.314 [0.251, 0.374] | 0.305 [0.184, 0.480] | 0.236 | 8.4 |
| mean predictor | 0.624 | 0.654 | 0.861 | 0 |

Paired over 16 splits (excluding quaternary; Holm): proposed − ridge +0.068 (p=0.0004, d_z 1.33); − MLP +0.057
(p<1e-4); − RF +0.036 (Holm p=0.038); − GBR +0.041 (Holm p=0.013); − V03 GP −0.032 (Holm p=0.038); − sparse Lasso −0.037 (n.s.).
Note the V03 GP here is pop 300/40 gens on full train; it was 0.305 in V03 (same code, different seed protocol).

## Interpretation
Symbolic GP methods (V03 and proposed) are clearly and significantly less accurate than ridge, MLP, RF and GBR on these
91 compounds. The proposed method improves on V03 GP but does not close the gap. Their advantages are compactness
(10–17 nodes) and speed, not accuracy. Ablation summary: see Expt-01 (only the missing-variable component matters).
