"""Expt-04: (i) robustness of the emergent periodicity (V03 PPMI-SVD co-occurrence embedding) under compound
subsampling and dimension changes; (ii) DOWNSTREAM benefit: do learned element embeddings improve formation-energy
prediction (Fe-Na-O-P splits; few-shot transfer targets) versus random / shuffled embeddings of equal size?
Embeddings never use any compound inside Fe-Na-O-P, nor (for transfer) inside the target system.  python reproduce.py [--quick]"""
import os, sys, json, time, argparse
from multiprocessing import Pool
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
from shared.common import load_poc, load_splits, load_mp_subset, system_table, featurize, mae, boot_ci, paired, holm, provenance, write_yaml, GP
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE))); from evochem import periodicity
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
ap = argparse.ArgumentParser(); ap.add_argument("--quick", action="store_true"); A = ap.parse_args()
CFG = dict(dim=12, boot=20, boot_frac=0.8, dims=[4, 8, 12, 24], gp_pop=200, gp_gens=40, evo_seeds=[0, 1, 2], n_null=200,
           transfer_targets=["K-Fe-O-P", "Li-Fe-O-P", "Na-Mn-O-P", "Na-Fe-O-S", "Ba-Ti-O-Si", "Al-Mg-O-Si", "H-N-O-S"], shots=10, draws=5)
if A.quick: CFG.update(boot=2, dims=[12], gp_pop=40, gp_gens=4, evo_seeds=[0], n_null=20, transfer_targets=["K-Fe-O-P"], draws=1)
P = load_poc(); el = P["el"]; MP = load_mp_subset(); SRC = set("Fe Na O P".split()); Zof = el["Z"].to_dict()

def emb_feats(comps, vocab, E):
    ix = {e: i for i, e in enumerate(vocab)}; out = []
    for c in comps:
        t = sum(c.values()); w = np.array([c[e] / t for e in c]); V = np.array([E[ix[e]] if e in ix else np.zeros(E.shape[1]) for e in c])
        m = w @ V; out.append(np.concatenate([m, w @ np.abs(V - m)]))
    return np.array(out)

def variants(vocab, E, seed):
    rng = np.random.default_rng(seed)
    return {"learned": E, "random_gaussian": rng.normal(0, E.std(), E.shape), "shuffled_elements": E[rng.permutation(len(E))]}

def robustness():
    rows = []
    vocab, embs, n = periodicity.element_embeddings(MP, SRC, dim=CFG["dim"])
    _, k, per = periodicity.evaluate(vocab, {"co": embs["co-occurrence (PPMI-SVD)"]}, Zof, n_null=CFG["n_null"]); rows.append(dict(kind="full", dim=CFG["dim"], ARI=per["co"]["ARI"], NN=per["co"]["nn_same_group"], null95=per["co"]["ARI_null_p95"]))
    for d in CFG["dims"]:
        v, e, _ = periodicity.element_embeddings(MP, SRC, dim=d); _, _, p = periodicity.evaluate(v, {"co": e["co-occurrence (PPMI-SVD)"]}, Zof, n_null=CFG["n_null"])
        rows.append(dict(kind="dim", dim=d, ARI=p["co"]["ARI"], NN=p["co"]["nn_same_group"], null95=p["co"]["ARI_null_p95"]))
    for b in range(CFG["boot"]):
        sub = MP.sample(frac=CFG["boot_frac"], random_state=b); v, e, _ = periodicity.element_embeddings(sub, SRC, dim=CFG["dim"])
        _, _, p = periodicity.evaluate(v, {"co": e["co-occurrence (PPMI-SVD)"]}, Zof, n_null=CFG["n_null"])
        rows.append(dict(kind="subsample80", dim=CFG["dim"], rep=b, ARI=p["co"]["ARI"], NN=p["co"]["nn_same_group"], null95=p["co"]["ARI_null_p95"]))
    return pd.DataFrame(rows), vocab, embs["co-occurrence (PPMI-SVD)"]

