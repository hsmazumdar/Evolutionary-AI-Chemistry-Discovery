"""Expt-05: statistical focusing / active observation. The learner may request labels (DFT Ef) from the TRAINING
partition only; the test partition stays sealed. Same GP budget per round for every strategy.  python reproduce.py [--quick]"""
import os, sys, json, time, argparse
from multiprocessing import Pool
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
from shared.common import load_poc, load_splits, reliability, mae, boot_ci, paired, holm, provenance, write_yaml, GP
from shared.twopop import archive, archive_sigma
ap = argparse.ArgumentParser(); ap.add_argument("--quick", action="store_true"); A = ap.parse_args()
CFG = dict(pop=150, gens_per_round=12, n_init=8, batch=4, n_max=40, evo_seeds=[0, 1, 2], archive_k=10,
           strategies=["random", "uncertainty", "uncertainty_x_reliability", "diversity", "uncertainty+diversity"])
if A.quick: CFG.update(pop=40, gens_per_round=3, n_max=16, evo_seeds=[0])
P = load_poc(); X, y = P["X"], P["y"]; REL = reliability(P["df"]); SPL = load_splits(P["df"])
if A.quick: SPL = {k: SPL[k] for k in list(SPL)[:2]}
Z = (X - X.mean(0)) / (X.std(0) + 1e-9)

def job(arg):
    sname, seed, strat = arg; tr, te = SPL[sname]["train"], SPL[sname]["test"]; rng = np.random.default_rng(seed)
    lab = list(rng.choice(tr, CFG["n_init"], replace=False)); g = GP(P["names"], pop_size=CFG["pop"], seed=seed); rows = []; picks = []
    while True:
        L = np.array(lab); g.fit(X[L], y[L], generations=CFG["gens_per_round"])
        rows.append(dict(split=sname, evo_seed=seed, strategy=strat, n_labels=len(L), test_MAE=mae(g.predict(X[te]), y[te]), rule=g.to_str()))
        if len(L) >= CFG["n_max"]: break
        pool = np.array([i for i in tr if i not in set(lab)])
        if strat == "random": sc = rng.random(len(pool))
        else:
            sig = archive_sigma(g, archive(g, X[L], y[L], CFG["archive_k"]), X[pool])
            dmin = np.min(((Z[pool][:, None, :] - Z[L][None, :, :]) ** 2).sum(-1), 1)
            sc = {"uncertainty": sig, "uncertainty_x_reliability": sig * REL[pool], "diversity": dmin,
                  "uncertainty+diversity": sig / (sig.std() + 1e-9) + dmin / (dmin.std() + 1e-9)}[strat]
        new = []
        for _ in range(CFG["batch"]):   # greedy batch; diversity terms updated for already-chosen points
            j = int(np.argmax(sc)); new.append(int(pool[j])); sc[j] = -np.inf
            if strat in ("diversity", "uncertainty+diversity"):
                dn = ((Z[pool] - Z[pool[j]]) ** 2).sum(1); sc = np.where(np.isfinite(sc), np.minimum(sc, dn if strat == "diversity" else sc - (dn < 1.0) * 1.0), sc)
        lab += new; picks.append(new)
    return rows, dict(split=sname, evo_seed=seed, strategy=strat, query_order=[int(i) for i in lab])

if __name__ == "__main__":
    T0 = time.time(); jobs = [(s, e, st) for s in SPL for e in CFG["evo_seeds"] for st in CFG["strategies"]]
    with Pool(8) as pool: res = pool.map(job, jobs)
    M = pd.DataFrame([r for x in res for r in x[0]]); M.to_csv(os.path.join(HERE, "metrics.csv"), index=False)
    M[["split", "evo_seed", "strategy", "n_labels", "test_MAE"]].to_csv(os.path.join(HERE, "predictions.csv"), index=False)  # learning-curve points
    json.dump([x[1] for x in res], open(os.path.join(HERE, "rules.json"), "w"), indent=1)
    write_yaml(os.path.join(HERE, "config.yaml"), dict(CFG, splits=list(SPL), provenance=provenance()))
    M["family"] = np.where(M.split.str.startswith("random"), "random_60_40", "group_heldout")
    auc = M.groupby(["family", "split", "evo_seed", "strategy"]).test_MAE.mean().reset_index().rename(columns={"test_MAE": "learning_curve_mean_MAE"})
    fin = M[M.n_labels == M.n_labels.max()][["family", "split", "evo_seed", "strategy", "test_MAE"]]
    D = auc.merge(fin, on=["family", "split", "evo_seed", "strategy"]); D.to_csv(os.path.join(HERE, "derived_metrics.csv"), index=False)
    S = []; T = []
    for fam in ["random_60_40", "group_heldout"]:
        for st in CFG["strategies"]:
            g = D[(D.family == fam) & (D.strategy == st)]
            for c in ["learning_curve_mean_MAE", "test_MAE"]:
                mm, lo, hi = boot_ci(g.groupby("split")[c].mean()); S.append(dict(family=fam, strategy=st, metric=c, mean=round(mm, 4), CI_lo=round(lo, 4), CI_hi=round(hi, 4)))
        for c in ["learning_curve_mean_MAE", "test_MAE"]:
            pv = D[D.family == fam].pivot_table(index=["split", "evo_seed"], columns="strategy", values=c)
            if pv.empty: continue
            for st in CFG["strategies"][1:]: T.append(dict(family=fam, metric=c, comparison=f"{st} - random", **paired(pv[st], pv["random"])))
    S = pd.DataFrame(S); S.to_csv(os.path.join(HERE, "summary.csv"), index=False); T = pd.DataFrame(T); T["holm_p"] = holm(T.wilcoxon_p.values); T.to_csv(os.path.join(HERE, "paired_tests.csv"), index=False)
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    os.makedirs(os.path.join(HERE, "figures"), exist_ok=True); fig, axs = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    for ax, fam in zip(axs, ["random_60_40", "group_heldout"]):
        for st in CFG["strategies"]:
            q = M[(M.family == fam) & (M.strategy == st)].groupby("n_labels").test_MAE.mean(); ax.plot(q.index, q.values, "o-", label=st)
        ax.set_title(fam); ax.set_xlabel("labelled training compounds")
    axs[0].set_ylabel("hidden-test MAE (eV/atom, DFT)"); axs[1].legend(fontsize=7); fig.tight_layout(); fig.savefig(os.path.join(HERE, "figures", "expt05_learning_curves.png"), dpi=150)
    pd.set_option("display.width", 250); print(S.to_string()); print(T.round(4).to_string()); print("runtime", time.time() - T0)
