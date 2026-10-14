# Expt-02 — Versioned competing-hypothesis memory

**Hypothesis.** A memory that keeps several competing, versioned rules (revised, retired, confidence-weighted) learns
incrementally with less forgetting and better calibration than single-rule or no-memory learners.

`shared/memory_v04.py` (new module; V03 `evochem/memory.py` untouched). Each hypothesis: tree, versions (refitted
coefficients per episode), MAE evidence, confidence ∝ exp(−MAE/τ), status active/retired (never deleted), revision log.
Prediction = confidence-weighted mean of top-3; predictive sd = ensemble spread ⊕ 1.25·best MAE.

Episode streams over each training partition: **chemical** (E1 elements+binaries, E2 ternaries, E3 quaternaries) and
**random** (3 equal random chunks). Every method: 20 GP generations × pop 200 per episode.
Methods: scratch retraining on all data seen; sequential GP (new episode only); replay GP (new + 12-sample buffer);
V03 archive (continue on all data, V03 single-active-rule KnowledgeMemory); proposed (new + same 12-sample buffer + memory).
10 random splits × 3 seeds × 2 streams. Measures: per-episode test MAE, forgetting (MAE on test elements/binaries after E3 −
after E1), forward transfer (MAE on quaternary test items before E3), revisions, 90% interval coverage, memory items,
fitness evaluations.
