# Pre-registration V06: scale-up, stronger baselines, novel-only scoring, temporal split
Status: APPROVED by the author 2026-10-21 22:15 IST; committed as drafted (only the frozen-hash block below was filled in, as Section 0 requires). Becomes binding when committed to `research-v05` (or a new `research-v06` branch cut from it; never `main`/`research-v04`) and archived as a Zenodo release **before** any V06 system is built or any V06 model is run.
Author: Himanshu S. Mazumdar (conceived and directed). Code developed with AI assistance.
Prepared 2026-10-21 (IST).

## 0. Fixed inputs (frozen before any V06 run)
- **Data:** Materials Project summary 2025-09-25 (`/workspace/DesignEvolutionaryChemistry/data/mp_inorganic_all.csv.gz`) and `feasibility_ranking_all.csv`. Their SHA-256 is recorded in the commit.
- **E2 adds:** MP provenance collection 2025-09-25 from the public AWS Open Data bucket `materialsproject-build/collections/2025-09-25/provenance/`. Its manifest SHA-256 is recorded at download.
- **Labels (unchanged):** observed = at least one ICSD-linked entry. Unit = reduced formula. Candidate space = 2–4 of the system's elements, ≤30 atoms per formula unit.
- **Code:** V05 replication pipeline (`experiments_v05/replication_rf_template`, `shared/core.py`), unchanged except for the new arms listed below. The exact commit hash goes here at commit time.
- **Global seed:** 20261021. Split seeds s1–s5 are derived exactly as in V05. Bootstrap uses 10,000 resamples with seed 20261021.

### Frozen hashes (filled at commit)
- mp_inorganic_all.csv.gz SHA-256: 20b221933a314aeee1113b789985e055db7a744b373c3d9c63bd62d00988f7c3
- feasibility_ranking_all.csv SHA-256: 33063286ca1617089d3f39a1bdb7be0b76bd686d8d4af42e69d4200b2089743b
- Code base: research-v05 @ 624ee13 (V06 arms are added in later commits on research-v06)
- Provenance manifest SHA-256: recorded at download time in experiments_v06/data/MANIFEST.json

