"""V05 core: multi-system data access, candidate spaces, splits, PU rankers, EHP (evolutionary hypothesis population),
ranking metrics. V03 modules (evochem) are imported read-only."""
import os, sys, json, hashlib
from functools import lru_cache
import numpy as np, pandas as pd
V05 = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); ROOT = os.path.dirname(V05); sys.path.insert(0, ROOT)
from evochem.features import load_elements, featurize   # noqa
from evochem.discovery import CandidateSpace              # noqa
from evochem.gp import GP                                 # noqa
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
DATA = os.path.join(V05, "data")
SYSTEMS = ["Fe-Na-O-P", "Ba-O-P-V", "K-O-S-V", "H-N-O-S", "Al-Ca-O-Si", "K-Mo-O-P", "B-H-Na-O", "Ba-Fe-O-S", "Mn-O-P-Ti"]
EL = load_elements(os.path.join(ROOT, "data", "elements_118.csv"))
KS = [10, 50, 100, 500, 1000]

@lru_cache(None)
def formulas():
    return pd.read_csv(os.path.join(DATA, "formulas_v05.csv"))

@lru_cache(None)
def space(system):
    els = sorted(system.split("-")); cs = CandidateSpace(els, EL, 30)
    F = formulas(); g = F[(F.system == system) & F.experimentally_observed & (F.nelements >= 2)].reset_index(drop=True)
    idx, keep = [], []
    for i, c in enumerate(g.composition):
        d = json.loads(c); m = min(d.values()); t = None
        for mult in range(1, 31):                       # recover the integer reduced formula
            v = {e: d[e] / m * mult for e in d}
            if all(abs(x - round(x)) < 1e-3 for x in v.values()):
                t = tuple(int(round(v.get(e, 0))) for e in els); break
        if t is not None and t in cs.ix: idx.append(cs.ix[t]); keep.append(i)
    pos = g.iloc[keep].reset_index(drop=True); pos["cand_idx"] = idx
    return cs, pos, len(g) - len(keep)

def splits(system, protocol, n=5):
    cs, pos, _ = space(system); P = len(pos); out = []
    if protocol == "A":
        for s in range(n):
            p = np.random.default_rng(s).permutation(P); cut = int(round(0.6 * P)); out.append((f"A{s}", np.sort(p[:cut]), np.sort(p[cut:])))
    elif protocol == "B":
        fam = pos.formula_anonymous.values; u = np.array(sorted(set(fam))); np.random.default_rng(0).shuffle(u)
        for f in range(n):
            held = set(u[f::n]); te = np.array([i for i in range(P) if fam[i] in held], int); tr = np.array([i for i in range(P) if fam[i] not in held], int)
            out.append((f"B{f}", tr, te))
    return out

def rank_metrics(score, train_c, test_c):
    """score: higher = more likely. train candidates are removed from the ranking (already known)."""
    s = score.astype(float).copy(); s[train_c] = -np.inf
    N = len(s) - len(train_c); order = np.argsort(-s, kind="stable"); rank = np.empty(len(s), int); rank[order] = np.arange(len(s))
    r = rank[test_c] + 1; m = dict(N_ranked=N, n_test=len(test_c), median_rank=float(np.median(r)), MRR=float(np.mean(1.0 / r)))
    for k in KS: m[f"recall@{k}"] = float(np.mean(r <= k)); m[f"random_recall@{k}"] = k / N
    m["precision@100_observed"] = float(np.sum(r <= 100) / 100); m["enrichment@100"] = m["recall@100"] / (100 / N)
    return m

# ---------------- PU rankers ----------------
def _bags(pos_c, n_cand, ratio, bags, rng):
    U = np.setdiff1d(np.arange(n_cand), pos_c)
    for b in range(bags): yield b, rng.choice(U, min(len(U), ratio * len(pos_c)), replace=False)

def pu_generic(make_clf, Xc, pos_c, seed, bags=15, ratio=5, extra_pos=None):
    """PU bagging. extra_pos: optional (X_extra_pos, X_extra_unl) pooled from other systems (transfer)."""
    rng = np.random.default_rng(seed); s = np.zeros(len(Xc)); n = np.zeros(len(Xc))
    for b, ub in _bags(pos_c, len(Xc), ratio, bags, rng):
        Xb = np.vstack([Xc[pos_c], Xc[ub]]); yb = np.r_[np.ones(len(pos_c)), np.zeros(len(ub))]
        if extra_pos is not None:
            XP, XU = extra_pos; j = rng.choice(len(XU), min(len(XU), ratio * len(XP)), replace=False)
            Xb = np.vstack([Xb, XP, XU[j]]); yb = np.r_[yb, np.ones(len(XP)), np.zeros(len(j))]
        clf = make_clf(seed * 100 + b).fit(Xb, yb)
        oob = np.ones(len(Xc), bool); oob[ub] = False
        s[oob] += clf.predict_proba(Xc[oob])[:, 1]; n[oob] += 1
    return s / np.maximum(n, 1)

