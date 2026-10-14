"""Expt-02: versioned competing-hypothesis memory under incremental evidence episodes.  python reproduce.py [--quick]
Streams: 'chemical' (episode 1 = elements+binaries, 2 = ternaries, 3 = quaternaries) and 'random' (3 random chunks).
Every method gets the same GP budget per episode (gens_per_episode x pop)."""
import os, sys, json, time, copy, argparse
from multiprocessing import Pool
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
from shared.common import load_poc, load_splits, mae, boot_ci, paired, holm, provenance, write_yaml, GP
from shared.memory_v04 import HypothesisMemory
from shared.twopop import archive
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE))); from evochem.memory import KnowledgeMemory
ap = argparse.ArgumentParser(); ap.add_argument("--quick", action="store_true"); A = ap.parse_args()
CFG = dict(pop=200, gens_per_episode=20, replay_size=12, archive_k=5, evo_seeds=[0, 1, 2], z90=1.645)
if A.quick: CFG.update(pop=50, gens_per_episode=4, evo_seeds=[0])
P = load_poc(); X, y, df = P["X"], P["y"], P["df"]; NE = df.nelements.values
SPL = {k: v for k, v in load_splits(df, include_groupfolds=False).items() if k.startswith("random")}
if A.quick: SPL = {k: SPL[k] for k in list(SPL)[:2]}
METHODS = ["scratch_retrain", "sequential_GP", "replay_GP", "V03_archive", "proposed_memory"]

def episodes(tr, stream, seed):
    if stream == "chemical": return [tr[NE[tr] <= 2], tr[NE[tr] == 3], tr[NE[tr] == 4]]
    p = np.random.default_rng(seed).permutation(tr); return [np.sort(c) for c in np.array_split(p, 3)]

def ep_of_test(te, stream):  # which episode-domain a test item belongs to (only meaningful for the chemical stream)
    return np.where(NE[te] <= 2, 0, np.where(NE[te] == 3, 1, 2)) if stream == "chemical" else np.full(len(te), -1)

def job(arg):
    sname, stream, seed = arg; tr, te = SPL[sname]["train"], SPL[sname]["test"]; E = episodes(tr, stream, seed); et = ep_of_test(te, stream)
    rng = np.random.default_rng(seed); rows = []; preds = []; mems = {}
    st = {m: dict(gp=None, buffer=np.array([], int), seen=np.array([], int), evals=0) for m in METHODS}
    hm = HypothesisMemory(); km = KnowledgeMemory(f"{sname} {stream}")
    for k, new in enumerate(E):
        for m in METHODS:
            s = st[m]; t0 = time.time(); s["seen"] = np.concatenate([s["seen"], new])
            if m == "scratch_retrain": data = s["seen"]; s["gp"] = GP(P["names"], pop_size=CFG["pop"], seed=seed * 100 + k)
            elif m == "sequential_GP": data = new
            elif m in ("replay_GP", "proposed_memory"): data = np.concatenate([new, s["buffer"]])
            else: data = s["seen"]                       # V03 archive: keeps all data, single active rule
            if s["gp"] is None: s["gp"] = GP(P["names"], pop_size=CFG["pop"], seed=seed)
            g = s["gp"]
            # fitness test before learning this episode = forward-transfer probe (on test items of the NEXT domain)
            g.fit(X[data], y[data], generations=CFG["gens_per_episode"]); s["evals"] += CFG["gens_per_episode"] * CFG["pop"] * len(data)
            if m in ("replay_GP", "proposed_memory"):
                pool_ = np.concatenate([s["buffer"], new]); s["buffer"] = np.sort(rng.choice(pool_, min(CFG["replay_size"], len(pool_)), replace=False))
            revs = dict(revised=0, retired=0, new=0, active=1)
            if m == "proposed_memory":
                revs = hm.update(g, [(t, sc) for t, sc, _ in archive(g, X[data], y[data], CFG["archive_k"])], X[data], y[data], k)
                pr, sd = hm.predict(g, X[te], return_std=True); mem_cost = len(hm.h) + len(s["buffer"])
                pnext = None
            else:
                if m == "V03_archive":
                    before = len(km.data["revision_history"])
                    km.consider(k, g.to_str(), len(g.best), float(np.mean(np.abs(y[data] - g.predict(X[data])))), len(data), f"episode{k}", "new episode evidence")
                    revs["revised"] = len(km.data["revision_history"]) - before
                pr = g.predict(X[te]); r = np.abs(y[data] - g.predict(X[data])); sd = np.full(len(te), 1.25 * r.mean())
                mem_cost = {"scratch_retrain": len(s["seen"]), "sequential_GP": 1, "replay_GP": 1 + len(s["buffer"]), "V03_archive": len(s["seen"]) + len(km.data["rules"])}[m]
            cover = float(np.mean(np.abs(y[te] - pr) <= CFG["z90"] * sd))
            row = dict(split=sname, stream=stream, evo_seed=seed, method=m, episode=k, n_episode_samples=len(new), test_MAE=mae(pr, y[te]),
                       coverage90=cover, mean_interval_halfwidth=float(np.mean(CFG["z90"] * sd)), memory_items=mem_cost,
                       cum_fitness_evals=s["evals"], runtime_s=time.time() - t0, **{f"n_{a}": b for a, b in revs.items()})
            for d in range(3):
                msk = et == d; row[f"MAE_domain{d}"] = mae(pr[msk], y[te][msk]) if msk.any() else np.nan
            rows.append(row)
            preds.extend(dict(split=sname, stream=stream, evo_seed=seed, method=m, episode=k, sample_idx=int(i), y_DFT=float(y[i]), y_pred=float(p), sd=float(q)) for i, p, q in zip(te, pr, sd))
    mems = dict(split=sname, stream=stream, evo_seed=seed, proposed=hm.to_json(), V03=km.data)
    return rows, preds, mems

