# V05 Q1 Readiness Audit
Concept and direction: Himanshu Mazumdar, R&D Centre, Dharmsinh Desai University · Code developed with AI assistance.

**Verdict: NOT ready for a Q1 venue as a methods paper claiming a better discovery algorithm.** The evidence refutes
that claim. A negative or benchmark paper is possible after the fixes listed below.

| # | Question | Plain answer |
|---|---|---|
| 1 | Does the proposed method beat the strongest baseline? | **No.** recall@100 0.036 vs 0.215, diff −0.179 [−0.215, −0.143], 0 of 9 systems, Holm p = 1.0. |
| 2 | Does knowledge transfer across chemical systems? | **No** for learned models (PU_RF −0.003, EHP −0.015). Yes, exploratorily, for pooled stoichiometry templates (+0.078, 9 of 9). |
| 3 | Does cumulative memory help? | **No.** 0.042 vs best control 0.051. No forgetting, but no gain. |
| 4 | Is the evidence multi-system and statistically sound? | Yes in design: 9 systems, system as unit, paired tests, cluster CIs, Holm, pre-registered. n = 9 limits power. |
| 5 | Is the data provenance clean and are labels kept separate? | Yes. SHA-256 manifest, MP snapshot 2025-09-25, ICSD-linked "observed" label, DFT and measured enthalpy kept separate (MAE 0.088 eV/atom over 71 formulas). |
| 6 | Is leakage controlled? | Mostly. Test sets are frozen, and the cross-system duplicate formulas (68) are removed in C/D. One flaw: Protocol B inner validation is not family-grouped. |
| 7 | Are the baselines strong and complete? | Yes for PU ranking (11 baselines, including priors and an embedding). PySR and Roost were run, but on a regression proxy task, not the PU ranking task. CrabNet/MEGNet-type baselines and a structure-aware baseline are absent. |
| 8 | Is it reproducible? | Yes. Lockfiles, pytest (8 V05 tests + V04 tests), CI workflow, `regenerate_all.sh`, deterministic seeds; V04 reproduces exactly. |
| 9 | Is there a real-world (industrial) value demonstrated? | **No.** The Na-Fe-P-O shortlist is computational hypotheses only, with no DFT or experimental validation; the expected precision is ~6%. |
| 10 | What is the paper's defensible contribution today? | A rigorous negative result: evolutionary symbolic PU hypotheses lose to simple stoichiometric-template priors for composition discovery across 9 systems, together with a reproducible multi-system benchmark. |

## Weaknesses (ranked)
1. The central method fails (H1), and the remaining claims (H2, H3) fail too.
2. The discovery "ground truth" is MP/ICSD-observed, so true precision is unknown (lower bound only), and the candidate space caps at 30 atoms.
3. Protocol B nested selection flaw.
4. No temporal validation (Protocol E unavailable).
5. n = 9 systems gives limited power; the systems are oxide-heavy and share O.
6. The best performer (PU_RF + template) is exploratory and not pre-registered.
7. The industrial case is unvalidated.
8. PySR and Roost were evaluated only on regression.

## Smallest decisive next experiment
Pre-register one comparison: **PU_RF + pooled template prior (rank-mean) vs template prior alone**, on Protocol A with
family-grouped inner validation. Run it on the **next 9 systems produced by the same greedy selection rule** (disjoint from
V05's nine), with recall@100, the system as the unit, a one-sided Wilcoxon test and a +0.02 margin. This takes about 10 CPU-minutes.
It decides whether any learned component adds value beyond template counting. If it fails, the work should be published
as a benchmark or negative-result paper. In parallel, getting ICSD publication years would enable Protocol E, the strongest
test of genuine discovery.

Note: the assignment's original list of 10 readiness questions was not available to me verbatim; the questions above
are my reconstruction of the standard Q1-readiness items.
