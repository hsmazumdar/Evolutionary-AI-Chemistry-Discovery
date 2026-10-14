"""Replication of the frozen decisive comparison (code identical except system lists) (see PREREGISTRATION.md). python run_decisive.py [--quick]"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"): os.environ.setdefault(_v, "1")
import sys, json, time, argparse
from collections import Counter
from multiprocessing import Pool
import numpy as np, pandas as pd
from scipy.stats import rankdata, wilcoxon
D = os.path.dirname(os.path.abspath(__file__)); V05 = os.path.dirname(D); sys.path.insert(0, V05)
import shared.core as core
from shared.core import space, splits, rank_metrics, pu_generic, RF, SYSTEMS as V05_SYSTEMS
ap = argparse.ArgumentParser(); ap.add_argument("--quick", action="store_true"); A = ap.parse_args()
_V = pd.read_csv(os.path.join(V05, "data", "formulas_v05.csv")); _F = pd.concat([pd.read_csv(os.path.join(V05, "decisive_rf_template", "data", "formulas_fresh.csv")), pd.read_csv(os.path.join(D, "data", "formulas_fresh.csv"))], ignore_index=True)
core.formulas = lambda: pd.concat([_V, _F], ignore_index=True)          # space() reads formulas() at call time
DEC = json.load(open(os.path.join(V05, "decisive_rf_template", "data", "MANIFEST.json")))["fresh_systems"]; FRESH = json.load(open(os.path.join(D, "data", "MANIFEST.json")))["fresh_systems"]; ALL = V05_SYSTEMS + DEC + FRESH
W = [round(0.1 * i, 1) for i in range(1, 10)]; BAGS, RATIO = (2, 5) if A.quick else (10, 5)
rn = lambda v: (rankdata(v, method="average") - 1) / (len(v) - 1)
tpl = lambda t: tuple(sorted(x for x in t if x))

def source_counter(target, test_keys, strict):
    C = Counter(); tels = set(target.split("-"))
    for s in ALL:
        if s == target: continue
        cs, pos, _ = space(s); keep = ~pos.key.isin(test_keys).values
        if strict: keep &= ~pos.composition.apply(lambda c: set(json.loads(c)) <= tels).values
        C.update(tpl(cs.t[j]) for j in pos.cand_idx.values[keep])
    return C

def tpool(cs, pos_c, C): return core.template_prior(cs, pos_c, C)

def choose_w(cs, pos, tr, C, seed):
    fam = pos.formula_anonymous.values[tr]; u = np.array(sorted(set(fam))); np.random.default_rng(seed).shuffle(u)
    sc = {w: [] for w in W}
    for f in range(3):
        held = set(u[f::3]); itr = tr[~np.isin(fam, list(held))]; ite = tr[np.isin(fam, list(held))]
        if len(ite) == 0 or len(itr) < 3: continue
        a, b = pos.cand_idx.values[itr], pos.cand_idx.values[ite]
        r1, r2 = rn(pu_generic(RF(1), cs.X, a, seed * 10 + f, BAGS, RATIO)), rn(tpool(cs, a, C))
        for w in W: sc[w].append(rank_metrics(w * r1 + (1 - w) * r2, a, b)["recall@100"])
    m = {w: np.mean(v) for w, v in sc.items()}; best = max(m.values()); return min(w for w in W if m[w] == best), m

def job(arg):
    s, (sid, tr, te) = arg; cs, pos, _ = space(s); seed = int(sid[1:]); trc, tec = pos.cand_idx.values[tr], pos.cand_idx.values[te]; tk = set(pos.key.values[te])
    rows = []; C = source_counter(s, tk, False); Cs = source_counter(s, tk, True)
    rf = pu_generic(RF(1), cs.X, trc, seed, BAGS, RATIO); tp = tpool(cs, trc, C); tps = tpool(cs, trc, Cs)
    w, inner = choose_w(cs, pos, tr, C, seed); ws, _ = choose_w(cs, pos, tr, Cs, seed)
    S = {"BLEND (RF + pooled template)": w * rn(rf) + (1 - w) * rn(tp), "TPOOL (pooled template)": tp, "RF alone": rf,
         "template target-only": core.template_prior(cs, trc), "random": np.random.default_rng(seed).random(len(cs.t)),
         "BLEND strict-leakage": ws * rn(rf) + (1 - ws) * rn(tps), "TPOOL strict-leakage": tps}
    for m, v in S.items():
        r = rank_metrics(v, trc, tec); r.update(system=s, split=sid, method=m, w=w if m.startswith("BLEND (") else (ws if m.startswith("BLEND s") else np.nan), source_templates=sum(C.values())); rows.append(r)
    return rows

if __name__ == "__main__":
    T0 = time.time(); SY = FRESH[:2] if A.quick else FRESH; NS = 1 if A.quick else 5
    jobs = [(s, sp) for s in SY for sp in splits(s, "A", NS)]
    with Pool(8) as p: M = pd.DataFrame([r for x in p.map(job, jobs, chunksize=1) for r in x])
    out = os.path.join(D, "results"); M.to_csv(f"{out}/metrics{'_quick' if A.quick else ''}.csv", index=False)
    print(M.groupby("method")[["recall@100", "recall@500", "MRR"]].mean().round(3)); print("runtime", round(time.time() - T0, 1))
