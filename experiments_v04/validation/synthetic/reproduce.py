"""SYNTHETIC controlled contradiction experiments (not chemistry, not discoveries).
Ground truth: general rule y = 0.3 + 1.2*x0 - 0.8*x1*x2 ; exception domain D = {x3 > t} (soft edge = overlap)
inside D: y = 0.3 - 1.0*x0 + 0.6*z   where z is a (possibly missing) explanatory variable.
Factors varied one at a time around a default: exception frequency, noise, reliability informativeness,
number of missing variables, domain overlap, corrupted (non-reproducible) observations."""
import os, sys, json, time, argparse
from multiprocessing import Pool
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from shared.common import boot_ci, paired, provenance, write_yaml, mae
from shared.twopop import fit_two_population, predict_two_population, in_domain
from shared.common import GP
import copy
ap = argparse.ArgumentParser(); ap.add_argument("--quick", action="store_true"); A = ap.parse_args()
CFG = dict(pop=150, gens_G=40, gens_S=20, inner_val_frac=0.25, archive_k=10, contradiction_frac=0.15, min_contradictions=4,
           gate_depth=2, gate_min_leaf=2, accept_margin=0.005, n_train=200, n_test=2000, seeds=[0, 1, 2, 3, 4])
if A.quick: CFG.update(pop=40, gens_G=6, gens_S=4, n_test=200, seeds=[0])
DEF = dict(freq=0.15, noise=0.05, rel_informative=True, missing=1, overlap=0.0, corrupt=0.0)
GRID = [("freq", v) for v in [0.0, 0.05, 0.15, 0.30]] + [("noise", v) for v in [0.01, 0.1, 0.2]] + \
       [("rel_informative", False)] + [("missing", v) for v in [0, 2]] + [("overlap", v) for v in [0.05, 0.15]] + \
       [("corrupt", v) for v in [0.05, 0.15]] + [("corrupt_freq0", 0.15)]

def make(env, n, rng, train=True):
    Xf = rng.uniform(0, 1, (n, 6)); x0, x1, x2, x3, x4, x5 = Xf.T
    t = np.quantile(rng.uniform(0, 1, 100000), 1 - env["freq"]) if env["freq"] > 0 else 2.0
    pD = 1 / (1 + np.exp(-(x3 - t) / max(env["overlap"], 1e-6))) if env["overlap"] > 0 else (x3 > t).astype(float)
    D = rng.random(n) < pD
    z = {0: x4, 1: x4, 2: 0.5 * (x4 + x5)}[env["missing"]]
    y_true = np.where(D, 0.3 - 1.0 * x0 + 0.6 * z * 2, 0.3 + 1.2 * x0 - 0.8 * x1 * x2)
    obs = Xf[:, :5] if env["missing"] == 0 else Xf[:, :4]          # observed features
    ext = Xf[:, :5]                                                # candidate missing variable x4 offered to S
    rel = rng.uniform(0.2, 1.0, n); y = y_true + rng.normal(0, env["noise"], n)
    y = y + rng.normal(0, 1, n) * 0.3 * (1 - rel)                  # low-reliability observations are noisier
    corrupted = np.zeros(n, bool)
    if train and env["corrupt"] > 0:
        corrupted = rng.random(n) < env["corrupt"]; y[corrupted] += rng.choice([-1, 1], corrupted.sum()) * rng.uniform(0.8, 1.5, corrupted.sum())
        if env["rel_informative"]: rel[corrupted] = rng.uniform(0.2, 0.5, corrupted.sum())
    if not env["rel_informative"]: rel = rng.uniform(0.2, 1.0, n)  # reliability label carries no information
    return obs, ext, y, y_true, D, rel, corrupted

