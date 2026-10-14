"""Expt-07: hidden-compound discovery with a positive-unlabelled (PU) protocol.  python reproduce.py [--quick]
Candidates: all 41k Fe_a Na_b O_c P_d formulas (a+b+c+d<=30, >=2 elements, reduced) = V03 candidate space.
Positives = training-partition compounds; unlabelled = every other candidate (the hidden test compounds are among them
and are never labelled). Score = PU-bagging probability (Mordelet & Vert 2014): K bags, each RF trained on all positives
vs a random unlabelled subsample, out-of-bag scoring. All hyperparameters fixed a priori (no test-based tuning).
Evaluation = V03 hits@k of hidden compounds in the ranked unseen candidates + median rank."""
import os, sys, json, time, argparse
from multiprocessing import Pool
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
from shared.common import load_poc, load_splits, mae, boot_ci, paired, holm, provenance, write_yaml, GP, ROOT
from evochem.discovery import CandidateSpace, base_score, hits, analogy_mask
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
ap = argparse.ArgumentParser(); ap.add_argument("--quick", action="store_true"); A = ap.parse_args()
KS = [10, 25, 50, 100, 200, 500, 1000]
CFG = dict(bags=30, unl_ratio=5, rf_trees=100, min_leaf=2, gp_pop=300, gp_gens=40, maxtot=30)
if A.quick: CFG.update(bags=3, rf_trees=20, gp_pop=40, gp_gens=3)
P = load_poc(); comps, y, X, Xo = P["comps"], P["y"], P["X"], P["Xo"]; EL = ["Fe", "Na", "O", "P"]
CS = CandidateSpace(EL, P["el"], CFG["maxtot"])
SPL = load_splits(P["df"]); SPL = {k: v for k, v in SPL.items() if k != "family_heldout"}
if A.quick: SPL = {k: SPL[k] for k in ["random_split_seed0"]}

def pu_scores(tr, F, seed, extra=None):
    pos = [CS.ix[CS.key(comps[i])] for i in tr if len(comps[i]) >= 2 and CS.key(comps[i]) in CS.ix]
    lab = np.zeros(len(CS.t), bool); lab[pos] = True; U = np.where(~lab)[0]
    FF = F if extra is None else np.column_stack([F, extra])
    rng = np.random.default_rng(seed); s = np.zeros(len(CS.t)); n = np.zeros(len(CS.t))
    for b in range(CFG["bags"]):
        ub = rng.choice(U, min(len(U), CFG["unl_ratio"] * len(pos)), replace=False)
        Xb = np.vstack([FF[pos], FF[ub]]); yb = np.r_[np.ones(len(pos)), np.zeros(len(ub))]
        clf = RandomForestClassifier(CFG["rf_trees"], min_samples_leaf=CFG["min_leaf"], random_state=seed * 100 + b, n_jobs=1).fit(Xb, yb)
        oob = np.ones(len(CS.t), bool); oob[ub] = False; oob[pos] = False
        s[oob] += clf.predict_proba(FF[oob])[:, 1]; n[oob] += 1
    return -(s / np.maximum(n, 1))   # lower = more likely (hits() ranks ascending)

