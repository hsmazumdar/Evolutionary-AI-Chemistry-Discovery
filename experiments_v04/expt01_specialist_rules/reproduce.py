"""Expt-01: contradiction-driven specialist rule evolution vs controls and ablations.  python reproduce.py [--quick]"""
import os, sys, json, time, argparse
from multiprocessing import Pool
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
from shared.common import load_poc, load_splits, reliability, mae, boot_ci, paired, holm, provenance, write_yaml
from shared.twopop import fit_two_population, predict_two_population, in_domain, fit_controls
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
ap = argparse.ArgumentParser(); ap.add_argument("--quick", action="store_true"); A = ap.parse_args()
CFG = dict(pop=200, gens_G=40, gens_S=20, inner_val_frac=0.25, archive_k=10, contradiction_frac=0.15, min_contradictions=4,
           gate_depth=2, gate_min_leaf=2, accept_margin=0.005, exceptional_quantile=0.75, evo_seeds=[0, 1, 2, 3, 4])
if A.quick: CFG.update(pop=60, gens_G=8, gens_S=4, evo_seeds=[0])
SPEC = {"specialist_random_samples": dict(selection="random"), "specialist_high_residual": dict(selection="high_residual"),
        "proposed_two_population": dict(selection="proposed"),
        "ablation_no_uncertainty": dict(selection="no_uncertainty"), "ablation_no_reliability": dict(selection="no_reliability"),
        "ablation_no_validation_gate": dict(selection="proposed", use_validation=False),
        "ablation_no_missing_variable_search": dict(selection="proposed", missing_var_search=False)}
P = load_poc(); X, Xo, y, df = P["X"], P["Xo"], P["y"], P["df"]; REL = reliability(df); SPL = load_splits(df)
if A.quick: SPL = {k: SPL[k] for k in ["random_split_seed0", "groupfold0"]}

def job(arg):
    sname, seed = arg; tr, te = SPL[sname]["train"], SPL[sname]["test"]
    # independent exceptional/ordinary labelling of TEST items (evaluation only): residual of a ridge reference model fit on train
    ref = make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-3, 3, 13))).fit(X[tr], y[tr])
    rr = np.abs(y[te] - ref.predict(X[te])); exc = rr >= np.quantile(rr, CFG["exceptional_quantile"])
    out_m, out_p, rules = [], [], []
    def record(name, pred, extra, dom=None):
        t0 = extra.pop("_t", None)
        m = dict(split=sname, evo_seed=seed, method=name, n_train=len(tr), n_test=len(te), test_MAE=mae(pred, y[te]),
                 MAE_exceptional=mae(pred[exc], y[te][exc]), MAE_ordinary=mae(pred[~exc], y[te][~exc]), **extra)
        if dom is not None:
            m["n_test_in_domain"] = int(dom.sum())
            m["domain_precision"] = float(exc[dom].mean()) if dom.any() else np.nan
            m["domain_recall"] = float(dom[exc].mean()) if exc.any() else np.nan
        out_m.append(m)
        out_p.extend([dict(split=sname, evo_seed=seed, method=name, sample_idx=int(i), formula=df.formula[i], y_DFT=float(y[i]),
                       y_pred=float(p), exceptional=bool(e), in_domain=(bool(dm) if dom is not None else None))
                  for i, p, e, dm in zip(te, pred, exc, dom if dom is not None else [None] * len(te))])
    t = time.time(); ctr, nflag = fit_controls(X, y, df.n_icsd.values, tr, seed, CFG, P["names"]); tc = time.time() - t
    for k, g in ctr.items():
        record(k, g.predict(X[te]), dict(rule_nodes=len(g.best), n_accepted_specialists=0, runtime_s=tc / 3,
                                         gp_generation_budget=CFG["gens_G"] + (0 if k == "ordinary_GP" else CFG["gens_S"])))
        rules.append(dict(split=sname, evo_seed=seed, method=k, rule=g.to_str(), nodes=len(g.best), v03_flagged=nflag if "V03" in k else None))
    # extra control (added after first analysis): ordinary GP given the same charge-balance features the specialist may use
    from shared.common import GP as _GP
    t = time.time(); gox = _GP(P["names_o"], pop_size=CFG["pop"], generations=CFG["gens_G"] + CFG["gens_S"], seed=seed).fit(Xo[tr], y[tr])
    record("GP_extra_generations_with_charge_balance_features", gox.predict(Xo[te]), dict(rule_nodes=len(gox.best), n_accepted_specialists=0, runtime_s=time.time() - t, gp_generation_budget=CFG["gens_G"] + CFG["gens_S"]))
    rules.append(dict(split=sname, evo_seed=seed, method="GP_extra_generations_with_charge_balance_features", rule=gox.to_str(), nodes=len(gox.best)))
    Gfit = None
    for k, kw in SPEC.items():
        t = time.time(); model, info, Gfit = fit_two_population(X, Xo, y, REL, tr, seed, CFG, P["names"], P["names_o"], G_fit=Gfit, **kw)
        pred = predict_two_population(model, X, te) if not model["accepted"] or model["XX"] is X else None
        if pred is None:
            pg = model["G"].predict(X[te]); ps = model["S"].predict(model["XX"][te]); d = model["gate"].predict(X[te]).astype(bool)
            pred = np.where(d, ps if model["mode"] == "replace" else 0.5 * (pg + ps), pg)
        dom = in_domain(model, X, te)
        record(k, pred, dict(rule_nodes=info["G_nodes"] + (info["S_nodes"] if info["accepted"] else 0), n_accepted_specialists=int(info["accepted"]),
                             specialist_nodes=info["S_nodes"] if info["accepted"] else None, specialist_features=info["S_features"] if info["accepted"] else None,
                             n_contradictions=info["n_contradictions"], train_C_err_G=info["train_C_abs_err_G"], train_C_err_after=info["train_C_abs_err_after"],
                             val_MAE_G=info["val_mae_G"], val_MAE_combo=info["val_mae_best_combo"], runtime_s=time.time() - t,
                             gp_generation_budget=CFG["gens_G"] + CFG["gens_S"]), dom)
        rules.append(dict(split=sname, evo_seed=seed, method=k, **{a: b for a, b in info.items()},
                          contradiction_formulas=[df.formula[i] for i in info["contradiction_idx"]]))
    return out_m, out_p, rules

