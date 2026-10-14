"""Contradiction-driven two-population learner (Population G = general rule, Population S = specialist rule
with a learned applicability domain) plus the Stage-1 control and ablation conditions.

Leakage rule: everything here sees ONLY the training indices. The test set enters only through
`predict_*` calls made by the caller after all decisions are frozen.

Compute budget (in GP generations of a population of size POP, all on <= n_train samples):
  ordinary      : G 40                                     (reference, smaller budget)
  extra_gens    : G 40 + 20                                (matched)
  v03_weighted  : G 40 + 20 with V03 contradiction weights (matched)
  specialist_*  : G 40 on the inner-fit part + S 10 (base features) + S 10 (base+missing variables) (matched)
"""
import copy
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from .common import GP

def archive(gp, X, y, k=10):
    """Distinct best rules of the final population (each with its own linear scaling)."""
    w = np.ones(len(y)); seen, out = set(), []
    scored = sorted(((gp._fitness(t, X, y, w), t) for t in gp.pop), key=lambda r: r[0][0])
    for (fit, m, sc), t in scored:
        s = gp.to_str(t, sc)
        if s in seen: continue
        seen.add(s); out.append((t, sc, m))
        if len(out) >= k: break
    return out

def archive_sigma(gp, arch, X):
    P = np.array([gp.predict(X, t, sc) for t, sc, _ in arch])
    return P.std(0)

def calibrate(resid_val, sig_val):
    """sigma_cal = sqrt(s0^2 + (c*sigma_archive)^2); (s0,c) maximise Gaussian log-likelihood on INNER validation."""
    best = (-np.inf, 0.1, 1.0)
    for s0 in np.geomspace(0.02, 1.0, 25):
        for c in [0.0, 0.25, 0.5, 1, 2, 4, 8]:
            s = np.sqrt(s0 ** 2 + (c * sig_val) ** 2)
            ll = float(np.sum(-np.log(s) - 0.5 * (resid_val / s) ** 2))
            if ll > best[0]: best = (ll, s0, c)
    return best[1], best[2]

def rescale(gp, tree, X, y):
    return gp._scale(gp._eval(tree, X), y, np.ones(len(y)))

class Specialist:
    """One accepted (or rejected) specialist: rule + domain gate + combination mode."""
    def __init__(self): self.accepted = False

