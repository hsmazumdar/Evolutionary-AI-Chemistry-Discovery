# Expt-04 — Emergent periodicity: robustness and downstream benefit

(i) Robustness of the V03 co-occurrence (PPMI-SVD) element embedding — 44k experimentally observed MP compounds, all
Fe-Na-O-P-internal compounds excluded; only co-occurrence is used, no energies — under 20 random 80% compound subsamples
and dimensions 4/8/12/24, scored by ARI vs IUPAC groups (null: 200 label permutations).
(ii) Downstream: composition-weighted mean and deviation of the 12-d embedding appended to the 22 base features, for
ridge and GP (pop 200, 40 gens, seeds 0–2) on the 16 Fe-Na-O-P splits; controls: random Gaussian embedding of equal
size/scale and element-shuffled embedding. (iii) Transfer: ridge zero-shot and pooled 10-shot on the 7 Expt-03 targets,
with embeddings rebuilt *excluding the target system's compounds*.
