"""M3 (exploratory, added after results were seen): SynthNN-style composition PU classifier as a task-matched baseline.
Faithful lightweight re-implementation of the SynthNN idea (Antoniuk et al., npj Comput. Mater. 2023): composition
fraction vector -> learned atom-embedding layer (atom2vec-like, trained end-to-end) -> MLP -> P(synthesised), trained
positive-unlabelled with unlabelled compositions drawn from enumerated candidate spaces and class re-weighting.
NOT the published SynthNN: no pretrained weights (pretrained SynthNN saw ICSD, i.e. our test compounds = leakage), smaller
network, no hyperparameter search. Retrained from scratch for every split on that split's information only:
  SYNTHNN-POOL : positives = target training formulas + observed formulas of the other selected systems with the target's
                 test formulas removed (exactly the information TPOOL uses); unlabelled = candidates of the same spaces.
  SYNTHNN-TARGET: positives = target training formulas only; unlabelled = target candidates.
Same splits, candidate pools, train-candidate removal and metrics as the frozen studies.  python run_m3.py decisive|replication"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"): os.environ[_v] = "1"
import sys, json, time, importlib.util
from multiprocessing import Pool
import numpy as np, pandas as pd, torch
STUDY = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__)); V05 = os.path.dirname(HERE)
SRC = {"decisive": "decisive_rf_template/run_decisive.py", "replication": "replication_rf_template/run_replication.py"}[STUDY]
sys.argv = [sys.argv[0]]
spec = importlib.util.spec_from_file_location("frozen", os.path.join(V05, SRC)); fz = importlib.util.module_from_spec(spec); spec.loader.exec_module(fz)
core = fz.core
VOC = sorted({e for s in fz.ALL for e in s.split("-")}); VI = {e: i for i, e in enumerate(VOC)}
EMB, STEPS, LR, WD = 30, 1500, 3e-3, 1e-4
GRID = [(h, r) for h in (64, 128) for r in (5, 20)]   # (hidden width, unlabelled:positive ratio), chosen per split by inner validation

def frac_matrix(system, rows):
    cs, _, _ = fz.space(system); T = np.array(cs.t, float)[rows]; F = np.zeros((len(rows), len(VOC)), np.float32)
    els = sorted(system.split("-"))
    for j, e in enumerate(els): F[:, VI[e]] = T[:, j]
    return F / F.sum(1, keepdims=True)

class Net(torch.nn.Module):
    def __init__(s, HID):
        super().__init__(); s.E = torch.nn.Linear(len(VOC), EMB, bias=False)          # atom embedding: fractions @ E
        s.f = torch.nn.Sequential(torch.nn.Linear(EMB, HID), torch.nn.ReLU(), torch.nn.Linear(HID, HID), torch.nn.ReLU(), torch.nn.Linear(HID, 1))
    def forward(s, x): return s.f(s.E(x)).squeeze(-1)

def train_score(P, U_pools, Xtarget, seed, HID=64, RATIO=5):
    """Fixed STEPS minibatch updates (batch 64 positives + RATIO*64 unlabelled, fresh unlabelled draws), class-weighted BCE."""
    torch.manual_seed(seed); rng = np.random.default_rng(seed); net = Net(HID); opt = torch.optim.Adam(net.parameters(), lr=LR, weight_decay=WD)
    P = torch.tensor(P); Uall = torch.tensor(np.vstack(U_pools)); bp = min(64, len(P)); bu = RATIO * bp
    y = torch.cat([torch.ones(bp), torch.zeros(bu)]); w = torch.where(y == 1, float(RATIO), 1.0)
    for _ in range(STEPS):
        X = torch.cat([P[torch.from_numpy(rng.integers(0, len(P), bp))], Uall[torch.from_numpy(rng.integers(0, len(Uall), bu))]])
        loss = (torch.nn.functional.binary_cross_entropy_with_logits(net(X), y, reduction="none") * w).mean()
        opt.zero_grad(); loss.backward(); opt.step()
    with torch.no_grad(): return torch.sigmoid(net(torch.tensor(Xtarget))).numpy().astype(float)

def fit_select(build, trc, Xt, seed):
    """build(train_cands) -> (P, U_pools). Inner validation: hide 25% of the target TRAINING positives, pick the GRID
    setting with the best inner recall@100 (test formulas never used), then refit on all training positives."""
    p = np.random.default_rng(seed + 7).permutation(trc); nv = max(2, len(p) // 4); iv, it = p[:nv], p[nv:]; best, bs = None, -1
    for h, r in GRID:
        P, U = build(it); sc = core.rank_metrics(train_score(P, U, Xt, seed, h, r), it, iv)["recall@100"]
        if sc > bs: best, bs = (h, r), sc
    P, U = build(trc); return train_score(P, U, Xt, seed, *best), best

def job(arg):
    torch.set_num_threads(1)
    s, (sid, tr, te) = arg; cs, pos, _ = fz.space(s); seed = int(sid[1:]); trc, tec = pos.cand_idx.values[tr], pos.cand_idx.values[te]; tk = set(pos.key.values[te])
    Xt = frac_matrix(s, np.arange(len(cs.t))); rng = np.random.default_rng(seed)
    Ut = np.setdiff1d(np.arange(len(cs.t)), trc); Ut = Ut[rng.choice(len(Ut), min(len(Ut), 4000), replace=False)]
    OP, OU = [], []
    for o in fz.ALL:
        if o == s: continue
        ocs, opos, _ = fz.space(o); keep = ~opos.key.isin(tk).values; pc = opos.cand_idx.values[keep]
        if len(pc): OP.append(frac_matrix(o, pc))
        uu = np.setdiff1d(np.arange(len(ocs.t)), pc); OU.append(frac_matrix(o, uu[rng.choice(len(uu), min(len(uu), 1000), replace=False)]))
    pool = lambda c: (np.vstack([Xt[c]] + OP), [Xt[np.setdiff1d(Ut, c)]] + OU)
    tgt = lambda c: (Xt[c], [Xt[np.setdiff1d(Ut, c)]])
    sp, hp = fit_select(pool, trc, Xt, seed); st, ht = fit_select(tgt, trc, Xt, seed)
    S = {"SYNTHNN-POOL (composition PU, pooled)": sp, "SYNTHNN-TARGET (composition PU, target only)": st}
    chosen = {"SYNTHNN-POOL (composition PU, pooled)": hp, "SYNTHNN-TARGET (composition PU, target only)": ht}
    mets, rows = [], []
    for m, v in S.items():
        r = core.rank_metrics(v, trc, tec); r.update(system=s, split=sid, method=m, hidden=chosen[m][0], ratio=chosen[m][1]); mets.append(r)
        sc = v.astype(float).copy(); sc[trc] = -np.inf
        for c, k, a in zip(tec, pos.key.values[te], pos.nelements.values[te]):
            rows.append(dict(system=s, split=sid, method=m, key=k, arity=int(a), n_greater=int((sc > sc[c]).sum()), n_tied=int((sc == sc[c]).sum())))
    print("done-job", s, sid, flush=True)
    return mets, rows

if __name__ == "__main__":
    T0 = time.time(); q = len(sys.argv) > 1
    jobs = [(s, sp) for s in fz.FRESH for sp in fz.splits(s, "A", 5)]
    with Pool(8) as p: out = p.map(job, jobs, chunksize=1)
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    pd.DataFrame([r for a, _ in out for r in a]).to_csv(os.path.join(HERE, "results", f"metrics_m3_{STUDY}.csv"), index=False)
    pd.DataFrame([r for _, b in out for r in b]).to_csv(os.path.join(HERE, "results", f"per_test_m3_{STUDY}.csv.gz"), index=False)
    print(STUDY, "done", round(time.time() - T0, 1), "s")
