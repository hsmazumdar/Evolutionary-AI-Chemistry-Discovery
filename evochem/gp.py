"""A small, readable genetic-programming symbolic regressor written in plain numpy.
Trees are prefix lists. Fitness = (weighted) MAE after linear scaling y ~ a + b*f(x), plus a parsimony penalty."""
import numpy as np

FUNCS = {  # name: (arity, function, infix format)
    "add": (2, lambda a, b: a + b, "({} + {})"),
    "sub": (2, lambda a, b: a - b, "({} - {})"),
    "mul": (2, lambda a, b: a * b, "({} * {})"),
    "div": (2, lambda a, b: np.where(np.abs(b) > 1e-3, a / np.where(np.abs(b) > 1e-3, b, 1.0), 1.0), "({} / {})"),
    "sqrt": (1, lambda a: np.sqrt(np.abs(a)), "sqrt|{}|"),
    "sq": (1, lambda a: a * a, "({})^2"),
    "neg": (1, lambda a: -a, "-({})"),
}
FNAMES = list(FUNCS)

class GP:
    def __init__(self, feature_names, pop_size=300, generations=40, max_depth=5, tournament=5,
                 p_cross=0.7, p_mut=0.25, parsimony=0.003, seed=0):
        self.names = feature_names; self.nf = len(feature_names)
        self.pop_size, self.generations, self.max_depth = pop_size, generations, max_depth
        self.tournament, self.p_cross, self.p_mut, self.parsimony = tournament, p_cross, p_mut, parsimony
        self.rng = np.random.default_rng(seed)
        self.pop = None; self.history = []

    # ---------- tree construction ----------
    def _terminal(self):
        if self.rng.random() < 0.8:
            return ("x", int(self.rng.integers(self.nf)))
        return ("c", float(np.round(self.rng.uniform(-3, 3), 2)))

    def _grow(self, depth, full=False):
        if depth == 0 or (not full and self.rng.random() < 0.35):
            return [self._terminal()]
        f = FNAMES[self.rng.integers(len(FNAMES))]
        out = [("f", f)]
        for _ in range(FUNCS[f][0]):
            out += self._grow(depth - 1, full)
        return out

    @staticmethod
    def _subtree_end(t, i):
        need = 1
        while need:
            node = t[i]; need += (FUNCS[node[1]][0] if node[0] == "f" else 0) - 1; i += 1
        return i

    def _depth(self, t):
        def rec(i):
            node = t[i]
            if node[0] != "f": return 1, i + 1
            d, j = 0, i + 1
            for _ in range(FUNCS[node[1]][0]):
                dd, j = rec(j); d = max(d, dd)
            return d + 1, j
        return rec(0)[0]

    # ---------- evaluation ----------
    def _eval(self, t, X):
        def rec(i):
            node = t[i]
            if node[0] == "x": return X[:, node[1]], i + 1
            if node[0] == "c": return np.full(X.shape[0], node[1]), i + 1
            ar, fn, _ = FUNCS[node[1]]; args, j = [], i + 1
            for _ in range(ar):
                a, j = rec(j); args.append(a)
            return fn(*args), j
        with np.errstate(all="ignore"):
            v = rec(0)[0]
        return np.nan_to_num(np.clip(v, -1e6, 1e6))

    def _scale(self, f, y, w):
        W = w.sum(); fm = (w * f).sum() / W; ym = (w * y).sum() / W
        var = (w * (f - fm) ** 2).sum()
        b = 0.0 if var < 1e-12 else (w * (f - fm) * (y - ym)).sum() / var
        return ym - b * fm, b

    def _fitness(self, t, X, y, w):
        f = self._eval(t, X); a, b = self._scale(f, y, w)
        mae = float((w * np.abs(y - (a + b * f))).sum() / w.sum())
        return mae + self.parsimony * len(t), mae, (a, b)

    # ---------- variation ----------
    def _crossover(self, p1, p2):
        i = self.rng.integers(len(p1)); j = self.rng.integers(len(p2))
        c = p1[:i] + p2[j:self._subtree_end(p2, j)] + p1[self._subtree_end(p1, i):]
        return c if self._depth(c) <= self.max_depth + 1 else p1

    def _mutate(self, p):
        i = self.rng.integers(len(p))
        if p[i][0] == "c" and self.rng.random() < 0.5:   # constant tweak
            c = list(p); c[i] = ("c", float(np.round(p[i][1] + self.rng.normal(0, 0.5), 2))); return c
        c = p[:i] + self._grow(2) + p[self._subtree_end(p, i):]
        return c if self._depth(c) <= self.max_depth + 1 else p

    def _select(self, fits):
        idx = self.rng.integers(len(fits), size=self.tournament)
        return idx[np.argmin(fits[idx])]

    # ---------- main loop ----------
    def fit(self, X, y, w=None, generations=None, callback=None):
        w = np.ones(len(y)) if w is None else np.asarray(w, float)
        if self.pop is None:  # ramped half-and-half
            self.pop = [self._grow(int(d), full=bool(k % 2))
                        for k, d in enumerate(np.linspace(2, self.max_depth, self.pop_size).astype(int))]
        for g in range(generations or self.generations):
            res = [self._fitness(t, X, y, w) for t in self.pop]
            fits = np.array([r[0] for r in res]); best = int(np.argmin(fits))
            self.best, self.best_scale = self.pop[best], res[best][2]
            self.history.append({"fitness": float(fits[best]), "train_mae": res[best][1], "size": len(self.best)})
            if callback: callback(self, len(self.history) - 1)
            new = [self.best]  # elitism
            while len(new) < self.pop_size:
                r = self.rng.random(); p1 = self.pop[self._select(fits)]
                if r < self.p_cross: c = self._crossover(p1, self.pop[self._select(fits)])
                elif r < self.p_cross + self.p_mut: c = self._mutate(p1)
                else: c = p1
                new.append(c)
            self.pop = new
        res = [self._fitness(t, X, y, w) for t in self.pop]
        best = int(np.argmin([r[0] for r in res])); self.best, self.best_scale = self.pop[best], res[best][2]
        return self

    def predict(self, X, tree=None, scale=None):
        tree = tree or self.best; a, b = scale or self.best_scale
        return a + b * self._eval(tree, X)

    def to_str(self, tree=None, scale=None):
        tree = tree or self.best; a, b = scale or self.best_scale
        def rec(i):
            node = tree[i]
            if node[0] == "x": return self.names[node[1]], i + 1
            if node[0] == "c": return f"{node[1]:g}", i + 1
            ar, _, fmt = FUNCS[node[1]]; args, j = [], i + 1
            for _ in range(ar):
                s, j = rec(j); args.append(s)
            return fmt.format(*args), j
        return f"Ef = {a:.3f} + {b:.3f} * {rec(0)[0]}"