def job(arg):
    fac, val, seed = arg; env = dict(DEF)
    if fac == "corrupt_freq0": env.update(freq=0.0, corrupt=val)
    else: env[fac] = val
    rng = np.random.default_rng(seed)
    Xo, Xe, y, _, Dtr, rel, cor = make(env, CFG["n_train"], rng)
    Xt, Xte, _, yt, Dte, _, _ = make(env, CFG["n_test"], rng, train=False)
    X = np.vstack([Xo, Xt]); XE = np.vstack([Xe, Xte]); Y = np.concatenate([y, yt]); R = np.concatenate([rel, np.ones(len(yt))])
    tr = np.arange(len(y)); te = np.arange(len(y), len(Y)); names = [f"x{i}" for i in range(X.shape[1])]; ne = [f"x{i}" for i in range(5)]
    out = []
    g = GP(names, pop_size=CFG["pop"], generations=CFG["gens_G"] + CFG["gens_S"], seed=seed).fit(X[tr], Y[tr])
    p = g.predict(X[te]); out.append(dict(method="GP_extra_generations", test_MAE=mae(p, yt), MAE_in_D=mae(p[Dte], yt[Dte]), MAE_out_D=mae(p[~Dte], yt[~Dte]), accepted=0))
    Gfit = None
    for meth in ["high_residual", "proposed"]:
        m, info, Gfit = fit_two_population(X, XE, Y, R, tr, seed, CFG, names, ne, selection=meth, G_fit=Gfit)
        pg = m["G"].predict(X[te]); d = in_domain(m, X, te)
        ps = m["S"].predict(m["XX"][te]); p = np.where(d, ps if m["mode"] == "replace" else 0.5 * (pg + ps), pg)
        Cidx = np.array(info["contradiction_idx"], int)
        out.append(dict(method=meth, test_MAE=mae(p, yt), MAE_in_D=mae(p[Dte], yt[Dte]), MAE_out_D=mae(p[~Dte], yt[~Dte]), accepted=int(info["accepted"]),
                        domain_precision=float(Dte[d].mean()) if d.any() else np.nan, domain_recall=float(d[Dte].mean()) if Dte.any() else np.nan,
                        false_discovery=int(info["accepted"] and (not Dte.any() or (d.any() and Dte[d].mean() < 0.5))),
                        contradictions_true_exception=float(Dtr[Cidx].mean()), contradictions_corrupted=float(cor[Cidx].mean()),
                        used_missing_variable=int(info["accepted"] and info["S_features"] != "base" and "x4" in info["S_rule"]),
                        specialist_rule=info["S_rule"] if info["accepted"] else None))
    for o in out: o.update(factor=fac, value=str(val), seed=seed, true_exception_frac_train=float(Dtr.mean()), corrupt_frac=float(cor.mean()))
    return out

if __name__ == "__main__":
    T0 = time.time(); jobs = [(f, v, s) for f, v in GRID for s in CFG["seeds"]]
    with Pool(8) as pool: res = pool.map(job, jobs)
    M = pd.DataFrame([o for r in res for o in r]); M.to_csv(os.path.join(HERE, "metrics.csv"), index=False)
    write_yaml(os.path.join(HERE, "config.yaml"), dict(CFG, default_environment=DEF, grid=[list(map(str, g)) for g in GRID], label="SYNTHETIC", provenance=provenance()))
    agg = M.groupby(["factor", "value", "method"]).agg(test_MAE=("test_MAE", "mean"), MAE_in_D=("MAE_in_D", "mean"), MAE_out_D=("MAE_out_D", "mean"),
          accept_rate=("accepted", "mean"), domain_precision=("domain_precision", "mean"), domain_recall=("domain_recall", "mean"),
          false_discovery_rate=("false_discovery", "mean"), C_true_exc=("contradictions_true_exception", "mean"), C_corrupted=("contradictions_corrupted", "mean"),
          used_missing_var=("used_missing_variable", "mean")).round(3).reset_index()
    agg.to_csv(os.path.join(HERE, "summary.csv"), index=False)
    piv = M.pivot_table(index=["factor", "value", "seed"], columns="method", values="test_MAE")
    tests = {f"proposed - {c}": paired(piv["proposed"], piv[c]) for c in ["GP_extra_generations", "high_residual"]}
    json.dump(tests, open(os.path.join(HERE, "paired_tests.json"), "w"), indent=1)
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    os.makedirs(os.path.join(HERE, "figures"), exist_ok=True)
    fig, ax = plt.subplots(figsize=(11, 4)); lab = [f"{f}={v}" for f, v in GRID]
    for meth in ["GP_extra_generations", "high_residual", "proposed"]:
        ax.plot(lab, [M[(M.factor == f) & (M.value == str(v)) & (M.method == meth)].test_MAE.mean() for f, v in GRID], "o-", label=meth)
    ax.set_xticks(range(len(lab))); ax.set_xticklabels(lab, rotation=60, fontsize=7); ax.set_ylabel("test MAE vs noise-free truth"); ax.set_title("SYNTHETIC environments"); ax.legend()
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "figures", "synthetic_mae.png"), dpi=150)
    print(agg.to_string()); print(json.dumps(tests, indent=1)); print("runtime", time.time() - T0)
