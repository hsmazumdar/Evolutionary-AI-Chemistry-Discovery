"""Independent MEASURED-property validation (kept separate from DFT targets).
Data (copied into ./data, from matminer, see ../../../DATA_CREDITS.md / outer data README):
  * expt_formation_enthalpy_kingsbury: MEASURED formation enthalpy, eV/atom, with reported uncertainty where available.
  * expt_gap: MEASURED band gap, eV.
Analyses: (1) DFT-trained Fe-Na-O-P models scored against measured enthalpies of Fe-Na-O-P-system compounds (cross-target,
reported as such); (2) models trained on measured enthalpies with chemical-system-grouped 5-fold CV;
(3) same for measured band gaps. Duplicated formulas are averaged once (not counted as independent).  python reproduce.py [--quick]"""
import os, sys, json, time, argparse
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from shared.common import load_poc, parse_formula, featurize, mae, boot_ci, paired, provenance, write_yaml, GP, sha256
from sklearn.linear_model import RidgeCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
ap = argparse.ArgumentParser(); ap.add_argument("--quick", action="store_true"); A = ap.parse_args()
CFG = dict(folds=5, gp_pop=200, gp_gens=40, evo_seeds=[0, 1, 2], rf_trees=300)
if A.quick: CFG.update(gp_pop=40, gp_gens=4, evo_seeds=[0], rf_trees=50)
P = load_poc(); el = P["el"]; SRC = {"Fe", "Na", "O", "P"}

def prep(path, col, unc=None):
    d = pd.read_csv(path); d["comp"] = d.formula.apply(parse_formula)
    d = d[d.comp.apply(lambda c: len(c) > 0 and all(e in el.index for e in c))]
    d["key"] = d.comp.apply(lambda c: str(sorted((k, round(v / sum(c.values()), 4)) for k, v in c.items())))
    agg = {col: "mean", "formula": "first", "comp": "first"}
    if unc: agg[unc] = "max"
    g = d.groupby("key").agg(agg).reset_index(); g["n_records"] = d.groupby("key").size().values
    rowsX = [featurize([c], el) for c in g.comp]; names = rowsX[0][1]; X = np.vstack([r[0] for r in rowsX]); ok = np.isfinite(X).all(1)  # per-row: V03 featurize propagates NaN of any element in the batch
    g = g[ok].reset_index(drop=True); X = X[ok]
    g["chemsys"] = g.comp.apply(lambda c: "-".join(sorted(c)))
    return g, X, names

def grouped_cv(g, X, names, target, label):
    rows, preds = [], []; y = g[target].values; groups = g.chemsys.values
    for f, (tr, te) in enumerate(GroupKFold(CFG["folds"]).split(X, y, groups)):
        out = {"mean": np.full(len(te), y[tr].mean()),
               "ridge": make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-3, 3, 13))).fit(X[tr], y[tr]).predict(X[te])}
        for s in CFG["evo_seeds"]:
            out[f"RF_seed{s}"] = RandomForestRegressor(CFG["rf_trees"], min_samples_leaf=2, random_state=s, n_jobs=8).fit(X[tr], y[tr]).predict(X[te])
            gp = GP(names, pop_size=CFG["gp_pop"], generations=CFG["gp_gens"], seed=s).fit(X[tr], y[tr]); out[f"GP_seed{s}"] = gp.predict(X[te])
        for m, p in out.items():
            rows.append(dict(target=label, fold=f, model=m.split("_seed")[0], seed=m.split("_seed")[1] if "_seed" in m else None, n_test=len(te), MAE=mae(p, y[te])))
            preds.extend(dict(target=label, fold=f, model=m, formula=g.formula[i], y_measured=float(y[i]), y_pred=float(q)) for i, q in zip(te, p))
    return rows, preds

