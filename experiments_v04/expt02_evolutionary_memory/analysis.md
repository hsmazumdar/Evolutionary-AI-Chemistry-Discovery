# Expt-02 analysis

| stream / method | final MAE [95% CI] | forgetting dom.0 | 90% coverage | memory items | fitness evals |
|---|---|---|---|---|---|
| chem / scratch retrain | 0.311 [0.286, 0.341] | 0.133 | 0.80 | 55 samples | 5.0e5 |
| chem / sequential GP | 0.813 [0.672, 0.990] | 1.318 | 0.18 | 1 rule | 2.2e5 |
| chem / replay GP | 0.432 [0.359, 0.547] | 0.472 | 0.58 | 13 | 3.2e5 |
| chem / V03 archive | **0.286 [0.261, 0.313]** | **0.055** | 0.82 | 58 | 5.0e5 |
| chem / **proposed memory** | 0.399 [0.351, 0.452] | 0.347 | 0.63 | 27 | 3.2e5 |
| random / scratch | 0.311 | – | 0.80 | 55 | 4.4e5 |
| random / sequential | 0.379 | – | 0.67 | 1 | 2.2e5 |
| random / replay | 0.341 | – | 0.77 | 13 | 3.2e5 |
| random / V03 archive | **0.305** | – | 0.81 | 58 | 4.4e5 |
| random / **proposed** | 0.317 [0.304, 0.334] | – | 0.79 | 27 | 3.2e5 |

Paired (30 runs, Holm across 20 tests), proposed − X, final MAE:
chemical: vs sequential −0.414 (p<1e-4); vs replay −0.033 [−0.153, +0.060] (n.s.); vs scratch +0.089 (Holm p=0.002);
vs V03 archive +0.113 (Holm p<1e-4). Random: vs sequential −0.062 (Holm p=0.005); vs replay −0.024 (p=0.025, Holm 0.25);
vs scratch +0.006 (n.s.); vs V03 archive +0.012 (n.s.).

## Interpretation
- With the same bounded replay buffer, competing-hypothesis memory is no better than plain replay on the chemical stream
  and slightly better on the random stream (not significant after correction). It strongly beats naive sequential GP.
- Methods that keep **all** past data (scratch, V03 archive) are best; their memory cost is ~2× in stored items and
  ~1.6× in fitness evaluations. The comparison is therefore a memory/compute trade-off, not a win.
- Calibration of the proposed memory is poor on the distribution-shifting chemical stream (63% coverage of nominal
  90%): ensemble spread of similar GP rules underestimates uncertainty under shift.
- The memory performs ~10 revisions per run, i.e. it is *active* but the revisions do not prevent forgetting.

**Verdict H2: NOT supported** as an accuracy/forgetting improvement; partially useful as a cheaper-than-full-retraining
memory on random streams. Revisable memory remains valuable as an *interpretability/provenance* device (rules.json), not
as demonstrated performance.