def poc_job(arg):
    sname, seed, vocab, E = arg; sp = load_splits(P["df"])[sname]; tr, te = sp["train"], sp["test"]; rows, preds = [], []
    for vn, EV in variants(vocab, E, seed).items():
        F = np.hstack([P["X"], emb_feats(P["comps"], vocab, EV)]); names = P["names"] + [f"emb{i}" for i in range(F.shape[1] - P["X"].shape[1])]
        r = make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-3, 3, 13))).fit(F[tr], P["y"][tr]).predict(F[te])
        g = GP(names, pop_size=CFG["gp_pop"], generations=CFG["gp_gens"], seed=seed).fit(F[tr], P["y"][tr]); pg = g.predict(F[te])
        rows += [dict(split=sname, evo_seed=seed, model="ridge", features=f"base+{vn}_embedding", MAE=mae(r, P["y"][te])),
                 dict(split=sname, evo_seed=seed, model="GP", features=f"base+{vn}_embedding", MAE=mae(pg, P["y"][te]), rule=g.to_str())]
        preds.extend(dict(split=sname, evo_seed=seed, model="GP", features=vn, sample_idx=int(i), y_DFT=float(P["y"][i]), y_pred=float(q)) for i, q in zip(te, pg))
    r = make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-3, 3, 13))).fit(P["X"][tr], P["y"][tr]).predict(P["X"][te])
    g = GP(P["names"], pop_size=CFG["gp_pop"], generations=CFG["gp_gens"], seed=seed).fit(P["X"][tr], P["y"][tr])
    rows += [dict(split=sname, evo_seed=seed, model="ridge", features="base_only", MAE=mae(r, P["y"][te])), dict(split=sname, evo_seed=seed, model="GP", features="base_only", MAE=mae(g.predict(P["X"][te]), P["y"][te]), rule=g.to_str())]
    return rows, preds

def transfer_job(t):
    rows = []; tel = set(t.split("-"))
    mp2 = MP[~MP.elset.apply(lambda e: e <= frozenset(tel))]
    vocab, embs, _ = periodicity.element_embeddings(mp2, SRC, dim=CFG["dim"]); E = embs["co-occurrence (PPMI-SVD)"]
    g = system_table(MP, t.split("-")); g = g[~g.elset.apply(lambda e: e <= frozenset(SRC))].reset_index(drop=True)
    Xt, _ = featurize(list(g.comp), el); yt = g.formation_energy_per_atom_eV.values
    for seed in CFG["evo_seeds"]:
        for vn, EV in list(variants(vocab, E, seed).items()) + [("none", None)]:
            Fs = P["X"] if EV is None else np.hstack([P["X"], emb_feats(P["comps"], vocab, EV)])
            Ft = Xt if EV is None else np.hstack([Xt, emb_feats(list(g.comp), vocab, EV)])
            for d in range(CFG["draws"]):
                p = np.random.default_rng(100 * seed + d).permutation(len(yt)); sh, ev = p[:CFG["shots"]], p[CFG["shots"]:]
                m = make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-3, 3, 13))).fit(np.vstack([Fs, Ft[sh]]), np.concatenate([P["y"], yt[sh]]))
                m0 = make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-3, 3, 13))).fit(Fs, P["y"])
                rows += [dict(target=t, evo_seed=seed, draw=d, features=vn, setting="pooled_10shot_ridge", MAE=mae(m.predict(Ft[ev]), yt[ev])),
                         dict(target=t, evo_seed=seed, draw=d, features=vn, setting="zero_shot_ridge", MAE=mae(m0.predict(Ft[ev]), yt[ev]))]
    return rows

