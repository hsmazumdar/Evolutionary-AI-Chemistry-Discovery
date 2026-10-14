"""Expt-03: does a rule evolved on Fe-Na-O-P transfer to other chemical systems?  python reproduce.py [--quick]
Source: all 91 Fe-Na-O-P formulas (DFT Ef). Targets: other MP experimentally-observed systems; target compounds that
lie inside the Fe-Na-O-P system are removed. Similar targets share the phosphate/oxide chemistry; dissimilar do not.
Few-shot k target labels are drawn at random; evaluation is on the remaining target compounds."""
import os, sys, json, time, argparse, copy
from multiprocessing import Pool
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
from shared.common import load_poc, load_mp_subset, system_table, featurize, mae, boot_ci, paired, holm, provenance, write_yaml, GP
from sklearn.linear_model import RidgeCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
ap = argparse.ArgumentParser(); ap.add_argument("--quick", action="store_true"); A = ap.parse_args()
TARGETS = {"K-Fe-O-P": "similar", "Li-Fe-O-P": "similar", "Na-Mn-O-P": "similar", "Na-Fe-O-S": "intermediate",
           "Ba-Ti-O-Si": "dissimilar", "Al-Mg-O-Si": "dissimilar", "H-N-O-S": "dissimilar"}
CFG = dict(pop=200, gens=60, evo_seeds=[0, 1, 2], shots=[0, 5, 10, 20], draws=5)
if A.quick: CFG.update(pop=40, gens=5, evo_seeds=[0], draws=1); TARGETS = dict(list(TARGETS.items())[:2])
P = load_poc(); el = P["el"]; MP = load_mp_subset(); SRC = frozenset("Fe Na O P".split())
TT = {}
for t in TARGETS:
    g = system_table(MP, t.split("-")); g = g[~g.elset.apply(lambda e: e <= SRC)].reset_index(drop=True)
    Xt, _ = featurize(list(g.comp), el); TT[t] = (Xt, g.formation_energy_per_atom_eV.values, list(g.formula))
Xs, ys = P["X"], P["y"]

def job(seed):
    rows, preds, rules = [], [], []
    g = GP(P["names"], pop_size=CFG["pop"], generations=CFG["gens"], seed=seed).fit(Xs, ys)
    rid = make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-3, 3, 13))).fit(Xs, ys)
    rf = RandomForestRegressor(300, min_samples_leaf=3, random_state=seed).fit(Xs, ys)
    rules.append(dict(evo_seed=seed, source_rule=g.to_str(), nodes=len(g.best)))
    for t, kind in TARGETS.items():
        Xt, yt, names = TT[t]
        for k in CFG["shots"]:
            for d in range(CFG["draws"] if k else 1):
                rng = np.random.default_rng(1000 * seed + 10 * k + d); p = rng.permutation(len(yt)); sh, ev = p[:k], p[k:]
                out = {"GP_source_zero_shot": g.predict(Xt[ev]), "ridge_source_zero_shot": rid.predict(Xt[ev]), "RF_source_zero_shot": rf.predict(Xt[ev])}
                if k:
                    sc = g._scale(g._eval(g.best, Xt[sh]), yt[sh], np.ones(k)); out["GP_source_structure_refit_on_target"] = g.predict(Xt[ev], scale=sc)
                    gt = GP(P["names"], pop_size=CFG["pop"], generations=CFG["gens"], seed=seed + 50).fit(Xt[sh], yt[sh]); out["GP_target_only_scratch"] = gt.predict(Xt[ev])
                    out["ridge_target_only"] = make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-3, 3, 13), cv=None)).fit(Xt[sh], yt[sh]).predict(Xt[ev])
                    out["ridge_pooled_source+target"] = make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-3, 3, 13))).fit(np.vstack([Xs, Xt[sh]]), np.concatenate([ys, yt[sh]])).predict(Xt[ev])
                    out["target_shot_mean"] = np.full(len(ev), yt[sh].mean())
                    # residual correction: source rule + constant offset learned on shots
                    out["GP_source_plus_offset"] = g.predict(Xt[ev]) + np.mean(yt[sh] - g.predict(Xt[sh]))
                for mname, pr in out.items():
                    rows.append(dict(target=t, similarity=kind, n_target=len(yt), shots=k, draw=d, evo_seed=seed, method=mname, MAE=mae(pr, yt[ev])))
                    if d == 0: preds.extend(dict(target=t, shots=k, evo_seed=seed, method=mname, formula=names[i], y_DFT=float(yt[i]), y_pred=float(q)) for i, q in zip(ev, pr))
    return rows, preds, rules

