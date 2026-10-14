"""EXPLORATORY (not confirmatory, per protocol §1): (1) EHP ablations on Protocol A; (2) redesigned contradiction
diagnostics: observed formulas that a cross-fitted PU model ranks below most unlabelled candidates, compared with a
permutation null, and tested for association with provenance/energy labels.
python scripts/run_exploratory.py [--quick]"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"): os.environ.setdefault(_v, "1")
import sys, json, time, argparse
from multiprocessing import Pool
import numpy as np, pandas as pd
from scipy.stats import mannwhitneyu, spearmanr
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, HERE)
from shared.core import *
ap = argparse.ArgumentParser(); ap.add_argument("--quick", action="store_true"); A = ap.parse_args()
NS = 1 if A.quick else 5; SYS = SYSTEMS[:2] if A.quick else SYSTEMS; G = 3 if A.quick else 30
OUT = os.path.join(HERE, "results", "exploratory"); os.makedirs(OUT, exist_ok=True)
rn = lambda v: v.argsort().argsort() / len(v)

def abl(arg):
    s, (sid, tr, te) = arg; cs, pos, _ = space(s); c = pos.cand_idx.values; trc, tec = c[tr], c[te]; seed = int(sid[1:]); out = {}
    t0 = time.time(); e = EHP(prim_names(), gens=G, seed=seed); H = e.fit(cs.X, trc); base = e.score(cs.X, H, e.val, seed); out["EHP (as H1)"] = base
    V = [rn(np.nan_to_num(h["gp"].predict(cs.X, h["tree"], h["scale"]))) for h in H]; C = np.array([h["conf"] for h in H])
    out["EHP uniform weights"] = np.mean([v for v, w in zip(V, C) if w > 0] or V, 0)
    out["EHP top-1 hypothesis"] = V[int(np.argmax(C))]
    e3 = EHP(prim_names(), gens=3 * G, seed=seed); H3 = e3.fit(cs.X, trc); out["EHP 3x generations"] = e3.score(cs.X, H3, e3.val, seed)
    e2 = EHP(prim_names(), gens=G, bags=15, seed=seed); H2 = e2.fit(cs.X, trc); out["EHP 3x bags"] = e2.score(cs.X, H2, e2.val, seed)
    tp = template_prior(cs, trc); out["template_prior"] = tp; out["EHP + template (rank mean)"] = 0.5 * rn(base) + 0.5 * rn(tp)
    rf = pu_generic(RF(1), cs.X, trc, seed, 10, 5); out["PU_RF_leaf1"] = rf; out["PU_RF + template (rank mean)"] = 0.5 * rn(rf) + 0.5 * rn(tp)
    return [dict(system=s, split=sid, method=m, **{k: v for k, v in rank_metrics(sc, trc, tec).items() if not k.startswith("random")}) for m, sc in out.items()]

def contra(s):
    cs, pos, _ = space(s); c = pos.cand_idx.values; P = len(c); rng = np.random.default_rng(0); fold = rng.permutation(P) % 5
    pct = np.zeros(P); U = np.setdiff1d(np.arange(len(cs.t)), c)
    for f in range(5):
        trc = c[fold != f]; sc = pu_generic(RF(1), cs.X, trc, f, 10, 5); u = sc[U]
        for i in np.where(fold == f)[0]: pct[i] = (u < sc[c[i]]).mean()   # percentile among unlabelled
    flag = pct < 0.5                                                          # ranked below the median unlabelled candidate
    # permutation null: random unlabelled "pseudo-positives" of equal count injected as positives, same procedure
    null = []
    for r in range(3 if A.quick else 20):
        fake = rng.choice(U, P, replace=False); fk = rng.permutation(P) % 5; pf = np.zeros(P); U2 = np.setdiff1d(U, fake)
        for f in range(5):
            sc = pu_generic(RF(1), cs.X, fake[fk != f], 100 + r, 5, 5); u = sc[U2]
            for i in np.where(fk == f)[0]: pf[i] = (u < sc[fake[i]]).mean()
        null.append(float((pf < 0.5).mean()))
    d = pos.assign(pct_among_unlabelled=pct, contradiction=flag); res = dict(system=s, n_observed=P, frac_flagged=float(flag.mean()), null_frac_mean=float(np.mean(null)), null_frac_p95=float(np.percentile(null, 95)),
        perm_p=float((np.sum(np.array(null) <= flag.mean()) + 1) / (len(null) + 1)))
    for col in ["dft_ehull_min_eV_atom", "dft_Ef_observed_min_eV_atom", "n_polymorphs_observed", "n_icsd_unique"]:
        x = d[col].astype(float); ok = x.notna()
        res[f"spearman_pct_vs_{col}"] = float(spearmanr(d.pct_among_unlabelled[ok], x[ok])[0]) if ok.sum() > 5 else None
        if flag[ok].sum() >= 3 and (~flag[ok]).sum() >= 3: res[f"MWU_p_{col}"] = float(mannwhitneyu(x[ok & flag], x[ok & ~flag]).pvalue)
    return res, d[["system", "formula", "pct_among_unlabelled", "contradiction", "n_icsd_unique", "dft_ehull_min_eV_atom"]]

if __name__ == "__main__":
    T0 = time.time(); jobs = [(s, sp) for s in SYS for sp in splits(s, "A", NS)]
    with Pool(8) as pool:
        M = pd.DataFrame([r for x in pool.map(abl, jobs, chunksize=1) for r in x]); C = pool.map(contra, SYS)
    M.to_csv(f"{OUT}/ablation_metrics.csv", index=False)
    pd.DataFrame([c[0] for c in C]).to_csv(f"{OUT}/contradiction_summary.csv", index=False); pd.concat([c[1] for c in C]).to_csv(f"{OUT}/contradiction_formulas.csv", index=False)
    print(M.groupby("method")[["recall@100", "recall@1000", "MRR"]].mean().round(3).sort_values("recall@100")); print(pd.DataFrame([c[0] for c in C]).iloc[:, :7].round(3).to_string()); print("runtime", time.time() - T0)