if __name__ == "__main__":
    T0 = time.time(); R, vocab, E = robustness(); R.to_csv(os.path.join(HERE, "periodicity_robustness.csv"), index=False)
    spl = list(load_splits(P["df"]))
    if A.quick: spl = spl[:2]
    with Pool(8) as pool:
        res = pool.map(poc_job, [(s, e, vocab, E) for s in spl for e in CFG["evo_seeds"]])
        tres = pool.map(transfer_job, CFG["transfer_targets"])
    M = pd.DataFrame([r for x in res for r in x[0]]); M.to_csv(os.path.join(HERE, "metrics.csv"), index=False)
    pd.DataFrame([r for x in res for r in x[1]]).to_csv(os.path.join(HERE, "predictions.csv"), index=False)
    TM = pd.DataFrame([r for x in tres for r in x]); TM.to_csv(os.path.join(HERE, "transfer_metrics.csv"), index=False)
    json.dump(dict(vocab=vocab, embedding=np.round(E, 5).tolist(), rules=M[M.model == "GP"][["split", "evo_seed", "features", "rule"]].to_dict("records")), open(os.path.join(HERE, "rules.json"), "w"), indent=1)
    write_yaml(os.path.join(HERE, "config.yaml"), dict(CFG, provenance=provenance()))
    S = []; T = []
    for mdl, g in M.groupby("model"):
        ps = g.groupby(["split", "features"]).MAE.mean().unstack()
        for f in ps.columns:
            mm, lo, hi = boot_ci(ps[f]); S.append(dict(setting="Fe-Na-O-P splits", model=mdl, features=f, MAE=round(mm, 4), CI_lo=round(lo, 4), CI_hi=round(hi, 4)))
        for c in ["base_only", "base+random_gaussian_embedding", "base+shuffled_elements_embedding"]:
            T.append(dict(setting="Fe-Na-O-P splits", model=mdl, comparison=f"learned - {c}", **paired(ps["base+learned_embedding"], ps[c])))
    for st, g in TM.groupby("setting"):
        ps = g.groupby(["target", "features"]).MAE.mean().unstack()
        for f in ps.columns:
            mm, lo, hi = boot_ci(ps[f]); S.append(dict(setting=st, model="ridge", features=f, MAE=round(mm, 4), CI_lo=round(lo, 4), CI_hi=round(hi, 4)))
        pv = g.pivot_table(index=["target", "evo_seed", "draw"], columns="features", values="MAE")
        for c in ["none", "random_gaussian", "shuffled_elements"]: T.append(dict(setting=st, model="ridge", comparison=f"learned - {c}", **paired(pv["learned"], pv[c])))
    S = pd.DataFrame(S); S.to_csv(os.path.join(HERE, "summary.csv"), index=False); T = pd.DataFrame(T); T["holm_p"] = holm(T.wilcoxon_p.values); T.to_csv(os.path.join(HERE, "paired_tests.csv"), index=False)
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    os.makedirs(os.path.join(HERE, "figures"), exist_ok=True); fig, axs = plt.subplots(1, 2, figsize=(11, 4))
    b = R[R.kind == "subsample80"]; axs[0].hist(b.ARI, bins=10); axs[0].axvline(R[R.kind == "full"].ARI.iloc[0], color="k", ls="--", label="full data"); axs[0].axvline(b.null95.mean(), color="r", ls=":", label="null 95th pct")
    axs[0].set_xlabel("ARI vs IUPAC groups (80% compound subsamples)"); axs[0].legend()
    s = S[S.setting == "Fe-Na-O-P splits"]; lab = [f"{a}\n{b}" for a, b in zip(s.model, s.features)]
    axs[1].errorbar(range(len(s)), s.MAE, yerr=[s.MAE - s.CI_lo, s.CI_hi - s.MAE], fmt="o"); axs[1].set_xticks(range(len(s))); axs[1].set_xticklabels(lab, rotation=60, ha="right", fontsize=6); axs[1].set_ylabel("MAE (eV/atom, DFT)")
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "figures", "expt04_periodicity.png"), dpi=150)
    pd.set_option("display.width", 250); print(R.groupby("kind")[["ARI", "NN", "null95"]].agg(["mean", "std"])); print(S.to_string()); print(T.round(4).to_string()); print("runtime", time.time() - T0)