if __name__ == "__main__":
    T0 = time.time()
    with Pool(8) as pool: res = pool.map(job, CFG["evo_seeds"])
    M = pd.DataFrame([r for x in res for r in x[0]]); M.to_csv(os.path.join(HERE, "metrics.csv"), index=False)
    pd.DataFrame([r for x in res for r in x[1]]).to_csv(os.path.join(HERE, "predictions.csv"), index=False)
    json.dump([r for x in res for r in x[2]], open(os.path.join(HERE, "rules.json"), "w"), indent=1)
    write_yaml(os.path.join(HERE, "config.yaml"), dict(CFG, targets=TARGETS, n_target={t: len(v[1]) for t, v in TT.items()}, provenance=provenance()))
    S = M.groupby(["similarity", "target", "shots", "method"]).MAE.mean().round(3).unstack("method"); S.to_csv(os.path.join(HERE, "summary_by_target.csv"))
    G = M.groupby(["similarity", "shots", "method", "target"]).MAE.mean().reset_index()
    rows = []
    for (sim, k, m), g in G.groupby(["similarity", "shots", "method"]):
        mm, lo, hi = boot_ci(g.MAE); rows.append(dict(similarity=sim, shots=k, method=m, n_targets=len(g), MAE=round(mm, 3), CI_lo=round(lo, 3), CI_hi=round(hi, 3)))
    S2 = pd.DataFrame(rows); S2.to_csv(os.path.join(HERE, "summary.csv"), index=False)
    T = []
    for k in [5, 10, 20]:
        pv = M[M.shots == k].pivot_table(index=["target", "draw", "evo_seed"], columns="method", values="MAE")
        for c in ["GP_target_only_scratch", "ridge_target_only", "target_shot_mean", "ridge_pooled_source+target", "GP_source_plus_offset"]:
            for sim in ["similar", "dissimilar"]:
                sub = pv[pv.index.get_level_values(0).map(TARGETS) == sim]
                if len(sub): T.append(dict(shots=k, similarity=sim, comparison=f"GP_source_structure_refit_on_target - {c}", **paired(sub["GP_source_structure_refit_on_target"], sub[c])))
    T = pd.DataFrame(T); T["holm_p"] = holm(T.wilcoxon_p.values); T.to_csv(os.path.join(HERE, "paired_tests.csv"), index=False)
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    os.makedirs(os.path.join(HERE, "figures"), exist_ok=True); fig, axs = plt.subplots(1, 3, figsize=(14, 4), sharey=True)
    for ax, sim in zip(axs, ["similar", "intermediate", "dissimilar"]):
        s = S2[S2.similarity == sim]
        for m in ["GP_source_structure_refit_on_target", "GP_source_plus_offset", "GP_target_only_scratch", "ridge_target_only", "ridge_pooled_source+target", "target_shot_mean", "GP_source_zero_shot"]:
            q = s[s.method == m].sort_values("shots"); ax.plot(q.shots, q.MAE, "o-", label=m)
        ax.set_title(f"{sim} targets"); ax.set_xlabel("target labels (shots)")
    axs[0].set_ylabel("target MAE (eV/atom, DFT)"); axs[2].legend(fontsize=6); fig.tight_layout(); fig.savefig(os.path.join(HERE, "figures", "expt03_transfer.png"), dpi=150)
    pd.set_option("display.width", 250); print(S2.to_string()); print(T.round(4).to_string()); print("runtime", time.time() - T0)
