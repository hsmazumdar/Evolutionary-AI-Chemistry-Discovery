# Knowledge memory: Fe-Na-O-P formation energy, split random_split_seed0

_No rule is permanent; every rule can be revised when evidence demands._

17 rules adopted, 16 revisions.

| id | gen | phase | status | nodes | train MAE | rule |
|---|---|---|---|---|---|---|
| R000 | 0 | evolution | superseded | 5 | 0.3696 | `Ef = -0.064 + -0.467 * (sqrt|dev_rCov| * (mean_EN)^2)` |
| R001 | 2 | evolution | superseded | 7 | 0.344 | `Ef = -0.032 + 0.515 * -(((range_EN / mean_rA) * sqrt|mean_EN|))` |
| R002 | 3 | evolution | superseded | 11 | 0.3182 | `Ef = 0.053 + -0.314 * ((sqrt|dev_rCov| * (mean_EN)^2) + (n_elem * sqrt|(dev_EN)^2|))` |
| R003 | 4 | evolution | superseded | 11 | 0.3163 | `Ef = 0.327 + -0.177 * ((sqrt|dev_rCov| * (mean_EN)^2) + (n_elem * (mean_EN + dev_IE)))` |
| R004 | 5 | evolution | superseded | 11 | 0.291 | `Ef = 0.088 + -0.097 * (((dev_rCov / 0.13) * (mean_EN)^2) + (n_elem * sqrt|n_elem|))` |
| R005 | 7 | evolution | superseded | 12 | 0.2865 | `Ef = 0.256 + -0.069 * (((dev_rCov / 0.13) * (mean_EN)^2) + (n_elem * (mean_EN + mean_EN)))` |
| R006 | 8 | evolution | superseded | 7 | 0.2954 | `Ef = 0.514 + -0.357 * ((sqrt|dev_rCov| * (mean_EN)^2) + n_elem)` |
| R007 | 10 | evolution | superseded | 12 | 0.2754 | `Ef = 1.463 + -1.305 * sqrt|(n_elem + (((dev_rCov / mean_rA) * sqrt|n_elem|) * (mean_EN)^2))|` |
| R008 | 14 | evolution | superseded | 11 | 0.2743 | `Ef = 0.974 + -0.943 * sqrt|(n_elem + (((dev_rCov / mean_rA) * n_elem) * (mean_EN)^2))|` |
| R009 | 16 | evolution | superseded | 10 | 0.2717 | `Ef = 0.564 + -0.454 * ((n_elem + ((dev_rCov / mean_rA) * (mean_EN)^2)) + dev_rCov)` |
| R010 | 18 | evolution | superseded | 8 | 0.2756 | `Ef = 0.552 + -0.476 * (n_elem + ((dev_rCov / mean_rA) * (mean_EN)^2))` |
| R011 | 40 | contradiction-driven | superseded | 8 | 0.3114 | `Ef = 0.544 + -0.474 * (n_elem + ((dev_rCov / mean_rA) * (mean_EN)^2))` |
| R012 | 41 | contradiction-driven | superseded | 13 | 0.2813 | `Ef = 1.041 + -0.689 * ((n_elem + ((dev_rCov / mean_rA) * ((mean_nval + range_IE) / range_nval))) + dev_rCov)` |
| R013 | 43 | contradiction-driven | superseded | 11 | 0.279 | `Ef = 1.050 + -0.740 * (n_elem + ((dev_rCov / mean_rA) * ((mean_nval + range_IE) / range_nval)))` |
| R014 | 47 | contradiction-driven | superseded | 9 | 0.2764 | `Ef = 0.853 + -0.597 * (n_elem + ((dev_rCov / mean_rA) * (range_EN / range_nval)))` |
| R015 | 49 | contradiction-driven | superseded | 15 | 0.2474 | `Ef = 1.682 + -0.818 * ((n_elem + ((dev_rCov / mean_rA) * ((mean_nval + range_IE) / range_nval))) + (dev_rCov / range_rCov))` |
| R016 | 51 | contradiction-driven | active | 15 | 0.234 | `Ef = 1.826 + -0.915 * ((n_elem + ((dev_rCov / mean_rA) * ((mean_nval + dev_rCov) / range_nval))) + (dev_rCov / range_rCov))` |

## Current active rule R016

`Ef = 1.826 + -0.915 * ((n_elem + ((dev_rCov / mean_rA) * ((mean_nval + dev_rCov) / range_nval))) + (dev_rCov / range_rCov))`

- Evidence: {'n_training_compounds': 55, 'train_MAE_eV_per_atom': 0.234}
- Confidence: None
- Limits: None
- Contradictions (reliable training compounds this rule mispredicts badly):

## Revision history

- gen 2: R000 -> R001 (lower fitness (error + complexity) found; train MAE 0.3696 -> 0.344)
- gen 3: R001 -> R002 (lower fitness (error + complexity) found; train MAE 0.344 -> 0.3182)
- gen 4: R002 -> R003 (lower fitness (error + complexity) found; train MAE 0.3182 -> 0.3163)
- gen 5: R003 -> R004 (lower fitness (error + complexity) found; train MAE 0.3163 -> 0.291)
- gen 7: R004 -> R005 (lower fitness (error + complexity) found; train MAE 0.291 -> 0.2865)
- gen 8: R005 -> R006 (lower fitness (error + complexity) found; train MAE 0.2865 -> 0.2954)
- gen 10: R006 -> R007 (lower fitness (error + complexity) found; train MAE 0.2954 -> 0.2754)
- gen 14: R007 -> R008 (lower fitness (error + complexity) found; train MAE 0.2754 -> 0.2743)
- gen 16: R008 -> R009 (lower fitness (error + complexity) found; train MAE 0.2743 -> 0.2717)
- gen 18: R009 -> R010 (lower fitness (error + complexity) found; train MAE 0.2717 -> 0.2756)
- gen 40: R010 -> R011 (re-weighted 2 contradicting compounds x3; train MAE 0.2756 -> 0.3114)
- gen 41: R011 -> R012 (re-weighted 2 contradicting compounds x3; train MAE 0.3114 -> 0.2813)
- gen 43: R012 -> R013 (re-weighted 2 contradicting compounds x3; train MAE 0.2813 -> 0.279)
- gen 47: R013 -> R014 (re-weighted 2 contradicting compounds x3; train MAE 0.279 -> 0.2764)
- gen 49: R014 -> R015 (re-weighted 2 contradicting compounds x3; train MAE 0.2764 -> 0.2474)
- gen 51: R015 -> R016 (re-weighted 2 contradicting compounds x3; train MAE 0.2474 -> 0.234)
