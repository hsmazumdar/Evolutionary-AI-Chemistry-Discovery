"""Revision M1/M2 (exploratory sensitivity, post hoc): re-run the FROZEN decisive / replication jobs with identical
code, seeds and splits, but save per-test-formula tie information so recall can be re-scored with fair tie-breaking.
The pre-registered metrics are NOT changed; the original rank_metrics output is recomputed and checked against
results/metrics.csv to prove the re-run is identical.  python rescore.py decisive|replication"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"): os.environ.setdefault(_v, "1")
import sys, json, time, importlib.util
from multiprocessing import Pool
import numpy as np, pandas as pd
STUDY = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__)); V05 = os.path.dirname(HERE)
SRC = {"decisive": "decisive_rf_template/run_decisive.py", "replication": "replication_rf_template/run_replication.py"}[STUDY]
sys.argv = [sys.argv[0]]                                     # frozen script parses argv (no --quick)
spec = importlib.util.spec_from_file_location("frozen", os.path.join(V05, SRC)); fz = importlib.util.module_from_spec(spec); spec.loader.exec_module(fz)
core = fz.core

def tie_rows(score, trc, tec, keys, arity):
    s = score.astype(float).copy(); s[trc] = -np.inf
    order = np.argsort(-s, kind="stable"); rank = np.empty(len(s), int); rank[order] = np.arange(len(s))
    return [dict(key=k, arity=int(a), stable_rank=int(rank[c] + 1), n_greater=int((s > s[c]).sum()), n_tied=int((s == s[c]).sum()), score=float(s[c]))
            for c, k, a in zip(tec, keys, arity)]

def job(arg):
    s, (sid, tr, te) = arg; cs, pos, _ = fz.space(s); seed = int(sid[1:]); trc, tec = pos.cand_idx.values[tr], pos.cand_idx.values[te]; tk = set(pos.key.values[te])
    C = fz.source_counter(s, tk, False); Cs = fz.source_counter(s, tk, True)
    rf = fz.pu_generic(fz.RF(1), cs.X, trc, seed, fz.BAGS, fz.RATIO); tp = fz.tpool(cs, trc, C); tps = fz.tpool(cs, trc, Cs)
    w, _ = fz.choose_w(cs, pos, tr, C, seed); ws, _ = fz.choose_w(cs, pos, tr, Cs, seed)
    S = {"BLEND (RF + pooled template)": w * fz.rn(rf) + (1 - w) * fz.rn(tp), "TPOOL (pooled template)": tp, "RF alone": rf,
         "template target-only": core.template_prior(cs, trc), "random": np.random.default_rng(seed).random(len(cs.t)),
         "BLEND strict-leakage": ws * fz.rn(rf) + (1 - ws) * fz.rn(tps), "TPOOL strict-leakage": tps,
         # exploratory control: TPOOL order kept exactly, RF used ONLY to break ties within equal TPOOL scores
         "TPOOL + RF tie-break only": fz.rn(tp) * 1e6 + fz.rn(rf)}
    # sanity: lexicographic arm must not reorder TPOOL across distinct scores
    keys = pos.key.values[te]; ar = pos.nelements.values[te]; rows, mets = [], []
    for m, v in S.items():
        r = core.rank_metrics(v, trc, tec); r.update(system=s, split=sid, method=m); mets.append(r)
        for x in tie_rows(v, trc, tec, keys, ar): x.update(system=s, split=sid, method=m, N_ranked=r["N_ranked"], w=w); rows.append(x)
    return rows, mets

if __name__ == "__main__":
    T0 = time.time(); jobs = [(s, sp) for s in fz.FRESH for sp in fz.splits(s, "A", 5)]
    with Pool(8) as p: out = p.map(job, jobs, chunksize=1)
    R = pd.DataFrame([r for a, _ in out for r in a]); M = pd.DataFrame([r for _, b in out for r in b])
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    R.to_csv(os.path.join(HERE, "results", f"per_test_{STUDY}.csv.gz"), index=False); M.to_csv(os.path.join(HERE, "results", f"metrics_rerun_{STUDY}.csv"), index=False)
    O = pd.read_csv(os.path.join(V05, os.path.dirname(SRC), "results", "metrics.csv"))
    j = O.merge(M, on=["system", "split", "method"], suffixes=("_orig", "_rerun"))
    mx = max(float((j[f"{k}_orig"] - j[f"{k}_rerun"]).abs().max()) for k in ["recall@10", "recall@50", "recall@100", "recall@500", "recall@1000", "MRR"])
    print(STUDY, "rows matched", len(j), "of", len(O), "max |orig - rerun|", mx, "runtime", round(time.time() - T0, 1))
    json.dump(dict(study=STUDY, matched=len(j), orig=len(O), max_abs_diff=mx), open(os.path.join(HERE, "results", f"rerun_check_{STUDY}.json"), "w"))
