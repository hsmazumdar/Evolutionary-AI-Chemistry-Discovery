# V06 deviations / interpretation log
Each entry gives the date and time (IST), what changed, and why. Every entry is recorded before any V06 outcome is computed unless marked otherwise.

1. 2026-10-21 22:40. **C2 (Hautier-style substitution ablation) deferred.** It needs oxidation-state species mapping, which isn't implemented yet. It is an exploratory domain-knowledge ablation only and touches no hypothesis. It will be added before the run or reported as not run.
2. 2026-10-21 22:40. **w grid {0,...,1}.** I follow PREREG s2 literally (V05 code used 0.1–0.9). This applies to all blend arms.
3. 2026-10-21 22:40. **E2 interpretation.**
   - (a) Formulas without a year are removed from the ranked list and from train and test, rather than treated as unlabelled.
   - (b) Pooled template counts and pooled network positives use only other-system compounds with year ≤ 2010, so no future information leaks.
   - (c) There is one temporal split per system (seed 20261021 + 1000·0).
4. 2026-10-21 22:40. **E3 hyperparameters, fixed in code before the run.**
   - Roost-style: H = 32, 2 message-passing layers, one-hot learned element embeddings, 1500 Adam steps (lr 3e-3), PU ratio 5, 4000 sampled unlabelled.
   - SynthNN-style: fixed (64, ratio 5) instead of M3's per-split grid, for cost.
   - Magpie-GB: HistGB(150 iterations), 22 Magpie properties × {mean, avg dev, min, max, range} + arity + sorted fractions.
5. 2026-10-21 22:40. **H6.3 best-learned arm.** It is selected per split by its own family-grouped 3-fold inner recall@100 on training positives. Candidates: PU-RF, B1, B2, SynthNN-style.
6. 2026-10-21 22:40. **The pre-registration was not yet pushed or archived** when this code was written. GitHub push credentials are not available on the box. System selection and building (#39–118) and all V06 runs are held until the pre-registration commit is on GitHub and archived on Zenodo.
7. 2026-10-21 22:27. **Hold lifted.**
   - research-v06 (ea74493, e1f8b41) was pushed by the author from the Vivobook.
   - Release https://github.com/hsmazumdar/Evolutionary-AI-Chemistry-Discovery/releases/tag/research-v06-prereg-ea74493 was published 2026-10-21 22:27 IST. Its tag points at commit ea744931ff37d19cca0648372017ffabcc798846 (verified via the GitHub API). The release's target_commitish field reads "main", but the tag object itself is ea74493.
   - Zenodo DOI not yet verified.
   - System selection and building start after this entry.
8. 2026-10-21 22:40. `analyze_v06.py` was committed before any E1 output was inspected. Interpretations:
   - The H6.3 margin and CI rule are applied in the hypothesis direction: TPOOL leads by ≥ 0.02 and the CI of (best − TPOOL) is below 0.
   - H6.4 eligibility (≥ 3 novel test positives summed over splits) and E2 eligibility (≥ 5 test positives) are computed from label counts only.
9. 2026-10-21 23:17 IST. The agent session was interrupted while waiting. The background E1 run was NOT affected: it was still running at 204/400 jobs, and its processes are intact. It was not restarted; E2 follows automatically in the same chain.
10. 2026-10-21 18:38 IST. E2 crashed at its first job, before producing any outcomes (logs/e2.log): derived RandomForest seed (seed*100+bag inside shared pu_generic, from E2 base SEED0+1000*i) = 20261021000 exceeds sklearn's 2^32 limit. Fix: in run_v06.py only, RF/GB factories now pass random_state % 2**32. This is a no-op for every seed < 2^32, so E1 (already finished, not re-run) is unaffected. Nothing else changed. The crashed E2 log is preserved as logs/e2_crash.log; E2 rerun once.
