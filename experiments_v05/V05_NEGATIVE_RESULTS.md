# V05 Negative Results and Deviations
Concept and direction: Himanshu Mazumdar, R&D Centre, Dharmsinh Desai University · Code developed with AI assistance.

## Negative results (all kept and reported)
1. **H1 failed decisively.** EHP recall@100 is 0.036, against 0.215 for the strongest PU baseline (diff −0.179 [−0.215, −0.143]; 0 of 9
   systems). EHP ranks below all learned PU baselines and nearest-positive, and above random only. It also loses on recall@50,
   @500 and MRR, without Fe-Na-O-P, and without H-containing systems.
2. **More EHP compute does not rescue it.** 3× generations gives 0.040 and 3× bags 0.052. Uniform weights change nothing (0.036).
   Confidence weighting is only marginally better than top-1 (0.029).
3. **H2 failed.** Pooling other systems' data into PU_RF (−0.003) or EHP (−0.015) does not improve recall@100. Zero-shot
   transfer is worse than target-only.
4. **H3 failed.** The versioned memory (0.042) does not beat scratch (0.045), sequential fine-tune (0.051) or the V04 archive
   (0.045). Its zero forgetting is real but uninformative, because all arms forget little at this low accuracy level.
5. **Contradiction diagnostics found nothing actionable.** Only 1.6% of observed formulas are flagged, with no consistent
   link to DFT stability or polymorph/ICSD counts.
6. **The V03 GP is a weaker regressor than RF/GBR** on leave-one-system-out DFT Ef (0.501 vs 0.418 MAE eV/atom). PySR (0.484) is
   not significantly better than the V03 GP.
7. **Most of the "discovery" signal is stoichiometric-template frequency, not learned chemistry.** A counting prior alone
   reaches 0.229, and pooling templates across systems reaches 0.307.
8. **Nested-validation design flaw (Protocol B).** Inner selection used random inner folds, so for family-held-out outer
   folds it picked the template prior, which scores exactly 0 on unseen families. The pre-registered "strongest
   baseline" in Protocol B is therefore not the strongest. Inner folds should have been family-grouped, matching the outer
   protocol. This flaw does not affect Protocol A, the primary analysis.
9. **Protocol E (temporal) is unavailable.** The MP snapshot has ICSD ids but no publication dates, and no proxy dates were invented.
10. **Periodicity/embedding work was not run** in V05. It was exploratory and dropped for time.

## Deviations from V05_RESEARCH_PROTOCOL.md
| # | Deviation | Reason | Effect on conclusions |
|---|---|---|---|
| D1 | H2 tested for two model classes (PU_RF, EHP); Holm over 4 tests | The protocol did not pin the model class | More conservative; none significant either way |
| D2 | H3 unit = system (mean over orders) | Avoids pseudo-replication | Conservative |
| D3 | H3 uses 3 bags/episode (H1 uses 5) | Runtime of 6 arms × 3 orders | Matched across arms; EHP-family arms all low anyway |
| D4 | Leakage controls added: in C, source positives sharing a target-test formula are removed (68 shared formulas); in D, buffer keys are filtered | Discovered during dataset QC | Prevents optimistic bias |
| D5 | Phase 8 regression benchmark added (DFT Ef) | Gives PySR/Roost a fair task (both are regressors) | Exploratory only |
| D6 | Template-prior pooling and rank-mean hybrids evaluated | Emerged from results | Exploratory; requires new pre-registration |
| D7 | GP rule strings print "Ef =" (V03 printer) although the EHP target is the PU label | Cosmetic, inherited | None |
