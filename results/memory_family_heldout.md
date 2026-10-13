# Knowledge memory: Fe-Na-O-P formation energy, split family_heldout

_No rule is permanent; every rule can be revised when evidence demands._

14 rules adopted, 13 revisions.

| id | gen | phase | status | nodes | train MAE | rule |
|---|---|---|---|---|---|---|
| R000 | 0 | evolution | superseded | 3 | 0.3915 | `Ef = -0.592 + 0.617 * (mean_rCov - n_elem)` |
| R001 | 1 | evolution | superseded | 7 | 0.3399 | `Ef = -0.725 + 0.343 * ((mean_rho / dev_mass) - (n_elem + 1.83))` |
| R002 | 2 | evolution | superseded | 4 | 0.3487 | `Ef = 1.222 + -0.547 * (n_elem - -(mean_EN))` |
| R003 | 3 | evolution | superseded | 9 | 0.3215 | `Ef = -1.019 + -0.303 * ((mean_IE)^2 + (n_elem + -((mean_rho / dev_mass))))` |
| R004 | 5 | evolution | superseded | 9 | 0.276 | `Ef = 1.744 + 0.411 * (-((n_elem + mean_EN)) + -((dev_EN / dev_IE)))` |
| R005 | 6 | evolution | superseded | 8 | 0.2751 | `Ef = 0.615 + -0.483 * ((dev_EN / dev_IE) + (n_elem + -(mean_rA)))` |
| R006 | 9 | evolution | superseded | 7 | 0.276 | `Ef = 1.744 + -0.411 * ((dev_EN / dev_IE) + (n_elem + mean_EN))` |
| R007 | 31 | evolution | superseded | 7 | 0.2722 | `Ef = 2.303 + -0.615 * (n_elem + ((dev_EN / range_IE) + mean_EN))` |
| R008 | 32 | evolution | superseded | 11 | 0.2537 | `Ef = 1.853 + -0.872 * (mean_nval + (((dev_rCov / range_nval) / (dev_rCov / dev_rCov)) + n_elem))` |
| R009 | 40 | contradiction-driven | superseded | 11 | 0.2709 | `Ef = 1.863 + -0.880 * (mean_nval + (((dev_rCov / range_nval) / (dev_rCov / dev_rCov)) + n_elem))` |
| R010 | 41 | contradiction-driven | superseded | 9 | 0.2746 | `Ef = 1.530 + -0.921 * (((dev_rCov / range_nval) / (dev_rCov / dev_rCov)) + n_elem)` |
| R011 | 47 | contradiction-driven | superseded | 7 | 0.2741 | `Ef = 1.480 + -0.884 * (((dev_rCov / range_nval) / 0.9) + n_elem)` |
| R012 | 49 | contradiction-driven | superseded | 5 | 0.2746 | `Ef = 1.530 + -0.921 * ((dev_rCov / range_nval) + n_elem)` |
| R013 | 58 | contradiction-driven | active | 7 | 0.2612 | `Ef = 1.904 + -0.784 * (((dev_rCov / range_nval) + mean_IE) + n_elem)` |

## Current active rule R013

`Ef = 1.904 + -0.784 * (((dev_rCov / range_nval) + mean_IE) + n_elem)`

- Evidence: {'n_training_compounds': 57, 'train_MAE_eV_per_atom': 0.2612}
- Confidence: None
- Limits: None
- Contradictions (reliable training compounds this rule mispredicts badly):

## Revision history

- gen 1: R000 -> R001 (lower fitness (error + complexity) found; train MAE 0.3915 -> 0.3399)
- gen 2: R001 -> R002 (lower fitness (error + complexity) found; train MAE 0.3399 -> 0.3487)
- gen 3: R002 -> R003 (lower fitness (error + complexity) found; train MAE 0.3487 -> 0.3215)
- gen 5: R003 -> R004 (lower fitness (error + complexity) found; train MAE 0.3215 -> 0.276)
- gen 6: R004 -> R005 (lower fitness (error + complexity) found; train MAE 0.276 -> 0.2751)
- gen 9: R005 -> R006 (lower fitness (error + complexity) found; train MAE 0.2751 -> 0.276)
- gen 31: R006 -> R007 (lower fitness (error + complexity) found; train MAE 0.276 -> 0.2722)
- gen 32: R007 -> R008 (lower fitness (error + complexity) found; train MAE 0.2722 -> 0.2537)
- gen 40: R008 -> R009 (re-weighted 1 contradicting compounds x3; train MAE 0.2537 -> 0.2709)
- gen 41: R009 -> R010 (re-weighted 1 contradicting compounds x3; train MAE 0.2709 -> 0.2746)
- gen 47: R010 -> R011 (re-weighted 1 contradicting compounds x3; train MAE 0.2746 -> 0.2741)
- gen 49: R011 -> R012 (re-weighted 1 contradicting compounds x3; train MAE 0.2741 -> 0.2746)
- gen 58: R012 -> R013 (re-weighted 1 contradicting compounds x3; train MAE 0.2746 -> 0.2612)
