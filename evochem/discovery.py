"""Discovery A: propose unseen Fe-Na-O-P formulas and rank them by how likely they are to exist.
score = predicted formation energy - training-only hull energy  (+ lam * distance outside the training domain)
lam is chosen by INNER cross-validation on the training split only; the hidden 40% is never consulted."""
from math import gcd
from functools import reduce
import numpy as np
from .features import featurize
from .hull import TrainingHull, comp_vec

LAMS = [0.0, 0.05, 0.1, 0.2, 0.5, 1.0]

class CandidateSpace:
    def __init__(self, elements, el, maxtot=30):
        self.EL = elements
        self.t = [t for a in range(maxtot + 1) for b in range(maxtot + 1 - a) for c in range(maxtot + 1 - a - b)
                  for d in range(maxtot + 1 - a - b - c) for t in [(a, b, c, d)] if sum(x > 0 for x in t) >= 2 and reduce(gcd, t) == 1]
        comps = [{e: float(n) for e, n in zip(elements, t) if n} for t in self.t]
        self.ix = {t: i for i, t in enumerate(self.t)}
        self.X, _ = featurize(comps, el); self.Xo, _ = featurize(comps, el, use_oxidation=True)
        self.F = np.array([comp_vec(c, elements) for c in comps])
    def key(self, comp): return tuple(int(round(comp.get(e, 0))) for e in self.EL)
    def name(self, j): return "".join(f"{e}{n if n > 1 else ''}" for e, n in zip(self.EL, self.t[j]) if n)

def domain_distance(Xtr, Xc):
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9; A, B = (Xtr - mu) / sd, (Xc - mu) / sd
    d2 = (B ** 2).sum(1)[:, None] - 2 * B @ A.T + (A ** 2).sum(1)[None, :]
    return np.sqrt(np.maximum(d2.min(1), 0))

def hits(score, cs, comps, seen_idx, hidden_idx, ks):
    mask = np.ones(len(cs.t), bool)
    for i in seen_idx:
        k = cs.key(comps[i])
        if k in cs.ix: mask[cs.ix[k]] = False
    pos = [cs.ix[cs.key(comps[i])] for i in hidden_idx if len(comps[i]) >= 2 and cs.key(comps[i]) in cs.ix]
    order = np.argsort(np.where(mask, score, np.inf)); rank = np.empty(len(score), int); rank[order] = np.arange(len(score))
    N = int(mask.sum())
    r = {"N_ranked": N, "n_hidden_multi": sum(len(comps[i]) >= 2 for i in hidden_idx), "n_hidden_in_space": len(pos),
         "median_rank": float(np.median(rank[pos])) if pos else None, "order": order}
    for k in ks: r[f"hits@{k}"] = int((rank[pos] < k).sum()); r[f"random@{k}"] = len(pos) * k / N
    return r

def base_score(model_pred_c, cs, comps, y, train_idx, Xtr, Xc_feat):
    hull = TrainingHull([comps[i] for i in train_idx], y[train_idx], cs.EL)
    return model_pred_c - hull.hull_energy(cs.F), domain_distance(Xtr, Xc_feat)

def choose_lambda(fit_predict, cs, comps, y, X, Xc_feat, train_idx, seed=0, n_rep=3, k=100):
    """fit_predict(inner_train_idx) -> predictions on candidates. Returns the lam maximising inner recall@k."""
    rng = np.random.default_rng(seed); tot = np.zeros(len(LAMS))
    for _ in range(n_rep):
        p = rng.permutation(train_idx); cut = int(0.7 * len(p)); itr, ite = p[:cut], p[cut:]
        e, dd = base_score(fit_predict(itr), cs, comps, y, itr, X[itr], Xc_feat)
        for j, lam in enumerate(LAMS):
            tot[j] += hits(e + lam * dd, cs, comps, itr, ite, [k])[f"hits@{k}"]
    return LAMS[int(np.argmax(tot))], dict(zip(map(str, LAMS), tot.tolist()))

def analogy_mask(cs, comps, train_idx):
    """Analogical hypothesis generator: re-use the stoichiometry templates (sorted subscript multisets, e.g. (1,1,4)
    from FePO4) seen in TRAINING compounds and assign the system's elements to them in every way."""
    import itertools
    tmpl = {tuple(sorted(int(round(x)) for x in comps[i].values())) for i in train_idx}
    m = np.zeros(len(cs.t), bool)
    for v in tmpl:
        for els in itertools.permutations(cs.EL, len(v)):
            t = tuple(dict(zip(els, v)).get(e, 0) for e in cs.EL)
            if t in cs.ix: m[cs.ix[t]] = True
    return m