## 1. System selection (E1), fixed rule, no outcome data consulted
- **Rule:** the V05 greedy rule (4-element, carbon-free, sorted by `n_expt_formulas_complete_props` desc then name, accepted if it shares ≤2 elements with every accepted system). It is continued past the 38 already used.
- **Systems:** accepted systems **#39 to #118 (80 systems)**.
- **Safety assert:** the script must reproduce systems #1–38 exactly, otherwise STOP.
- **Pre-lock check:** only the count of eligible systems (782) and the observed-count thresholds were inspected before lock (#39 has 56 observed formulas; #99 has 47). No names, no labels, no model outputs.
- **Leakage audit:** observed formulas shared with systems #1–38 are reported. Primary analysis keeps them (as in V05). The strict variant removes them from the test sets and is secondary.

## 2. Arms
**A. Reference arms (unchanged from V05):**
- TPOOL (pooled template counts, pooled over all other systems in the same study).
- Target-only template prior.
- PU-RF (primitive element features).
- BLEND (rank blend RF + TPOOL, w chosen by family-grouped inner validation over {0, 0.1, …, 1}).
- SynthNN-style PU.
- Random.

**B. E3-light learned baselines (new, primitive inputs only):**
- **B1** Magpie-statistics + gradient-boosting PU (same bagging as PU-RF).
- **B2** Roost-style composition network, PU-trained. CPU; fixed hyper-parameters stated in code before the run, no tuning on test.
- **B3** Each of B1 and B2 blended with TPOOL, w by the same inner validation.

**C. Domain-knowledge ablations (labelled as such; never in a confirmatory test):**
- **C1** Charge-neutrality filter (pymatgen oxidation-state guesses) applied to TPOOL.
- **C2** Hautier-style ionic substitution probability model.

## 3. Hypotheses (confirmatory; unit = chemical system, n = 80; values are means over 5 splits per system)
- **H6.1** (core replication): BLEND > TPOOL, recall@100 (tie-fair expected recall). One-sided Wilcoxon signed-rank, Pratt zero handling. Margin: mean diff ≥ 0.02.
- **H6.2:** BLEND > TPOOL, recall@500 (same test).
- **H6.3** (hard baseline): TPOOL ≥ best learned non-template arm (max of PU-RF, B1, B2, SynthNN-style), recall@100. Tested as best-learned − TPOOL < 0, i.e. one-sided, with the learned arm that is best on the **inner validation folds** fixed per system (not chosen on test).
- **H6.4** (novel-only, E4): on novel-only test positives (Section 4), BLEND > TPOOL at recall@500.

**Correction:** Holm across H6.1–H6.4 (4 tests), α = 0.05.

**Success rule:** a hypothesis is supported only if the Holm-adjusted p < 0.05 **and** the mean difference ≥ 0.02 **and** the 95% system-cluster bootstrap CI excludes 0. Otherwise it is reported as "not supported" in the main text.

**Pre-stated interpretation:** If H6.1 fails, the paper's headline becomes "a learned RF adds nothing reliable to pooled templates at scale", and V05's p = 0.047 is reported as not replicated.

## 4. E4: novel-only scoring
- **Definition:** a test positive is *novel* if it is ternary or quaternary **and** its anonymous formula/template has no observed instance among the training positives of the same system with the same element subset.
- **Scoring:** recall@k is computed over novel positives only (k = 100, 500, 1000). Non-novel test positives are removed from the ranked list before scoring, as training positives are.
- **Minimum data:** systems with < 3 novel test positives (summed over splits) are excluded from H6.4. The count is reported. If fewer than 30 systems remain, H6.4 is downgraded to exploratory (decided mechanically, before seeing scores).
- Quaternary-only recall@1000 is reported descriptively.

## 5. E2: temporal split (feasible; see feasibility note)
- **First-report year:** for each observed formula, the minimum `year` across the non-MP bibtex `references` of all its ICSD-linked provenance entries. The MP methodology references (e.g. Jain2013) are excluded by key/DOI list.
  - Formulas with no year are excluded from the temporal train and test sets and counted.
- **Split:** train = observed with year ≤ 2010; test = observed with year 2011–2025. Systems = the same 80. Systems with < 5 test positives are excluded (count reported).
  - The cut-off of 2010 is fixed now and is not tuned.
- **Hypothesis H6.5** (separate family; own α = 0.05, not Holm-pooled with H6.1–4): on the temporal split, BLEND > TPOOL at recall@100. Same test, margin and CI rule.
- **Descriptive:** all arms at k = 100/500/1000; per-arity recall.
- **Caveat stated in advance:** this is retrospective, and year labels reflect the reference set MP holds, not necessarily the true first report.

## 6. Secondary / exploratory (reported, uncorrected)
- k = 10/50/1000.
- MRR.
- Precision@100 (lower bound).
- Strict leakage variant.
- Per-arity results.
- C1/C2 ablations.
- Pooled V05+V06 (109 systems).
- The stable (enumeration-order) tie rule versus the fair rule.

## 7. Stopping and integrity rules
- No outcome on any V06 system is computed before this file is committed and archived.
- **Pilot:** a pipeline smoke test is allowed only on V05 systems #1–9 (already unsealed) to check that the new arms run. Pilot numbers are not reported as results.
- **Fixed design:** the analysis is one-shot. There is no optional stopping, no adding systems, and no changing k, margins, w grid or features after the run starts.
- **Crashes:** if a run crashes, it is fixed and rerun on the same seeds; every crash/fix is logged. If an arm cannot run on > 10% of systems, it is reported as failed and excluded from H6.3 (decided before seeing its scores).
- **Deviations** are logged in `DEVIATIONS.md` with date and reason, and disclosed in the paper.
- **Reporting:** all hypotheses are reported regardless of outcome. Negative results stay in the main text.

## 8. Compute estimate (box: 8 CPU, 15 GB RAM, no GPU)
- **Reference arms:** V05 replication cost × 4 (80 vs 20 systems), roughly 1–2 days of CPU.
- **B1:** similar to PU-RF.
- **B2 (Roost-style, CPU):** the largest cost, estimated 2–4 days. Option: a small fixed architecture, or run on the user's PC if it has a GPU.
- **E2:** one extra full pass (~1–2 days) plus a ~1 h provenance download.
- **Total:** about 5–9 days wall-clock.
