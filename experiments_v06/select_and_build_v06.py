"""V06 E1: select accepted systems #39-#118 with the V05 greedy rule (PREREG_V06 s1) and build their dataset with the
V05/replication builder logic (unchanged). Asserts that #1-38 reproduce the V05 primary, decisive and replication sets."""
import os, sys, json, hashlib
import numpy as np, pandas as pd
D = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(D); V05 = os.path.join(ROOT, "experiments_v05"); sys.path.insert(0, V05)
from shared.core import SYSTEMS as V05_SYSTEMS
src = "/workspace/DesignEvolutionaryChemistry/data"; sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
EXP = {"mp": "20b221933a314aeee1113b789985e055db7a744b373c3d9c63bd62d00988f7c3", "rank": "33063286ca1617089d3f39a1bdb7be0b76bd686d8d4af42e69d4200b2089743b"}
assert sha(f"{src}/mp_inorganic_all.csv.gz") == EXP["mp"] and sha(f"{src}/feasibility_ranking_all.csv") == EXP["rank"], "input hash mismatch -> STOP"
R = pd.read_csv(f"{src}/feasibility_ranking_all.csv")
R = R[(R.n_elements == 4) & ~R.system.str.split("-").apply(lambda e: "C" in e)].sort_values(["n_expt_formulas_complete_props", "system"], ascending=[False, True])
acc = ["Fe-Na-O-P"]
for s in R.system:
    if s in acc: continue
    if all(len(set(s.split("-")) & set(a.split("-"))) <= 2 for a in acc): acc.append(s)
    if len(acc) == 118: break
DEC = json.load(open(os.path.join(V05, "decisive_rf_template", "data", "MANIFEST.json")))["fresh_systems"]
REP = json.load(open(os.path.join(V05, "replication_rf_template", "data", "MANIFEST.json")))["fresh_systems"]
assert acc[:9] == V05_SYSTEMS and acc[9:18] == DEC and acc[18:38] == REP, "selection rule does not reproduce systems 1-38 -> STOP"
print("systems 1-38 reproduce: OK")
if "--verify-only" in sys.argv: sys.exit(0)
FRESH = acc[38:118]; assert len(FRESH) == 80; print("V06 systems:", len(FRESH))
mp = pd.read_csv(f"{src}/mp_inorganic_all.csv.gz"); mp["elset"] = mp.elements.str.split().apply(frozenset)
def red_key(comp):
    c = json.loads(comp); t = sum(c.values()); return json.dumps({k: round(v / t, 6) for k, v in sorted(c.items())})
rows = []; man = dict(source_mp_sha256=EXP["mp"], ranking_sha256=EXP["rank"], fresh_systems=FRESH, systems={})
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
F = pd.DataFrame(rows); F.to_csv(f"{D}/data/formulas_v06.csv", index=False); man["formulas_v06_sha256"] = sha(f"{D}/data/formulas_v06.csv")
json.dump(man, open(f"{D}/data/MANIFEST.json", "w"), indent=1)
V = pd.concat([pd.read_csv(os.path.join(V05, "data", "formulas_v05.csv"))] + [pd.read_csv(os.path.join(V05, d, "data", "formulas_fresh.csv")) for d in ("decisive_rf_template", "replication_rf_template")])
obs = pd.concat([V, F]); obs = obs[obs.experimentally_observed & (obs.nelements >= 2)]; kv = set(obs[obs.system.isin(V.system.unique())].key)
aud = [dict(system=s, observed_multi=len(k := set(obs[obs.system == s].key)), shared_with_v05_38=len(k & kv),
            shared_with_other_v06=len(k & set(obs[obs.system.isin(FRESH) & (obs.system != s)].key)), quaternary_observed=int(((obs.system == s) & (obs.nelements == 4)).sum())) for s in FRESH]
pd.DataFrame(aud).to_csv(f"{D}/results/overlap_audit.csv", index=False); print("audit written (labels only, no model outputs)")