def job(sname):
    tr, te = SPL[sname]["train"], SPL[sname]["test"]; seed = 0; out = []
    rf = RandomForestRegressor(300, random_state=seed, n_jobs=1).fit(X[tr], y[tr])
    e_rf, _ = base_score(rf.predict(CS.X), CS, comps, y, tr, X[tr], CS.X)
    gpo = GP(P["names_o"], pop_size=CFG["gp_pop"], generations=CFG["gp_gens"], seed=seed).fit(Xo[tr], y[tr])
    e_gpo, _ = base_score(gpo.predict(CS.Xo), CS, comps, y, tr, Xo[tr], CS.Xo)
    am = analogy_mask(CS, comps, tr)
    S = {"random": np.random.default_rng(seed).random(len(CS.t)),
         "charge_balance_only (ox. prior)": CS.Xo[:, -1],
         "V03 analogy ranked by GP_ox+hull (recomputed)": np.where(am, e_gpo, 1e6 + e_gpo),
         "PU_bagging_RF (element attributes only)": pu_scores(tr, CS.X, seed),
         "PU_bagging_RF + RF energy above training hull": pu_scores(tr, CS.X, seed, extra=e_rf),
         "PU_bagging_RF + ox. features (prior)": pu_scores(tr, CS.Xo, seed)}
    pu = S["PU_bagging_RF + ox. features (prior)"]
    S["PU(ox) restricted to analogy templates"] = np.where(am, pu, 1e6 + pu)
    preds = []
    for m, sc in S.items():
        h = hits(sc, CS, comps, tr, te, KS); order = h.pop("order"); h.update(split=sname, method=m); out.append(h)
        preds.extend(dict(split=sname, method=m, rank=r, candidate=CS.name(j)) for r, j in enumerate(order[:100]))
    return out, preds

if __name__ == "__main__":
    T0 = time.time()
    with Pool(8) as pool: res = pool.map(job, list(SPL))
    M = pd.DataFrame([r for x in res for r in x[0]]); M.to_csv(os.path.join(HERE, "metrics.csv"), index=False)
    pd.DataFrame([r for x in res for r in x[1]]).to_csv(os.path.join(HERE, "predictions.csv"), index=False)
    write_yaml(os.path.join(HERE, "config.yaml"), dict(CFG, n_candidates=len(CS.t), splits=list(SPL), provenance=provenance()))
    M["family"] = np.where(M.split.str.startswith("random"), "random_60_40", "group_heldout")
    S = M.groupby(["family", "method"])[[f"hits@{k}" for k in KS] + ["median_rank", "n_hidden_in_space"]].mean().round(2)
    S["random@100"] = M.groupby(["family", "method"])["random@100"].mean().round(3); S.to_csv(os.path.join(HERE, "summary.csv"))
    T = []
    for fam in ["random_60_40", "group_heldout"]:
        for met in ["hits@100", "hits@1000", "median_rank"]:
            pv = M[M.family == fam].pivot_table(index="split", columns="method", values=met)
            if pv.empty: continue
            for ref in ["PU_bagging_RF + ox. features (prior)", "PU_bagging_RF (element attributes only)"]:
                for c in ["V03 analogy ranked by GP_ox+hull (recomputed)", "charge_balance_only (ox. prior)", "random"]:
                    # for hits higher is better -> test (c - ref) so negative mean_diff means ref better
                    a, b = (pv[c], pv[ref]) if met.startswith("hits") else (pv[ref], pv[c])
                    T.append(dict(family=fam, metric=met, comparison=f"{ref} vs {c} (negative = {ref.split(' (')[0]} better)", **paired(a, b)))
    T = pd.DataFrame(T); T["holm_p"] = holm(T.wilcoxon_p.values); T.to_csv(os.path.join(HERE, "paired_tests.csv"), index=False)
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    os.makedirs(os.path.join(HERE, "figures"), exist_ok=True); fig, ax = plt.subplots(figsize=(8, 4.5)); r = M[M.family == "random_60_40"]
    for m in r.method.unique(): ax.plot(KS, [r[r.method == m][f"hits@{k}"].mean() for k in KS], "o-", label=m)
    ax.plot(KS, [r[r.method == "random"][f"random@{k}"].mean() for k in KS], "k--", label="expected random"); ax.set_xscale("log")
    ax.set_xlabel("top-k of ~41k candidates"); ax.set_ylabel("hidden real compounds found (mean, 10 random splits)"); ax.legend(fontsize=6)
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "figures", "expt07_recall_at_k.png"), dpi=150)
    pd.set_option("display.width", 250); print(S.to_string()); print(T.round(4).to_string()); print("runtime", time.time() - T0)
