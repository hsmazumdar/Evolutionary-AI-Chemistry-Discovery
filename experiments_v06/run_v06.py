"""V06 confirmatory runner (PREREG_V06). Modes:
  python run_v06.py smoke        -> pipeline check on unsealed V05 primary systems (2 systems, 1 split, reduced effort); NOT results
  python run_v06.py e1           -> E1/E3/E4 on the 80 V06 systems, 5 random splits each (protocol A, as V05)
  python run_v06.py e2           -> E2 temporal split (train year<=2010, test 2011-2025) on the 80 V06 systems
Pooled template source = the other systems of the same study (V06 set). Primitive element features only for learned arms;
C1 (charge neutrality) is a labelled domain-knowledge ablation and never enters a confirmatory test."""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"): os.environ[_v] = "1"
import sys, json, time, itertools
from collections import Counter
from multiprocessing import Pool
import numpy as np, pandas as pd, torch
from scipy.stats import rankdata
D = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(D); V05 = os.path.join(ROOT, "experiments_v05"); sys.path.insert(0, V05)
import shared.core as core
from shared.core import space, splits, pu_generic, RF, GB, SYSTEMS as V05_SYSTEMS
MODE = sys.argv[1]; SMOKE = MODE == "smoke"; SEED0 = 20261021
if SMOKE:
    STUDY = V05_SYSTEMS; RUN = V05_SYSTEMS[:2]; NS = 1
else:
    _F = pd.read_csv(os.path.join(D, "data", "formulas_v06.csv")); core.formulas = lambda: _F
    STUDY = json.load(open(os.path.join(D, "data", "MANIFEST.json")))["fresh_systems"]; RUN = STUDY; NS = 5
BAGS, RATIO = (2, 5) if SMOKE else (10, 5); STEPS = 200 if SMOKE else 1500
W = [round(0.1 * i, 1) for i in range(0, 11)]                     # PREREG_V06 s2: w grid {0, 0.1, ..., 1}
KS = [10, 50, 100, 500, 1000]
rn = lambda v: (rankdata(v, method="average") - 1) / (len(v) - 1)
tpl = lambda t: tuple(sorted(x for x in t if x))

# ---------- temporal labels (E2) ----------
YEARS = {}
if MODE == "e2":
    Y = pd.read_csv(os.path.join(D, "data", "first_report_year.csv")); YEARS = dict(zip(Y.key, Y.year))
def yr(k): v = YEARS.get(k, np.nan); return np.nan if pd.isna(v) else int(v)

# ---------- metrics: tie-fair expected recall (primary), stable (secondary) ----------
def metrics(score, remove, test):
    s = score.astype(float).copy(); s[remove] = -np.inf; st = s[test]
    srt = np.sort(s); g = len(s) - np.searchsorted(srt, st, "right"); t = np.searchsorted(srt, st, "right") - np.searchsorted(srt, st, "left")
    order = np.argsort(-s, kind="stable"); rank = np.empty(len(s), int); rank[order] = np.arange(len(s)); r = rank[test] + 1
    m = dict(n_test=len(test), N_ranked=int(len(s) - len(set(np.r_[remove]))))
    for k in KS:
        m[f"recall@{k}"] = float(np.mean(np.clip((k - g) / t, 0, 1))) if len(test) else np.nan
        m[f"stable_recall@{k}"] = float(np.mean(r <= k)) if len(test) else np.nan
    m["MRR"] = float(np.mean(1.0 / r)) if len(test) else np.nan
    return m

# ---------- Magpie features (B1) ----------
from matminer.utils.data import MagpieData
from pymatgen.core import Element
MPROPS = ["Number", "MendeleevNumber", "AtomicWeight", "MeltingT", "Column", "Row", "CovalentRadius", "Electronegativity", "NsValence", "NpValence",
          "NdValence", "NfValence", "NValence", "NsUnfilled", "NpUnfilled", "NdUnfilled", "NfUnfilled", "NUnfilled", "GSvolume_pa", "GSbandgap", "GSmagmom", "SpaceGroupNumber"]
_MD = MagpieData()
def magpie_X(cs):
    els = sorted(cs.EL); P = np.array([[_MD.get_elemental_property(Element(e), p) for p in MPROPS] for e in els], float)
    T = np.array(cs.t, float); F = T / T.sum(1, keepdims=True); mean = F @ P; dev = F @ np.abs(P[None] - mean[:, None, :]).transpose(1, 0, 2).reshape(len(els), -1).reshape(len(els), len(F), -1).transpose(1, 0, 2).sum(1) if False else np.einsum("ne,nep->np", F, np.abs(P[None, :, :] - mean[:, None, :]))
    pres = T > 0; big = np.where(pres[:, :, None], P[None], np.nan)
    mn, mx = np.nanmin(big, 1), np.nanmax(big, 1)
    return np.hstack([mean, dev, mn, mx, mx - mn, (T > 0).sum(1, keepdims=True), np.sort(F, 1)])

