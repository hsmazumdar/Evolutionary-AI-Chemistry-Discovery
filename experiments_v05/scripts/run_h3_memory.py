"""H3: cumulative hypothesis memory over a stream of systems (Protocol D), 6 arms at matched GP generations per episode.
python scripts/run_h3_memory.py [--quick]"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"): os.environ.setdefault(_v, "1")
import sys, json, time, argparse, copy
from multiprocessing import Pool
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, HERE)
from shared.core import *
ap = argparse.ArgumentParser(); ap.add_argument("--quick", action="store_true"); A = ap.parse_args()
CFG = dict(orders=[0, 1, 2], pop=200, gens=30, bags=3, ratio=3, archive_k=3, buffer_pos=60, buffer_unl=600, ensemble_top=10, v04_keep=5)
if A.quick: CFG.update(orders=[0], pop=30, gens=3, bags=2)
ARMS = ["scratch", "sequential_finetune", "replay", "V04_archive", "full_data_retrain", "proposed_versioned_memory"]
OUT = os.path.join(HERE, "results", "h3"); os.makedirs(OUT, exist_ok=True)

def sysdata(s):
    cs, pos, _ = space(s); sid, tr, te = splits(s, "A", 1)[0]; return cs, pos, pos.cand_idx.values[tr], pos.cand_idx.values[te]

def job(arg):
    order_seed, arm = arg; order = list(np.random.default_rng(order_seed).permutation(SYSTEMS)); rng = np.random.default_rng(order_seed)
    D = {s: sysdata(s) for s in order}; gp_list = []; archive = []; buf_P = np.zeros((0, 22)); buf_U = np.zeros((0, 22)); buf_K = np.array([], object); allP, allU, allK = [], [], []
    memconf = {}; rows = []; evals = 0
    for k, s in enumerate(order):
        cs, pos, trc, tec = D[s]
        # leakage control: past positives equal to the current system's TEST formulas are dropped from replay/full data
        test_keys = set(pos.key[np.isin(pos.cand_idx.values, tec)])
        e = EHP(prim_names(), pop=CFG["pop"], gens=CFG["gens"], bags=CFG["bags"], ratio=CFG["ratio"], archive_k=CFG["archive_k"], seed=order_seed * 10 + k)
        if arm == "scratch": hyps = e.fit(cs.X, trc)
        elif arm == "sequential_finetune": hyps = e.fit(cs.X, trc, gp_list=gp_list)
        elif arm in ("replay", "proposed_versioned_memory", "V04_archive"):
            okb = ~np.isin(buf_K, list(test_keys)); ex = (buf_P[okb], buf_U) if okb.any() else None; hyps = e.fit(cs.X, trc, extra=ex, gp_list=gp_list)
        elif arm == "full_data_retrain":
            if allP:
                K = np.concatenate(allK); ok = ~np.isin(K, list(test_keys)); ex = (np.vstack(allP)[ok], np.vstack(allU))
            else: ex = None
            hyps = e.fit(cs.X, trc, extra=ex)
        evals += CFG["bags"] * CFG["gens"] * CFG["pop"]
        if arm == "V04_archive":
            archive = archive + hyps; e.score(cs.X, archive, e.val, k); archive = sorted(archive, key=lambda h: -h["conf"])[: CFG["v04_keep"]]; use = archive
        elif arm == "proposed_versioned_memory":
            for h in hyps: h["born"] = s
            archive = archive + hyps; e.score(cs.X, archive, e.val, k)
            memconf[s] = [h["conf"] for h in archive]   # per-system confidence version
            use = sorted(archive, key=lambda h: -h["conf"])[: CFG["ensemble_top"]]
        else: use = hyps
        cur = e.score(cs.X, use, e.val, k); r = rank_metrics(cur, trc, tec)
        rows.append(dict(order=order_seed, arm=arm, episode=k, system=s, eval_system=s, kind="new", **{m: r[m] for m in ["recall@100", "recall@500", "MRR"]}, memory_hypotheses=len(use) if arm != "proposed_versioned_memory" else len(archive), cum_gp_evals=evals))
        # retention on all earlier systems with the CURRENT model (proposed uses its stored per-system confidences)
        for j in order[:k]:
            csj, posj, trj, tej = D[j]
            if arm == "proposed_versioned_memory":
                conf = memconf[j]; hs = archive[: len(conf)]
                for h, c in zip(hs, conf): h["_c"] = c
                top = sorted(hs, key=lambda h: -h["_c"])[: CFG["ensemble_top"]]; S = np.zeros(len(csj.t)); W = 0
                for h in top:
                    if h["_c"] <= 0: continue
                    v = np.nan_to_num(h["gp"].predict(csj.X, h["tree"], h["scale"])); S += h["_c"] * v.argsort().argsort() / len(v); W += h["_c"]
                sj = S / max(W, 1e-9)
            else:
                ej = EHP(prim_names(), seed=0); sj = ej.score(csj.X, use, np.array(trj[: max(2, len(trj) // 4)]), k)
            rj = rank_metrics(sj, trj, tej)
            rows.append(dict(order=order_seed, arm=arm, episode=k, system=s, eval_system=j, kind="old", **{m: rj[m] for m in ["recall@100", "recall@500", "MRR"]}))
        # update buffers (positives of the current training split + unlabelled sample)
        U = np.setdiff1d(np.arange(len(cs.t)), pos.cand_idx.values); u = rng.choice(U, 300, replace=False)
        kk = pos.key.values[np.isin(pos.cand_idx.values, trc)]; kk = np.array([pos.key.values[np.where(pos.cand_idx.values == c)[0][0]] for c in trc], object)
        allP.append(cs.X[trc]); allU.append(cs.X[u]); allK.append(kk)
        buf_P = np.vstack([buf_P, cs.X[trc]]); buf_U = np.vstack([buf_U, cs.X[u]]); buf_K = np.concatenate([buf_K, kk])
        if len(buf_P) > CFG["buffer_pos"]:
            j = rng.choice(len(buf_P), CFG["buffer_pos"], replace=False); buf_P, buf_K = buf_P[j], buf_K[j]
        if len(buf_U) > CFG["buffer_unl"]: buf_U = buf_U[rng.choice(len(buf_U), CFG["buffer_unl"], replace=False)]
    return rows

if __name__ == "__main__":
    T0 = time.time()
    with Pool(8) as pool: res = pool.map(job, [(o, a) for o in CFG["orders"] for a in ARMS], chunksize=1)
    M = pd.DataFrame([r for x in res for r in x]); M.to_csv(os.path.join(OUT, "metrics.csv"), index=False); json.dump(CFG, open(os.path.join(OUT, "config.json"), "w"), indent=1)
    print(M[M.kind == "new"].groupby("arm")["recall@100"].mean().round(3)); print(M[M.kind == "old"].groupby("arm")["recall@100"].mean().round(3)); print("runtime", time.time() - T0)
