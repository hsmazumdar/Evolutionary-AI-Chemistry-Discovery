"""Expt-06 (Stage-1 core): baselines on identical splits. Hyperparameters by inner CV on the training partition only.
python reproduce.py [--quick]. Ablations of Stage-1 components are taken from expt01 (same runs) and summarised here."""
import os, sys, json, time, argparse, warnings
from multiprocessing import Pool
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
from shared.common import load_poc, load_splits, reliability, mae, boot_ci, paired, holm, provenance, write_yaml, GP, SPLITDIR
from shared.twopop import fit_two_population, predict_two_population
from sklearn.linear_model import RidgeCV, LassoCV
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import GridSearchCV, KFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
warnings.filterwarnings("ignore")
ap = argparse.ArgumentParser(); ap.add_argument("--quick", action="store_true"); A = ap.parse_args()
CFG = dict(evo_seeds=[0, 1, 2], gp_pop=300, gp_gens=40, inner_cv_folds=5,
           twopop=dict(pop=200, gens_G=40, gens_S=20, inner_val_frac=0.25, archive_k=10, contradiction_frac=0.15, min_contradictions=4, gate_depth=2, gate_min_leaf=2, accept_margin=0.005))
if A.quick: CFG.update(evo_seeds=[0], gp_pop=50, gp_gens=5); CFG["twopop"].update(pop=50, gens_G=5, gens_S=4)
P = load_poc(); X, Xo, y, df = P["X"], P["Xo"], P["y"], P["df"]; REL = reliability(df)
SPL = load_splits(df); SPL["quaternary_heldout"] = {k: np.array(v) for k, v in json.load(open(os.path.join(SPLITDIR, "group_heldout_quaternary.json"))).items() if k in ("train", "test")}
if A.quick: SPL = {k: SPL[k] for k in ["random_split_seed0", "groupfold0"]}

def models(seed, cv):
    return {
        "ridge": make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-3, 3, 13))),
        "sparse_lasso_expanded (SISSO-like)": make_pipeline(StandardScaler(), PolynomialFeatures(2, include_bias=False), StandardScaler(), LassoCV(cv=cv, random_state=seed, max_iter=20000)),
        "random_forest": GridSearchCV(RandomForestRegressor(n_estimators=300, random_state=seed), {"min_samples_leaf": [1, 3, 5], "max_features": [0.33, 1.0]}, cv=cv, scoring="neg_mean_absolute_error"),
        "gradient_boosting": GridSearchCV(GradientBoostingRegressor(random_state=seed), {"n_estimators": [100, 300], "max_depth": [2, 3], "learning_rate": [0.05, 0.1]}, cv=cv, scoring="neg_mean_absolute_error"),
        "mlp": GridSearchCV(make_pipeline(StandardScaler(), MLPRegressor(hidden_layer_sizes=(32, 32), max_iter=3000, random_state=seed)), {"mlpregressor__alpha": [1e-3, 1e-2, 1e-1, 1.0]}, cv=cv, scoring="neg_mean_absolute_error")}

def job(arg):
    sname, seed = arg; tr, te = SPL[sname]["train"], SPL[sname]["test"]; cv = KFold(CFG["inner_cv_folds"], shuffle=True, random_state=seed)
    rows, preds = [], []
    def rec(name, p, t, nodes=None):
        rows.append(dict(split=sname, evo_seed=seed, model=name, n_test=len(te), test_MAE=mae(p, y[te]), runtime_s=t, complexity_nodes=nodes))
        preds.extend(dict(split=sname, evo_seed=seed, model=name, sample_idx=int(i), y_DFT=float(y[i]), y_pred=float(q)) for i, q in zip(te, p))
    rec("mean_predictor", np.full(len(te), y[tr].mean()), 0.0)
    for n, m in models(seed, cv).items():
        if n == "ridge" and seed != CFG["evo_seeds"][0]: continue  # deterministic
        if n.startswith("sparse") and seed != CFG["evo_seeds"][0]: continue
        t = time.time(); m.fit(X[tr], y[tr]); rec(n, m.predict(X[te]), time.time() - t)
    t = time.time(); g = GP(P["names"], pop_size=CFG["gp_pop"], generations=CFG["gp_gens"], seed=seed).fit(X[tr], y[tr]); rec("V03_GP", g.predict(X[te]), time.time() - t, len(g.best))
    t = time.time(); md, info, _ = fit_two_population(X, Xo, y, REL, tr, seed, CFG["twopop"], P["names"], P["names_o"])
    pg = md["G"].predict(X[te])
    if md["accepted"]:
        d = md["gate"].predict(X[te]).astype(bool); ps = md["S"].predict(md["XX"][te]); pg = np.where(d, ps if md["mode"] == "replace" else 0.5 * (pg + ps), pg)
    rec("proposed_two_population", pg, time.time() - t, info["G_nodes"] + (info["S_nodes"] if info["accepted"] else 0))
    return rows, preds

