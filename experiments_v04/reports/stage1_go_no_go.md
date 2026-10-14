# Stage 1 go/no-go report (V04)

Date: 2026-10-14. Branch `research-v04`, tag `stage1-checkpoint`. All numbers: DFT (Materials Project) formation energy,
eV/atom, hidden test partitions never used for any decision.

## (a) V03 baseline verification — PASS
Unchanged V03 code re-run in a clean worktree of `a3b1daa`: all CSV/JSON/PNG outputs byte-identical or identical up to
floating-point round-off (max 3.3e-16) and timestamps; only the runtime line differs (87 s vs 104 s).
See `validation/baseline_verification/v03_reproduction.md`. No discrepancies.

## (b) Synthetic controlled contradictions — MIXED / falsification concern
- Architecture recovers a hidden exception domain and its missing variable under low noise/hard boundaries, but the
  plain high-residual specialist does it better than the proposed uncertainty×reliability priority
  (overall proposed − high-residual +0.009 [+0.004, +0.015], p=0.004).
- **False discoveries:** specialists accepted in 40% of environments that contain no exception at all, and 40–60% with
  corruption only. The inner-validation gate is insufficient.
- Reliability helps exclude corrupted observations from the contradiction set (61% vs 83% corrupted) but not test error.

## (c) Expt-01 contradiction-driven two-population — **NO-GO for H1**
- vs ordinary GP −0.031 [−0.050, −0.013] (Holm p=0.004); vs GP+extra generations −0.030 (Holm p=0.018).
- vs high-residual specialist +0.002 [−0.012, +0.016] (p=0.90): **no contradiction-specific benefit**.
- vs GP given the same charge-balance features: **+0.029 [+0.005, +0.052] worse (p=0.002)**.
- Ablations: uncertainty, reliability, validation gate each ≈0 effect; missing-variable search is the only active part.
- Gain on training contradictions (0.63→0.33) ≫ gain on held-out exceptions (0.49→0.45).
Conclusion: the observed improvement is explained by (i) residual focusing and (ii) injected oxidation-state prior
features — not by contradiction reliability/uncertainty. Hypothesis unsupported as stated.

## (d) Expt-02 competing-hypothesis memory — **NO-GO for H2 (accuracy/forgetting)**
Equal to replay at equal buffer size (chemical stream −0.033, n.s.); worse than keeping all data (V03 archive +0.113,
Holm p<1e-4); under-covers 90% intervals under distribution shift (0.63). Useful only as provenance/interpretability.

## (e) Expt-06 baselines — GP family is not competitive
Ridge 0.197, MLP 0.217, GBR 0.232, RF 0.243 vs proposed 0.277 and V03 GP 0.290 (random splits); all differences vs
ridge/MLP/RF/GBR significant after Holm over 16 splits. PySR and Roost not run (no Julia / PyTorch) — documented.

## Decision
- **Do not prepare a manuscript claiming contradiction-driven discovery improves generalisation.** Current evidence is
  negative.
- Stage 2 proceeds (user instruction) as *exploratory* work: transfer, periodicity downstream value, active observation,
  measured-property validation — which do not depend on H1 being true.
- Required fixes before revisiting H1: permutation/null-based specialist acceptance (to control false discoveries),
  uncertainty that does not shrink at exceptions, larger systems (>91 compounds), controls given identical feature sets.
