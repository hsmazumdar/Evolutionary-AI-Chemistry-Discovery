"""Phase 2: build the V05 multi-system dataset from the MP snapshot (V03 outer data folder) + measured enthalpies.
Writes data/entries_<system>.csv (every MP entry in the system, provenance kept), data/formulas_v05.csv (one row per
reduced formula), data/MANIFEST.json (sha256, counts, source). Usage: python scripts/build_dataset.py <outer_data_dir>"""
import os, sys, json, hashlib, re
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(HERE, "data")
SYSTEMS = ["Fe-Na-O-P", "Ba-O-P-V", "K-O-S-V", "H-N-O-S", "Al-Ca-O-Si", "K-Mo-O-P", "B-H-Na-O", "Ba-Fe-O-S", "Mn-O-P-Ti"]
src = sys.argv[1] if len(sys.argv) > 1 else "/workspace/DesignEvolutionaryChemistry/data"
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
mp = pd.read_csv(os.path.join(src, "mp_inorganic_all.csv.gz"))
mp["elset"] = mp.elements.str.split().apply(frozenset)
def red_key(comp):
    c = json.loads(comp); t = sum(c.values()); return json.dumps({k: round(v / t, 6) for k, v in sorted(c.items())})
rows = []; man = {"source_mp": "mp_inorganic_all.csv.gz", "source_mp_sha256": sha(os.path.join(src, "mp_inorganic_all.csv.gz")),
                  "mp_snapshot": str(mp.source.iloc[0]), "systems": {}}
H = pd.read_csv(os.path.join(src, "matminer_expt_formation_enthalpy_kingsbury_inorganic.csv"))
man["source_measured_enthalpy_sha256"] = sha(os.path.join(src, "matminer_expt_formation_enthalpy_kingsbury_inorganic.csv"))
def parse(f):
    d = {}
    for e, n in re.findall(r"([A-Z][a-z]?)([\d.]*)", str(f)): d[e] = d.get(e, 0) + float(n or 1)
    return d
H = H[~H.formula.str.contains(r"\(")].copy(); H["key"] = H.formula.apply(lambda f: json.dumps({k: round(v / sum(parse(f).values()), 6) for k, v in sorted(parse(f).items())}))
Hm = H.groupby("key").agg(measured_dHf_eV_atom=("expt_form_e", "mean"), measured_unc=("uncertainty", "max"), measured_n=("formula", "size")).reset_index()
for s in SYSTEMS:
    E = mp[mp.elset.apply(lambda e: e <= frozenset(s.split("-")))].copy(); E["system"] = s
    E.drop(columns=["elset"]).to_csv(os.path.join(OUT, f"entries_{s}.csv"), index=False)
    E["key"] = E.composition_reduced.apply(red_key); E["obs"] = E.experimentally_observed.astype(str) == "True"
    for k, g in E.groupby("key"):
        o = g[g.obs]; best = g.sort_values("formation_energy_per_atom_eV").iloc[0]
        icsd = sorted({i for v in o.icsd_ids.dropna() for i in str(v).split()})
        rows.append(dict(system=s, key=k, formula=best.formula, nelements=int(best.nelements), formula_anonymous=best.formula_anonymous,
                         composition=k, experimentally_observed=bool(len(o)), n_polymorphs_mp=len(g), n_polymorphs_observed=len(o),
                         n_icsd_unique=len(icsd), icsd_ids=" ".join(icsd), dft_Ef_min_eV_atom=float(g.formation_energy_per_atom_eV.min()),
                         dft_Ef_observed_min_eV_atom=float(o.formation_energy_per_atom_eV.min()) if len(o) else np.nan,
                         dft_ehull_min_eV_atom=float(g.energy_above_hull_eV.min()), material_ids=" ".join(g.material_id)))
F = pd.DataFrame(rows).merge(Hm, on="key", how="left")
F.to_csv(os.path.join(OUT, "formulas_v05.csv"), index=False)
for s in SYSTEMS:
    g = F[F.system == s]; man["systems"][s] = dict(n_formulas=len(g), n_observed=int(g.experimentally_observed.sum()), n_theoretical_only=int((~g.experimentally_observed).sum()),
        n_with_measured_dHf=int(g.measured_dHf_eV_atom.notna().sum()), n_observed_quaternary=int((g.experimentally_observed & (g.nelements == 4)).sum()),
        entries_sha256=sha(os.path.join(OUT, f"entries_{s}.csv")))
man["formulas_v05_sha256"] = sha(os.path.join(OUT, "formulas_v05.csv")); man["n_formulas"] = len(F); man["n_observed"] = int(F.experimentally_observed.sum())
man["n_unique_observed_formulas_across_systems"] = int(F[F.experimentally_observed].key.nunique())
man["publication_dates"] = "UNAVAILABLE: snapshot has ICSD ids but no ICSD collection/publication dates -> Protocol E not run"
json.dump(man, open(os.path.join(OUT, "MANIFEST.json"), "w"), indent=1); print(json.dumps(man, indent=1)[:2500])
