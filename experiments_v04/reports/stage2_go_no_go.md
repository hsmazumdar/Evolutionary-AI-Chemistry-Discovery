# Stage 2 go/no-go report (V04) — tag `stage2-checkpoint`

| hypothesis | result | verdict |
|---|---|---|
| H3 transfer (Expt-03) | Source-structure refit beats target-only GP at 10 shots on similar systems (−0.128, Holm p=0.024); reverses on dissimilar systems at 20 shots (+0.188, Holm p<1e-4); RF zero-shot as good or better on similar systems | partial: low-data prior, not a symbolic advantage |
| H4 periodicity (Expt-04) | ARI 0.50 ± 0.03 under 80% subsampling (null 95th 0.03); GP + learned embedding 0.210 vs base 0.320 (Holm p=0.0003) and vs shuffled (Holm p=0.0015), but vs random embedding only −0.021 (n.s.); no gain for ridge | periodicity robust: GO as a finding; downstream benefit: weak |
| H5 focusing (Expt-05) | uncertainty+diversity improves learning-curve MAE (−0.172, Holm p=0.001); final MAE n.s.; reliability adds nothing | weak, diversity-driven |
| Measured validation | DFT–experiment gap 0.080 eV/atom (13 Fe-Na-O-P formulas); measured ΔHf grouped CV: RF 0.192 ≪ GP 0.323 ≈ ridge 0.316; band gap RF 0.54 vs GP 0.94 | GP not competitive on measured data |

Decision: Stage 3 proceeds (user instruction). Expt-07 is run with a PU protocol. Expt-08 (strategy evolution) is
conditional on Expts 01–06 being stable and showing a positive core mechanism; Stage 1 found the core contradiction
mechanism unsupported, so Expt-08 is expected to be skipped with justification.