# ---------- composition networks (B2 Roost-style, SynthNN-style) ----------
VOC = sorted({e for s in STUDY for e in s.split("-")}); VI = {e: i for i, e in enumerate(VOC)}
def comp_tensors(cs):
    els = sorted(cs.EL); T = np.array(cs.t, float); F = T / T.sum(1, keepdims=True)
    return torch.tensor([VI[e] for e in els]).repeat(len(T), 1), torch.tensor(F, dtype=torch.float32)
class Roost(torch.nn.Module):
    """Roost-style: learned element embeddings (from one-hot identity only), 2 rounds of fraction-weighted soft-attention message passing, weighted attention pooling."""
    def __init__(s, H=32, L=2):
        super().__init__(); s.E = torch.nn.Embedding(len(VOC), H)
        s.msg = torch.nn.ModuleList([torch.nn.Sequential(torch.nn.Linear(2 * H, H), torch.nn.SiLU(), torch.nn.Linear(H, H)) for _ in range(L)])
        s.gate = torch.nn.ModuleList([torch.nn.Sequential(torch.nn.Linear(2 * H, H), torch.nn.SiLU(), torch.nn.Linear(H, 1)) for _ in range(L)])
        s.pg = torch.nn.Sequential(torch.nn.Linear(H, H), torch.nn.SiLU(), torch.nn.Linear(H, 1)); s.out = torch.nn.Sequential(torch.nn.Linear(H, 64), torch.nn.SiLU(), torch.nn.Linear(64, 1))
    def forward(s, idx, f):
        h = s.E(idx); mask = f > 0; n = h.shape[1]
        for msg, gate in zip(s.msg, s.gate):
            pair = torch.cat([h[:, :, None].expand(-1, -1, n, -1), h[:, None].expand(-1, n, -1, -1)], -1)
            a = gate(pair).squeeze(-1) + torch.log(f[:, None, :].clamp_min(1e-9)); a = a.masked_fill(~mask[:, None, :], -1e9)
            h = h + (torch.softmax(a, -1)[..., None] * msg(pair)).sum(2)
        a = (s.pg(h).squeeze(-1) + torch.log(f.clamp_min(1e-9))).masked_fill(~mask, -1e9)
        return s.out((torch.softmax(a, -1)[..., None] * h).sum(1)).squeeze(-1)
class SynthNN(torch.nn.Module):                                   # as V05 revision M3, fixed (64, ratio 5)
    def __init__(s, H=64):
        super().__init__(); s.E = torch.nn.Linear(len(VOC), 30, bias=False); s.f = torch.nn.Sequential(torch.nn.Linear(30, H), torch.nn.ReLU(), torch.nn.Linear(H, H), torch.nn.ReLU(), torch.nn.Linear(H, 1))
    def forward(s, idx, f): x = torch.zeros(len(f), len(VOC)).scatter_add_(1, idx, f); return s.f(s.E(x)).squeeze(-1)
def train_net(make, IDX, FR, P_rows, U_rows, seed, extra=None):
    """PU training: positives P_rows (+extra pooled positives), unlabelled U_rows of the target space (+extra unlabelled); class-weighted BCE; fixed steps."""
    torch.manual_seed(seed); rng = np.random.default_rng(seed); net = make(); opt = torch.optim.Adam(net.parameters(), lr=3e-3, weight_decay=1e-4)
    Pi, Pf, Ui, Uf = IDX[P_rows], FR[P_rows], IDX[U_rows], FR[U_rows]
    if extra is not None: Pi, Pf, Ui, Uf = torch.cat([Pi, extra[0]]), torch.cat([Pf, extra[1]]), torch.cat([Ui, extra[2]]), torch.cat([Uf, extra[3]])
    bp = min(64, len(Pi)); bu = 5 * bp; y = torch.cat([torch.ones(bp), torch.zeros(bu)]); w = torch.where(y == 1, 5.0, 1.0)
    for _ in range(STEPS):
        a, b = torch.from_numpy(rng.integers(0, len(Pi), bp)), torch.from_numpy(rng.integers(0, len(Ui), bu))
        loss = (torch.nn.functional.binary_cross_entropy_with_logits(net(torch.cat([Pi[a], Ui[b]]), torch.cat([Pf[a], Uf[b]])), y, reduction="none") * w).mean()
        opt.zero_grad(); loss.backward(); opt.step()
    with torch.no_grad(): return np.concatenate([net(IDX[i:i + 8192], FR[i:i + 8192]).numpy() for i in range(0, len(IDX), 8192)]).astype(float)

