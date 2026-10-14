"""H2: leave-one-system-out transfer (Protocol C). Source positives equal (same reduced formula) to any target TEST
positive are removed. python scripts/run_h2_transfer.py [--quick]"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"): os.environ.setdefault(_v, "1")
import sys, json, time, argparse
from multiprocessing import Pool
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, HERE)
from shared.core import *
ap = argparse.ArgumentParser(); ap.add_argument("--quick", action="store_true"); A = ap.parse_args()
CFG = dict(rf_bags=10, ratio=5, src_unl_per_system=3000, ehp=dict(pop=200, gens=30, bags=5, ratio=3, archive_k=3), n_splits=5)
if A.quick: CFG.update(rf_bags=2, ehp=dict(pop=30, gens=3, bags=2, ratio=3, archive_k=2), n_splits=1)
OUT = os.path.join(HERE, "results", "h2"); os.makedirs(OUT, exist_ok=True)

def source(target, test_keys, seed):
    XP, XU, T = [], [], []; rng = np.random.default_rng(seed)
    from collections import Counter; C = Counter()
    for s in SYSTEMS:
        if s == target: continue
        cs, pos, _ = space(s); keep = ~pos.key.isin(test_keys).values; pc = pos.cand_idx.values[keep]
        XP.append(cs.X[pc]); U = np.setdiff1d(np.arange(len(cs.t)), pos.cand_idx.values); XU.append(cs.X[rng.choice(U, CFG["src_unl_per_system"], replace=False)])
        C.update(tuple(sorted(x for x in cs.t[j] if x)) for j in pc)
    return np.vstack(XP), np.vstack(XU), C

def job(arg):
    target, sid, tr, te = arg; cs, pos, _ = space(target); seed = int(sid[1:]); trc, tec = pos.cand_idx.values[tr], pos.cand_idx.values[te]
    XP, XU, C = source(target, set(pos.key.values[te]), seed); n_removed = sum(len(space(s)[1]) for s in SYSTEMS if s != target) - len(XP)
    sc = {"PU_RF target-only": pu_generic(RF(1), cs.X, trc, seed, CFG["rf_bags"], CFG["ratio"]),
          "PU_RF pooled (source+target)": pu_generic(RF(1), cs.X, trc, seed, CFG["rf_bags"], CFG["ratio"], extra_pos=(XP, XU)),
          "template_prior target-only": template_prior(cs, trc), "template_prior pooled": template_prior(cs, trc, C)}
    # source-only zero-shot: classifier trained on source only
    clf = RF(1)(seed).fit(np.vstack([XP, XU]), np.r_[np.ones(len(XP)), np.zeros(len(XU))]); sc["PU_RF source-only zero-shot"] = clf.predict_proba(cs.X)[:, 1]
    e = EHP(prim_names(), seed=seed, **CFG["ehp"]); h = e.fit(cs.X, trc); sc["EHP target-only"] = e.score(cs.X, h, e.val, seed)
    e2 = EHP(prim_names(), seed=seed, **CFG["ehp"]); h2 = e2.fit(cs.X, trc, extra=(XP, XU)); sc["EHP pooled (source+target)"] = e2.score(cs.X, h2, e2.val, seed)
    rows = []
    for m, s in sc.items():
        r = rank_metrics(s, trc, tec); r.update(system=target, split=sid, method=m, source_positives=len(XP), source_positives_removed_as_target_test=n_removed); rows.append(r)
    return rows

if __name__ == "__main__":
    T0 = time.time(); jobs = [(s, sid, tr, te) for s in SYSTEMS for sid, tr, te in splits(s, "A", CFG["n_splits"])]
    if A.quick: jobs = jobs[:2]
    with Pool(8) as pool: res = pool.map(job, jobs, chunksize=1)
    M = pd.DataFrame([r for x in res for r in x]); M.to_csv(os.path.join(OUT, "metrics.csv"), index=False); json.dump(CFG, open(os.path.join(OUT, "config.json"), "w"), indent=1)
    print(M.groupby("method")[["recall@100", "recall@1000", "MRR"]].mean().round(3).to_string()); print("runtime", time.time() - T0)