if __name__ == "__main__":
    T0 = time.time(); jobs = [(s, e) for s in SPL for e in CFG["evo_seeds"]]
    with Pool(8) as pool: res = pool.map(job, jobs)
    M = pd.DataFrame([r for x in res for r in x[0]]); M.to_csv(os.path.join(HERE, "metrics.csv"), index=False)
    pd.DataFrame([r for x in res for r in x[1]]).to_csv(os.path.join(HERE, "predictions.csv"), index=False)
    write_yaml(os.path.join(HERE, "config.yaml"), dict(CFG, splits=list(SPL), infeasible=dict(
        PySR="not run: requires a Julia runtime, not installed on the box; LassoCV on degree-2 expanded features used as SISSO/PySR-like sparse baseline",
        Roost="not run: requires PyTorch + roost package and GPU-scale training; not installed; with 55 training formulas a message-passing net is expected to be data-starved. Documented as a gap."), provenance=provenance()))
    M["family"] = np.where(M.split.str.startswith("random"), "random_60_40", np.where(M.split == "quaternary_heldout", "quaternary_heldout", "group_heldout"))
    per_split = M.groupby(["family", "split", "model"]).test_MAE.mean().reset_index()
    S = []
    for (fam, m), g in per_split.groupby(["family", "model"]):
        mm, lo, hi = boot_ci(g.test_MAE); S.append(dict(family=fam, model=m, n_splits=len(g), MAE_mean=round(mm, 4), CI95_lo=round(lo, 4), CI95_hi=round(hi, 4),
                                                        runtime_s=round(M[(M.family == fam) & (M.model == m)].runtime_s.mean(), 2)))
    S = pd.DataFrame(S).sort_values(["family", "MAE_mean"]); S.to_csv(os.path.join(HERE, "summary.csv"), index=False)
    T = []
    for fam in ["random_60_40", "group_heldout", "all_except_quaternary"]:
        g = per_split[per_split.family != "quaternary_heldout"] if fam.startswith("all") else per_split[per_split.family == fam]
        pv = g.pivot_table(index="split", columns="model", values="test_MAE")
        for ref in ["V03_GP", "proposed_two_population"]:
            for m in pv.columns:
                if m != ref: T.append(dict(family=fam, comparison=f"{ref} - {m}", **paired(pv[ref], pv[m])))
    T = pd.DataFrame(T); T["holm_p"] = np.nan
    for fam, idx in T.groupby("family").groups.items(): T.loc[idx, "holm_p"] = holm(T.loc[idx, "wilcoxon_p"].values)
    T.to_csv(os.path.join(HERE, "paired_tests.csv"), index=False)
    # ablations from expt01
    e1 = os.path.join(os.path.dirname(HERE), "expt01_specialist_rules", "paired_tests.csv")
    if os.path.exists(e1):
        a = pd.read_csv(e1); a[(a.comparison.str.contains("ablation|high_residual|random_samples")) & (a.family == "all")].to_csv(os.path.join(HERE, "ablations_from_expt01.csv"), index=False)
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    os.makedirs(os.path.join(HERE, "figures"), exist_ok=True); fig, ax = plt.subplots(figsize=(10, 4.5))
    fams = ["random_60_40", "group_heldout", "quaternary_heldout"]; mods = list(S[S.family == "random_60_40"].model)
    for j, fam in enumerate(fams):
        s = S[S.family == fam].set_index("model").reindex(mods)
        ax.errorbar(np.arange(len(mods)) + 0.25 * (j - 1), s.MAE_mean, yerr=[s.MAE_mean - s.CI95_lo, s.CI95_hi - s.MAE_mean], fmt="o", capsize=3, label=fam)
    ax.set_xticks(range(len(mods))); ax.set_xticklabels(mods, rotation=30, ha="right", fontsize=7); ax.set_ylabel("hidden-test MAE (eV/atom, DFT) with 95% CI"); ax.legend()
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "figures", "expt06_baselines.png"), dpi=150)
    pd.set_option("display.width", 250); print(S.to_string()); print(T[T.family == "all_except_quaternary"].round(4).to_string()); print("runtime", time.time() - T0)