# ---------- C1: charge-neutrality ablation (domain knowledge, labelled) ----------
def neutral_mask(cs):
    els = sorted(cs.EL); ox = [list(Element(e).common_oxidation_states) or [0] for e in els]; T = np.array(cs.t)
    ok = np.zeros(len(T), bool)
    for combo in itertools.product(*ox): ok |= (T @ np.array(combo)) == 0
    return ok

# ---------- helpers ----------
def source_counter(target, exclude_keys, strict, year_max=None):
    C = Counter(); tels = set(target.split("-"))
    for s in STUDY:
        if s == target: continue
        cs, pos, _ = space(s); keep = ~pos.key.isin(exclude_keys).values
        if strict: keep &= ~pos.composition.apply(lambda c: set(json.loads(c)) <= tels).values
        if year_max is not None: keep &= np.array([(not np.isnan(yr(k))) and yr(k) <= year_max for k in pos.key], bool)
        C.update(tpl(cs.t[j]) for j in pos.cand_idx.values[keep])
    return C
def pooled_net_extra(target, exclude_keys, rng, year_max=None):
    Pi, Pf, Ui, Uf = [], [], [], []
    for o in STUDY:
        if o == target: continue
        ocs, opos, _ = space(o); keep = ~opos.key.isin(exclude_keys).values
        if year_max is not None: keep &= np.array([(not np.isnan(yr(k))) and yr(k) <= year_max for k in opos.key], bool)
        I, F = comp_tensors(ocs); pc = opos.cand_idx.values[keep]
        if len(pc): Pi.append(I[pc]); Pf.append(F[pc])
        uu = np.setdiff1d(np.arange(len(ocs.t)), opos.cand_idx.values); uu = rng.choice(uu, min(len(uu), 1000), replace=False); Ui.append(I[uu]); Uf.append(F[uu])
    return torch.cat(Pi), torch.cat(Pf), torch.cat(Ui), torch.cat(Uf)

def learned_scores(cs, trc, seed, Xm, IDX, FR, extra):
    U = np.setdiff1d(np.arange(len(cs.t)), trc); rng = np.random.default_rng(seed); Us = rng.choice(U, min(len(U), 4000), replace=False)
    return {"PU-RF": pu_generic(RF(1), cs.X, trc, seed, BAGS, RATIO), "B1 Magpie-GB PU": pu_generic(GB, Xm, trc, seed, BAGS, RATIO),
            "B2 Roost-style PU": train_net(Roost, IDX, FR, trc, Us, seed), "SynthNN-style pooled": train_net(SynthNN, IDX, FR, trc, Us, seed, extra)}

def inner(cs, pos, tr, C, seed, Xm, IDX, FR, extra):
    """Family-grouped 3-fold inner validation on TRAINING positives only: per learned arm, its own inner recall@100 and the best blend w with TPOOL."""
    fam = pos.formula_anonymous.values[tr]; u = np.array(sorted(set(fam))); np.random.default_rng(seed).shuffle(u)
    sc = {}; own = {}
    for f in range(3):
        held = set(u[f::3]); itr = tr[~np.isin(fam, list(held))]; ite = tr[np.isin(fam, list(held))]
        if len(ite) == 0 or len(itr) < 3: continue
        a, b = pos.cand_idx.values[itr], pos.cand_idx.values[ite]; tp = rn(core.template_prior(cs, a, C))
        for arm, v in learned_scores(cs, a, seed * 10 + f, Xm, IDX, FR, extra).items():
            own.setdefault(arm, []).append(metrics(v, a, b)["recall@100"]); r1 = rn(v)
            for w in W: sc.setdefault(arm, {}).setdefault(w, []).append(metrics(w * r1 + (1 - w) * tp, a, b)["recall@100"])
    wbest = {arm: min(w for w in W if np.mean(d[w]) == max(np.mean(x) for x in d.values())) for arm, d in sc.items()}
    return wbest, {arm: float(np.mean(v)) for arm, v in own.items()}

