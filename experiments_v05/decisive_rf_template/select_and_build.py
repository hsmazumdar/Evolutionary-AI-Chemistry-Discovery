"""Select fresh systems (V05 rule continued; must reproduce the V05 nine) and build their dataset with the V05 builder logic."""
import os, sys, json, hashlib, re
import numpy as np, pandas as pd
D = os.path.dirname(os.path.abspath(__file__)); V05 = os.path.dirname(D); sys.path.insert(0, V05)
from shared.core import SYSTEMS as V05_SYSTEMS
src = "/workspace/DesignEvolutionaryChemistry/data"; sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
R = pd.read_csv(f"{src}/feasibility_ranking_all.csv")
R = R[(R.n_elements == 4) & ~R.system.str.split("-").apply(lambda e: "C" in e)].sort_values(["n_expt_formulas_complete_props", "system"], ascending=[False, True])
acc = ["Fe-Na-O-P"]
for s in R.system:
    if s in acc: continue
    if all(len(set(s.split("-")) & set(a.split("-"))) <= 2 for a in acc): acc.append(s)
    if len(acc) == 18: break
assert acc[:9] == V05_SYSTEMS, "selection rule does not reproduce V05 -> STOP"
FRESH = acc[9:]; print("fresh systems:", FRESH, len(FRESH))
mp = pd.read_csv(f"{src}/mp_inorganic_all.csv.gz"); mp["elset"] = mp.elements.str.split().apply(frozenset)
def red_key(comp):
    c = json.loads(comp); t = sum(c.values()); return json.dumps({k: round(v / t, 6) for k, v in sorted(c.items())})
rows = []; man = dict(source_mp_sha256=sha(f"{src}/mp_inorganic_all.csv.gz"), ranking_sha256=sha(f"{src}/feasibility_ranking_all.csv"), fresh_systems=FRESH, systems={})
for s in FRESH:
    E = mp[mp.elset.apply(lambda e: e <= frozenset(s.split("-")))].copy(); E["system"] = s
    E.drop(columns=["elset"]).to_csv(f"{D}/data/entries_{s}.csv", index=False)
    E["key"] = E.composition_reduced.apply(red_key); E["obs"] = E.experimentally_observed.astype(str) == "True"
    for k, g in E.groupby("key"):
        o = g[g.obs]; best = g.sort_values("formation_energy_per_atom_eV").iloc[0]; icsd = sorted({i for v in o.icsd_ids.dropna() for i in str(v).split()})
        rows.append(dict(system=s, key=k, formula=best.formula, nelements=int(best.nelements), formula_anonymous=best.formula_anonymous, composition=k,
                         experimentally_observed=bool(len(o)), n_polymorphs_mp=len(g), n_polymorphs_observed=len(o), n_icsd_unique=len(icsd), icsd_ids=" ".join(icsd),
                         dft_Ef_min_eV_atom=float(g.formation_energy_per_atom_eV.min()), dft_Ef_observed_min_eV_atom=float(o.formation_energy_per_atom_eV.min()) if len(o) else np.nan,
                         dft_ehull_min_eV_atom=float(g.energy_above_hull_eV.min()), material_ids=" ".join(g.material_id), measured_dHf_eV_atom=np.nan, measured_unc=np.nan, measured_n=np.nan))
    man["systems"][s] = dict(entries_sha256=sha(f"{D}/data/entries_{s}.csv"))
F = pd.DataFrame(rows); F.to_csv(f"{D}/data/formulas_fresh.csv", index=False); man["formulas_fresh_sha256"] = sha(f"{D}/data/formulas_fresh.csv")
json.dump(man, open(f"{D}/data/MANIFEST.json", "w"), indent=1)
# overlap / leakage audit
V = pd.read_csv(os.path.join(V05, "data", "formulas_v05.csv")); A = pd.concat([V, F]); obs = A[A.experimentally_observed & (A.nelements >= 2)]
aud = []
for s in FRESH:
    k = set(obs[obs.system == s].key); kv = set(obs[obs.system.isin(V05_SYSTEMS)].key); kf = set(obs[obs.system.isin(FRESH) & (obs.system != s)].key)
    aud.append(dict(system=s, observed_multi=len(k), shared_with_V05=len(k & kv), shared_with_other_fresh=len(k & kf), shared_any=len(k & (kv | kf)), quaternary_observed=int(((obs.system == s) & (obs.nelements == 4)).sum())))
pd.DataFrame(aud).to_csv(f"{D}/results/overlap_audit.csv", index=False); print(pd.DataFrame(aud).to_string())