def fit_two_population(X, Xext, y, rel, train, seed, cfg, names, names_ext, selection="proposed",
                       use_validation=True, missing_var_search=True, G_fit=None):
    """selection in {proposed, no_uncertainty, no_reliability, high_residual, random}."""
    from .common import inner_split
    pop, gG, gS = cfg["pop"], cfg["gens_G"], cfg["gens_S"]
    fit, val = inner_split(train, seed, cfg["inner_val_frac"])
    rng = np.random.default_rng(777 + seed)
    if G_fit is None:
        G_fit = GP(names, pop_size=pop, generations=gG, seed=seed).fit(X[fit], y[fit])
    G = copy.deepcopy(G_fit)
    arch = archive(G, X[fit], y[fit], cfg["archive_k"])
    r_fit = y[fit] - G.predict(X[fit]); r_val = y[val] - G.predict(X[val])
    s0, c = calibrate(r_val, archive_sigma(G, arch, X[val]))
    sig_fit = np.sqrt(s0 ** 2 + (c * archive_sigma(G, arch, X[fit])) ** 2)
    surprise = np.abs(r_fit) / sig_fit
    pr = {"proposed": surprise * rel[fit], "no_uncertainty": np.abs(r_fit) * rel[fit],
          "no_reliability": surprise, "high_residual": np.abs(r_fit), "random": rng.random(len(fit))}[selection]
    n_c = max(cfg["min_contradictions"], int(np.ceil(cfg["contradiction_frac"] * len(fit))))
    C = np.zeros(len(fit), bool); C[np.argsort(-pr)[:n_c]] = True
    info = dict(selection=selection, n_fit=len(fit), n_val=len(val), calib_s0=float(s0), calib_c=float(c),
                n_contradictions=int(C.sum()), contradiction_idx=[int(i) for i in fit[C]])
    gate = DecisionTreeClassifier(max_depth=cfg["gate_depth"], min_samples_leaf=cfg["gate_min_leaf"],
                                  class_weight="balanced", random_state=seed).fit(X[fit], C)
    D_fit = gate.predict(X[fit]).astype(bool)
    if D_fit.sum() < 3: D_fit = C.copy()
    cands = []
    feats = [("base", X, names, gS if not missing_var_search else gS // 2)]
    if missing_var_search: feats.append(("base+charge_balance", Xext, names_ext, gS // 2))
    for fname, XX, nn, gens in feats:
        S = GP(nn, pop_size=pop, generations=gens, seed=seed + 1000).fit(XX[fit][D_fit], y[fit][D_fit])
        for mode in ["replace", "blend"]:
            pg = G.predict(X[val]); ps = S.predict(XX[val]); dv = gate.predict(X[val]).astype(bool)
            comb = np.where(dv, ps if mode == "replace" else 0.5 * (pg + ps), pg)
            cands.append(dict(features=fname, mode=mode, S=S, XX=XX, val_mae=float(np.mean(np.abs(y[val] - comb))),
                              n_val_in_domain=int(dv.sum())))
    g_val = float(np.mean(np.abs(r_val)))
    best = min(cands, key=lambda d: d["val_mae"])
    accept = (best["val_mae"] < g_val - cfg["accept_margin"] and best["n_val_in_domain"] >= 1) if use_validation else True
    # final: re-scale linear coefficients of the chosen trees on the WHOLE training partition (no new search)
    G.best_scale = rescale(G, G.best, X[train], y[train])
    D_tr = gate.predict(X[train]).astype(bool)
    S = best["S"]
    if D_tr.sum() >= 3: S.best_scale = rescale(S, S.best, best["XX"][train][D_tr], y[train][D_tr])
    info.update(G_rule=G.to_str(), G_nodes=len(G.best), val_mae_G=g_val, val_mae_best_combo=best["val_mae"],
                accepted=bool(accept), S_rule=S.to_str().replace("Ef =", "Ef_S ="), S_nodes=len(S.best),
                S_features=best["features"], mode=best["mode"], n_val_in_domain=best["n_val_in_domain"],
                gate_rules=_tree_text(gate, names), n_train_in_domain=int(D_tr.sum()),
                train_C_abs_err_G=float(np.mean(np.abs(r_fit[C]))))
    model = dict(G=G, S=S, XX=best["XX"], gate=gate, mode=best["mode"], accepted=accept)
    pC = predict_two_population(model, X, fit[C]) if C.any() else []
    info["train_C_abs_err_after"] = float(np.mean(np.abs(y[fit[C]] - pC))) if C.any() else None
    return model, info, G_fit

def predict_two_population(model, X, idx):
    pg = model["G"].predict(X[idx])
    if not model["accepted"]: return pg
    ps = model["S"].predict(model["XX"][idx]); d = model["gate"].predict(X[idx]).astype(bool)
    return np.where(d, ps if model["mode"] == "replace" else 0.5 * (pg + ps), pg)

def in_domain(model, X, idx):
    return model["gate"].predict(X[idx]).astype(bool) & bool(model["accepted"])

def _tree_text(tree, names):
    from sklearn.tree import export_text
    return export_text(tree, feature_names=list(names))

def fit_controls(X, y, df_ncsd, train, seed, cfg, names):
    """Controls 1-3 trained on the whole training partition."""
    pop, gG, gE = cfg["pop"], cfg["gens_G"], cfg["gens_S"]
    g40 = GP(names, pop_size=pop, generations=gG, seed=seed).fit(X[train], y[train])
    ext = copy.deepcopy(g40).fit(X[train], y[train], generations=gE)
    resid = y[train] - g40.predict(X[train]); thr = 2.5 * np.mean(np.abs(resid))
    flag = (np.abs(resid) > thr) & (df_ncsd[train] >= 2)          # exact V03 rule
    wgt = copy.deepcopy(g40).fit(X[train], y[train], w=np.where(flag, 3.0, 1.0), generations=gE)
    return {"ordinary_GP": g40, "GP_extra_generations": ext, "V03_contradiction_weighted": wgt}, int(flag.sum())