if __name__ == "__main__":
    T0 = time.time()
    H, XH, nH = prep(os.path.join(HERE, "data", "matminer_expt_formation_enthalpy_kingsbury_inorganic.csv"), "expt_form_e", "uncertainty")
    G, XG, nG = prep(os.path.join(HERE, "data", "matminer_expt_gap_inorganic.csv"), "gap expt")
    # (1) cross-target check inside Fe-Na-O-P
    inS = np.array([set(c) <= SRC for c in H.comp], bool)
    poc = P["df"].copy(); poc["key"] = [str(sorted((k, round(v / sum(c.values()), 4)) for k, v in c.items())) for c in P["comps"]]
    Hs = H[inS].copy().reset_index(drop=True); Hs["formation_energy_per_atom_eV"] = Hs["key"].map(dict(zip(poc["key"], poc["formation_energy_per_atom_eV"])))
    rid = make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-3, 3, 13))).fit(P["X"], P["y"])
    gps = [GP(P["names"], pop_size=CFG["gp_pop"], generations=CFG["gp_gens"], seed=s).fit(P["X"], P["y"]) for s in CFG["evo_seeds"]]
    Xs = XH[inS]; cross = dict(n_measured_in_FeNaOP=int(inS.sum()), n_matched_to_MP_formula=int(Hs.formation_energy_per_atom_eV.notna().sum()))
    m = Hs.formation_energy_per_atom_eV.notna()
    cross["MAE_MP_DFT_vs_measured_matched"] = mae(Hs.formation_energy_per_atom_eV[m], Hs.expt_form_e[m])
    cross["MAE_ridge_trainedOnDFT_vs_measured"] = mae(rid.predict(Xs), Hs.expt_form_e)
    cross["MAE_GP_trainedOnDFT_vs_measured_mean_over_seeds"] = float(np.mean([mae(g.predict(Xs), Hs.expt_form_e) for g in gps]))
    cross["note"] = "Models trained on ALL 91 DFT values incl. these formulas; this measures DFT->experiment target mismatch, not generalisation."
    Hs.drop(columns=["comp", "key"]).to_csv(os.path.join(HERE, "FeNaOP_measured_vs_DFT.csv"), index=False)
    # (2)+(3)
    r1, p1 = grouped_cv(H, XH, nH, "expt_form_e", "measured_formation_enthalpy_eV_per_atom")
    r2, p2 = grouped_cv(G, XG, nG, "gap expt", "measured_band_gap_eV")
    M = pd.DataFrame(r1 + r2); M.to_csv(os.path.join(HERE, "metrics.csv"), index=False); pd.DataFrame(p1 + p2).to_csv(os.path.join(HERE, "predictions.csv"), index=False)
    S = []
    for (t, mm), g in M.groupby(["target", "model"]):
        a, lo, hi = boot_ci(g.groupby("fold").MAE.mean()); S.append(dict(target=t, model=mm, MAE=round(a, 4), CI_lo=round(lo, 4), CI_hi=round(hi, 4)))
    S = pd.DataFrame(S); S.to_csv(os.path.join(HERE, "summary.csv"), index=False)
    T = {}
    for t, g in M.groupby("target"):
        pv = g.groupby(["fold", "model"]).MAE.mean().unstack()
        T[t] = {f"GP - {c}": paired(pv["GP"], pv[c]) for c in ["ridge", "RF", "mean"]}
    json.dump(dict(cross_target=cross, paired=T, n=dict(enthalpy=len(H), gap=len(G), enthalpy_with_uncertainty=int(H.uncertainty.notna().sum()),
              median_reported_uncertainty=float(H.uncertainty.median()))), open(os.path.join(HERE, "results.json"), "w"), indent=1)
    write_yaml(os.path.join(HERE, "config.yaml"), dict(CFG, data_sha256={f: sha256(os.path.join(HERE, "data", f)) for f in os.listdir(os.path.join(HERE, "data"))}, provenance=provenance()))
    print(json.dumps(cross, indent=1)); print(S.to_string()); print(json.dumps(T, indent=1)[:1500]); print("runtime", time.time() - T0)