if __name__ == "__main__":
    T0 = time.time(); jobs = [(s, st, e) for s in SPL for st in ["chemical", "random"] for e in CFG["evo_seeds"]]
    with Pool(8) as pool: res = pool.map(job, jobs)
    M = pd.DataFrame([r for x in res for r in x[0]]); M.to_csv(os.path.join(HERE, "metrics.csv"), index=False)
    pd.DataFrame([r for x in res for r in x[1]]).to_csv(os.path.join(HERE, "predictions.csv"), index=False)
    json.dump([x[2] for x in res], open(os.path.join(HERE, "rules.json"), "w"), indent=1, default=str)
    write_yaml(os.path.join(HERE, "config.yaml"), dict(CFG, splits=list(SPL), provenance=provenance()))
    # derived: forgetting (domain0 MAE at last episode - right after episode 0), forward transfer (domain k+1 MAE before seeing it - after)
    D = []
    for key, g in M.groupby(["split", "stream", "evo_seed", "method"]):
        g = g.sort_values("episode"); d = dict(zip(["split", "stream", "evo_seed", "method"], key)); d["final_test_MAE"] = g.test_MAE.iloc[-1]
        d["mean_episode_MAE"] = g.test_MAE.mean(); d["final_coverage90"] = g.coverage90.iloc[-1]; d["total_revisions"] = g.n_revised.sum(); d["total_retired"] = g.n_retired.sum()
        d["memory_items_final"] = g.memory_items.iloc[-1]; d["fitness_evals"] = g.cum_fitness_evals.iloc[-1]; d["runtime_s"] = g.runtime_s.sum()
        if key[1] == "chemical":
            d["forgetting_domain0"] = g.MAE_domain0.iloc[-1] - g.MAE_domain0.iloc[0]
            d["forward_transfer_MAE_domain1_before"] = g.MAE_domain1.iloc[0]; d["forward_transfer_MAE_domain2_before"] = g.MAE_domain2.iloc[1]
        D.append(d)
    D = pd.DataFrame(D); D.to_csv(os.path.join(HERE, "derived_metrics.csv"), index=False)
    S = []
    for (stream, m), g in D.groupby(["stream", "method"]):
        row = dict(stream=stream, method=m)
        for c in ["final_test_MAE", "mean_episode_MAE", "final_coverage90", "forgetting_domain0", "forward_transfer_MAE_domain2_before", "total_revisions", "memory_items_final", "fitness_evals", "runtime_s"]:
            if c in g and g[c].notna().any():
                mm, lo, hi = boot_ci(g.groupby("split")[c].mean()); row[c] = f"{mm:.3f} [{lo:.3f}, {hi:.3f}]" if abs(mm) < 100 else f"{mm:.3g}"
        S.append(row)
    S = pd.DataFrame(S); S.to_csv(os.path.join(HERE, "summary.csv"), index=False)
    T = []
    for stream in ["chemical", "random"]:
        for c in ["final_test_MAE", "mean_episode_MAE"] + (["forgetting_domain0"] if stream == "chemical" else []):
            pv = D[D.stream == stream].pivot_table(index=["split", "evo_seed"], columns="method", values=c)
            for m in METHODS[:-1]: T.append(dict(stream=stream, metric=c, comparison=f"proposed_memory - {m}", **paired(pv["proposed_memory"], pv[m])))
    T = pd.DataFrame(T); T["holm_p"] = holm(T.wilcoxon_p.values); T.to_csv(os.path.join(HERE, "paired_tests.csv"), index=False)
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    os.makedirs(os.path.join(HERE, "figures"), exist_ok=True); fig, axs = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    for ax, stream in zip(axs, ["chemical", "random"]):
        for m in METHODS:
            g = M[(M.stream == stream) & (M.method == m)].groupby("episode").test_MAE.mean(); ax.plot(g.index + 1, g.values, "o-", label=m)
        ax.set_title(f"{stream} episode stream"); ax.set_xlabel("episode"); ax.set_xticks([1, 2, 3])
    axs[0].set_ylabel("hidden-test MAE (eV/atom, DFT)"); axs[1].legend(fontsize=7); fig.tight_layout(); fig.savefig(os.path.join(HERE, "figures", "expt02_episode_mae.png"), dpi=150)
    pd.set_option("display.width", 250); print(S.to_string()); print(T.round(4).to_string()); print("runtime", time.time() - T0)
