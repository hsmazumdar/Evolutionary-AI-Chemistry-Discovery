"""Phase 7 / H1: discovery within each system (Protocols A and B). python scripts/run_h1_discovery.py [--quick]"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"): os.environ.setdefault(_v, "1")
import os, sys, json, time, argparse
from multiprocessing import Pool
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, HERE)
from shared.core import *
from shared.embed import emb_features
ap = argparse.ArgumentParser(); ap.add_argument("--quick", action="store_true"); A = ap.parse_args()
CFG = dict(rf_bags=10, ratio=5, ehp=dict(pop=200, gens=30, bags=5, ratio=3, archive_k=3), protocols=["A", "B"], n_splits=5)
if A.quick: CFG.update(rf_bags=2, ehp=dict(pop=30, gens=3, bags=2, ratio=3, archive_k=2), n_splits=1, protocols=["A"])
OUT = os.path.join(HERE, "results", "h1"); os.makedirs(OUT, exist_ok=True)

def methods(system, cs, pos_c, seed):
    Xc, Xo = cs.X, cs.Xo; Xe = np.hstack([Xc, emb_features(cs, system)])
    out = {"random": np.random.default_rng(seed).random(len(Xc)),
           "charge_balance (prior)": -Xo[:, -1] + 1e-4 * Xo[:, -2],
           "template_prior": template_prior(cs, pos_c),
           "nearest_positive": nearest_positive(Xc, pos_c),
           "PU_RF_leaf1": pu_generic(RF(1), Xc, pos_c, seed, CFG["rf_bags"], CFG["ratio"]),
           "PU_RF_leaf3": pu_generic(RF(3), Xc, pos_c, seed, CFG["rf_bags"], CFG["ratio"]),
           "PU_GB": pu_generic(GB, Xc, pos_c, seed, CFG["rf_bags"], CFG["ratio"]),
           "PU_logistic": pu_generic(LOGIT, Xc, pos_c, seed, CFG["rf_bags"], CFG["ratio"]),
           "PU_RF_ox (prior)": pu_generic(RF(1), Xo, pos_c, seed, CFG["rf_bags"], CFG["ratio"]),
           "PU_RF_embedding": pu_generic(RF(1), Xe, pos_c, seed, CFG["rf_bags"], CFG["ratio"])}
    t = time.time(); e = EHP(prim_names(), seed=seed, **CFG["ehp"]); hyps = e.fit(Xc, pos_c); out["EHP (proposed)"] = e.score(Xc, hyps, e.val, seed)
    return out, dict(ehp_time=time.time() - t, ehp_hyps=[dict(rule=h["str"], nodes=h["nodes"], conf=round(h.get("conf", 0), 4)) for h in hyps])

PU_BASELINES = ["template_prior", "nearest_positive", "PU_RF_leaf1", "PU_RF_leaf3", "PU_GB", "PU_logistic", "PU_RF_ox (prior)", "PU_RF_embedding"]

def job(arg):
    system, sid, tr, te = arg; cs, pos, _ = space(system); seed = int(sid[1:]); trc, tec = pos.cand_idx.values[tr], pos.cand_idx.values[te]
    t0 = time.time()
    # nested inner validation (training positives only) to pick the strongest PU baseline
    p = np.random.default_rng(500 + seed).permutation(trc); nv = max(2, len(p) // 4); iv, it = p[:nv], p[nv:]
    inner, _ = methods(system, cs, it, seed); inner_r = {m: rank_metrics(s, it, iv)["recall@100"] for m, s in inner.items()}
    best = max(PU_BASELINES, key=lambda m: (inner_r[m], m))
    sc, info = methods(system, cs, trc, seed); rows = []
    for m, s in sc.items():
        r = rank_metrics(s, trc, tec); r.update(system=system, protocol=sid[0], split=sid, method=m, inner_recall100=inner_r[m]); rows.append(r)
    r = rank_metrics(sc[best], trc, tec); r.update(system=system, protocol=sid[0], split=sid, method="strongest_PU_baseline (inner-selected)", selected=best, inner_recall100=inner_r[best]); rows.append(r)
    top = np.argsort(-np.where(np.isin(np.arange(len(cs.t)), trc), -np.inf, sc["EHP (proposed)"]))[:20]
    info.update(system=system, split=sid, selected_baseline=best, runtime_s=time.time() - t0, ehp_top20=[cs.name(j) for j in top])
    return rows, info

if __name__ == "__main__":
    T0 = time.time(); jobs = []
    for s in SYSTEMS:
        for pr in CFG["protocols"]:
            for sid, tr, te in splits(s, pr, CFG["n_splits"]): jobs.append((s, sid, tr, te))
    if A.quick: jobs = jobs[:2]
    with Pool(8) as pool: res = pool.map(job, jobs, chunksize=1)
    M = pd.DataFrame([r for x in res for r in x[0]]); M.to_csv(os.path.join(OUT, "metrics.csv"), index=False)
    json.dump([x[1] for x in res], open(os.path.join(OUT, "rules_and_runinfo.json"), "w"), indent=1)
    json.dump(CFG, open(os.path.join(OUT, "config.json"), "w"), indent=1)
    print(M.groupby(["protocol", "method"])[["recall@100", "recall@1000", "MRR", "median_rank"]].mean().round(3).to_string()); print("runtime", time.time() - T0)