def job(arg):
    torch.set_num_threads(1)
    s, (sid, tr, te, drop) = arg; cs, pos, _ = space(s); seed = SEED0 + 1000 * int(sid[1:]) if MODE == "e2" else int(sid[1:])
    trc, tec = pos.cand_idx.values[tr], pos.cand_idx.values[te]; remove = np.r_[trc, pos.cand_idx.values[drop]].astype(int); tk = set(pos.key.values[te]) | set(pos.key.values[drop])
    ymax = 2010 if MODE == "e2" else None
    C = source_counter(s, tk, False, ymax); Cs = source_counter(s, tk, True, ymax)
    Xm = magpie_X(cs); IDX, FR = comp_tensors(cs); extra = pooled_net_extra(s, tk, np.random.default_rng(seed), ymax)
    L = learned_scores(cs, trc, seed, Xm, IDX, FR, extra); tp = core.template_prior(cs, trc, C); tps = core.template_prior(cs, trc, Cs)
    wb, own = inner(cs, pos, tr, C, seed, Xm, IDX, FR, extra)
    best_learned = max(own, key=lambda a: (own[a], a))                       # chosen on inner folds only
    nm = neutral_mask(cs)
    S = {"TPOOL": tp, "template target-only": core.template_prior(cs, trc), "random": np.random.default_rng(seed).random(len(cs.t)), "TPOOL strict-leakage": tps,
         "BLEND (RF + TPOOL)": wb["PU-RF"] * rn(L["PU-RF"]) + (1 - wb["PU-RF"]) * rn(tp),
         "B3a BLEND (Magpie-GB + TPOOL)": wb["B1 Magpie-GB PU"] * rn(L["B1 Magpie-GB PU"]) + (1 - wb["B1 Magpie-GB PU"]) * rn(tp),
         "B3b BLEND (Roost + TPOOL)": wb["B2 Roost-style PU"] * rn(L["B2 Roost-style PU"]) + (1 - wb["B2 Roost-style PU"]) * rn(tp),
         "BEST-LEARNED (inner-selected)": L[best_learned],
         "C1 ablation: TPOOL + charge-neutral first [domain knowledge]": rn(tp) + 2.0 * nm}
    S.update(L)
    # E4 novel-only test positives: ternary/quaternary whose template has no training positive with the same element subset
    trset = {(frozenset(json.loads(c)), tpl(cs.t[j])) for c, j in zip(pos.composition.values[tr], trc)}
    nov = np.array([a >= 3 and (frozenset(json.loads(c)), tpl(cs.t[j])) not in trset for a, c, j in zip(pos.nelements.values[te], pos.composition.values[te], tec)], bool)
    rows = []
    for m, v in S.items():
        for subset, tsel, rem in (("all", tec, remove), ("novel", tec[nov], np.r_[remove, tec[~nov]].astype(int))):
            r = metrics(v, rem, tsel); r.update(system=s, split=sid, method=m, subset=subset, w=wb.get({"BLEND (RF + TPOOL)": "PU-RF", "B3a BLEND (Magpie-GB + TPOOL)": "B1 Magpie-GB PU", "B3b BLEND (Roost + TPOOL)": "B2 Roost-style PU"}.get(m, ""), np.nan),
                     best_learned=best_learned if m.startswith("BEST") else "", inner_own=json.dumps(own) if m == "TPOOL" else "", n_dropped=len(drop)); rows.append(r)
        sc = v.astype(float).copy(); sc[remove] = -np.inf
    print("done-job", s, sid, best_learned, round(time.time() - T0), flush=True)
    return rows

def build_jobs():
    J = []
    for s in RUN:
        if MODE == "e2":
            cs, pos, _ = space(s); y = np.array([yr(k) for k in pos.key], float)
            tr = np.where(y <= 2010)[0]; te = np.where((y >= 2011) & (y <= 2025))[0]; drop = np.where(np.isnan(y) | (y > 2025))[0]
            J.append((s, ("T0", tr, te, drop)))
        else:
            J += [(s, (sid, tr, te, np.array([], int))) for sid, tr, te in splits(s, "A", NS)]
    return J

if __name__ == "__main__":
    T0 = time.time(); jobs = build_jobs(); print("jobs", len(jobs), flush=True)
    with Pool(8) as p: M = pd.DataFrame([r for x in p.imap_unordered(job, jobs, chunksize=1) for r in x])
    M.to_csv(os.path.join(D, "results", f"metrics_{MODE}.csv"), index=False)
    print(M[M.subset == "all"].groupby("method")[["recall@100", "recall@500"]].mean().round(3)); print("runtime_s", round(time.time() - T0))
