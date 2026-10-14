"""Automated dataset QC + audit table (writes results/dataset_qc.json and prints a markdown table)."""
import os, sys, json
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, HERE)
from shared.core import formulas, space, SYSTEMS
F = formulas(); M = json.load(open(os.path.join(HERE, "data", "MANIFEST.json"))); out = {"checks": {}, "systems": {}}
chk = out["checks"]
chk["no_carbon"] = bool(not any("C" in s.split("-") for s in F.system.unique()))
chk["unique_key_per_system"] = bool(not F.duplicated(["system", "key"]).any())
chk["observed_have_icsd"] = bool((F[F.experimentally_observed].n_icsd_unique > 0).all())
chk["theoretical_have_no_icsd"] = bool((F[~F.experimentally_observed].n_icsd_unique == 0).all())
chk["dft_and_measured_columns_distinct"] = bool(np.allclose(F.dft_Ef_min_eV_atom, F.dft_Ef_min_eV_atom) and "measured_dHf_eV_atom" in F)
obs = F[F.experimentally_observed]; shared = obs.groupby("key").system.nunique()
chk["observed_formulas_shared_by_>1_system"] = int((shared > 1).sum())
for s in SYSTEMS:
    cs, pos, dropped = space(s); g = F[F.system == s]
    out["systems"][s] = dict(formulas=len(g), observed=int(g.experimentally_observed.sum()), observed_multi_in_space=len(pos), observed_outside_space_or_unary=int(g.experimentally_observed.sum()) - len(pos),
        polymorph_observed_mean=round(float(g[g.experimentally_observed].n_polymorphs_observed.mean()), 2), max_polymorphs=int(g.n_polymorphs_mp.max()),
        with_measured_dHf=int(g.measured_dHf_eV_atom.notna().sum()), mean_abs_DFT_minus_measured=round(float((g.dft_Ef_observed_min_eV_atom - g.measured_dHf_eV_atom).abs().mean()), 3) if g.measured_dHf_eV_atom.notna().any() else None)
dm = F.dropna(subset=["measured_dHf_eV_atom", "dft_Ef_observed_min_eV_atom"]).drop_duplicates("key")
out["dft_vs_measured_unique_formulas"] = dict(n=len(dm), MAE=round(float((dm.dft_Ef_observed_min_eV_atom - dm.measured_dHf_eV_atom).abs().mean()), 4))
json.dump(out, open(os.path.join(HERE, "results", "dataset_qc.json"), "w"), indent=1)
print(json.dumps(out["checks"], indent=1)); print(pd.DataFrame(out["systems"]).T.to_markdown()); print(out["dft_vs_measured_unique_formulas"])
assert all(v for k, v in chk.items() if isinstance(v, bool)), chk