if __name__ == "__main__":
    T0 = time.time(); jobs = [(s, e) for s in SPL for e in CFG["evo_seeds"]]
    with Pool(min(8, os.cpu_count())) as pool: res = pool.map(job, jobs)
    M = pd.DataFrame([m for r in res for m in r[0]]); Pr = pd.DataFrame([p for r in res for p in r[1]]); R = [x for r in res for x in r[2]]
    M.to_csv(os.path.join(HERE, "metrics.csv"), index=False); Pr.to_csv(os.path.join(HERE, "predictions.csv"), index=False)
    json.dump(R, open(os.path.join(HERE, "rules.json"), "w"), indent=1, default=str)
    write_yaml(os.path.join(HERE, "config.yaml"), dict(CFG, splits=list(SPL), provenance=provenance()))
    # summary
    M["family"] = np.where(M.split.str.startswith("random"), "random_60_40", "group_heldout")
    S = []
    for (fam, meth), g in M.groupby(["family", "method"]):
        row = dict(family=fam, method=meth, n_runs=len(g))
        for c in ["test_MAE", "MAE_exceptional", "MAE_ordinary"]:
            # average over evo seeds within split first, then CI over splits
            v = g.groupby("split")[c].mean(); m, lo, hi = boot_ci(v); row[c] = f"{m:.3f} [{lo:.3f}, {hi:.3f}]"
        row["accept_rate"] = round(g.n_accepted_specialists.mean(), 2); row["mean_nodes"] = round(g.rule_nodes.mean(), 1)
        row["domain_precision"] = round(g.domain_precision.mean(), 2) if "domain_precision" in g and g.domain_precision.notna().any() else None
        row["runtime_s"] = round(g.runtime_s.mean(), 2); S.append(row)
    S = pd.DataFrame(S); S.to_csv(os.path.join(HERE, "summary.csv"), index=False)
    T = []
    for fam in ["random_60_40", "group_heldout", "all"]:
        g = M if fam == "all" else M[M.family == fam]
        piv = {c: g.pivot_table(index=["split", "evo_seed"], columns="method", values=c) for c in ["test_MAE", "MAE_exceptional", "MAE_ordinary"]}
        for ctl in ["ordinary_GP", "GP_extra_generations", "GP_extra_generations_with_charge_balance_features", "V03_contradiction_weighted", "specialist_random_samples", "specialist_high_residual"] + [k for k in SPEC if k.startswith("ablation")]:
            for c, pv in piv.items():
                T.append(dict(family=fam, metric=c, comparison=f"proposed - {ctl}", **paired(pv["proposed_two_population"], pv[ctl])))
    T = pd.DataFrame(T); T["holm_p"] = np.nan
    for (fam, c), idx in T.groupby(["family", "metric"]).groups.items(): T.loc[idx, "holm_p"] = holm(T.loc[idx, "wilcoxon_p"].values)
    T.to_csv(os.path.join(HERE, "paired_tests.csv"), index=False)
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    os.makedirs(os.path.join(HERE, "figures"), exist_ok=True)
    order = ["ordinary_GP", "GP_extra_generations", "GP_extra_generations_with_charge_balance_features", "V03_contradiction_weighted", "specialist_random_samples", "specialist_high_residual", "proposed_two_population"]
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.5), sharey=True)
    for ax, c in zip(axs, ["test_MAE", "MAE_exceptional", "MAE_ordinary"]):
        data = [M[M.method == o].groupby("split")[c].mean().values for o in order]
        ax.boxplot(data, tick_labels=[o.replace("_", "\n") for o in order]); ax.set_title(c + " (eV/atom, DFT target)"); ax.tick_params(labelsize=6)
    axs[0].set_ylabel("MAE per split (mean of 5 evo seeds)"); fig.tight_layout(); fig.savefig(os.path.join(HERE, "figures", "expt01_mae_boxplots.png"), dpi=150)
    print(S.to_string()); print(T[(T.family == "all")].round(4).to_string()); print("runtime", time.time() - T0)