RF = lambda leaf: (lambda rs: RandomForestClassifier(100, min_samples_leaf=leaf, n_jobs=1, random_state=rs))
GB = lambda rs: HistGradientBoostingClassifier(max_iter=150, learning_rate=0.1, random_state=rs)
class _Logit:
    def __init__(self, rs): self.sc = StandardScaler(); self.m = LogisticRegression(C=1.0, max_iter=2000)
    def fit(self, X, y): self.m.fit(self.sc.fit_transform(X), y); return self
    def predict_proba(self, X): return self.m.predict_proba(self.sc.transform(X))
LOGIT = lambda rs: _Logit(rs)

def nearest_positive(Xc, pos_c):
    mu, sd = Xc[pos_c].mean(0), Xc.std(0) + 1e-9; A = (Xc[pos_c] - mu) / sd; B = (Xc - mu) / sd
    d2 = (B ** 2).sum(1)[:, None] - 2 * B @ A.T + (A ** 2).sum(1)[None, :]
    return -np.sqrt(np.maximum(d2, 0)).min(1)

def template_prior(cs, pos_c, extra_templates=None):
    from collections import Counter
    C = Counter(tuple(sorted(x for x in cs.t[j] if x)) for j in pos_c)
    if extra_templates: C.update(extra_templates)
    tot = np.array([sum(t) for t in cs.t])
    return np.array([C.get(tuple(sorted(x for x in t if x)), 0) for t in cs.t], float) - 1e-3 * tot

# ---------------- EHP: evolutionary hypothesis population (primitive features only) ----------------
class EHP:
    """Each hypothesis = GP expression tree h(x) over primitive features, fitted as a least-squares PU discriminant
    (target 1 for positives, 0 for an unlabelled bag, class-balanced weights) via the V03 GP engine (linear scaling).
    Confidence of a hypothesis = rank-AUC on inner-validation positives vs fresh unlabelled. Score = confidence-weighted
    mean of rank-normalised hypothesis outputs over the archive."""
    def __init__(self, names, pop=200, gens=30, bags=5, ratio=3, archive_k=3, seed=0):
        self.names, self.pop, self.gens, self.bags, self.ratio, self.k, self.seed = names, pop, gens, bags, ratio, archive_k, seed
        self.hyp = []; self.gps = []

    @staticmethod
    def auc(sp, su):
        a = np.r_[sp, su]; r = a.argsort().argsort(); rp = r[: len(sp)]
        return float((rp.sum() - len(sp) * (len(sp) - 1) / 2) / (len(sp) * len(su)))

    def _bag_data(self, Xc, pos_c, rng, extra=None):
        U = np.setdiff1d(np.arange(len(Xc)), pos_c); u = rng.choice(U, self.ratio * len(pos_c), replace=False)
        X = np.vstack([Xc[pos_c], Xc[u]]); y = np.r_[np.ones(len(pos_c)), np.zeros(len(u))]
        if extra is not None:
            XP, XU = extra; j = rng.choice(len(XU), min(len(XU), self.ratio * len(XP)), replace=False)
            X = np.vstack([X, XP, XU[j]]); y = np.r_[y, np.ones(len(XP)), np.zeros(len(j))]
        w = np.where(y == 1, (y == 0).sum() / max(1, (y == 1).sum()), 1.0)
        return X, y, w

    def fit(self, Xc, pos_c, extra=None, gp_list=None, gens=None):
        rng = np.random.default_rng(self.seed); p = rng.permutation(pos_c); nv = max(2, len(p) // 4); val, fit = p[:nv], p[nv:]
        new = []
        for b in range(self.bags):
            X, y, w = self._bag_data(Xc, fit, rng, extra)
            g = gp_list[b] if gp_list is not None and b < len(gp_list) else GP(self.names, pop_size=self.pop, seed=self.seed * 100 + b)
            g.fit(X, y, w=w, generations=gens or self.gens)
            if gp_list is not None and b >= len(gp_list): gp_list.append(g)
            res = sorted(((g._fitness(t, X, y, w), t) for t in g.pop), key=lambda r: r[0][0]); seen = set(); c = 0
            for (fit_, m, sc), t in res:
                s = g.to_str(t, sc)
                if s in seen: continue
                seen.add(s); new.append(dict(gp=g, tree=t, scale=sc, str=s, nodes=len(t))); c += 1
                if c >= self.k: break
        self.val, self.Xc = val, Xc
        return new

    def score(self, Xc, hyps, val_c, rng_seed=0):
        rng = np.random.default_rng(rng_seed); U = np.setdiff1d(np.arange(len(Xc)), val_c); u = rng.choice(U, min(len(U), 2000), replace=False)
        S = np.zeros(len(Xc)); W = 0
        for h in hyps:
            v = h["gp"].predict(Xc, h["tree"], h["scale"]); v = np.nan_to_num(v)
            h["conf"] = max(0.0, self.auc(v[val_c], v[u]) - 0.5)
            if h["conf"] <= 0: continue
            S += h["conf"] * (v.argsort().argsort() / len(v)); W += h["conf"]
        return S / W if W > 0 else S

def prim_names():
    from evochem.features import ATTRS
    return [f"{p}_{a[0]}" for a in ATTRS.values() for p in ("mean", "dev", "range")] + ["n_elem"]
