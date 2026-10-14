"""Phase 8: DFT formation-energy regression benchmark, Protocol C (leave-one-system-out) over the 9 V05 systems.
Target = DFT formation energy of the lowest-energy OBSERVED polymorph (computed, not measured).
Training formulas identical (reduced composition) to any target formula are removed from the training set.
sklearn models + V03 GP run here; PySR and Roost run in /workspace/venv_v05x via subprocess (CPU)."""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"): os.environ.setdefault(_v, "1")
import sys, json, time, subprocess, tempfile, argparse
from multiprocessing import Pool
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, HERE)
from shared.core import *
from sklearn.linear_model import RidgeCV
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
ap = argparse.ArgumentParser(); ap.add_argument("--quick", action="store_true"); ap.add_argument("--xpy", default="/workspace/venv_v05x/bin/python"); A = ap.parse_args()
OUT = os.path.join(HERE, "results", "phase8"); os.makedirs(OUT, exist_ok=True)
F = formulas(); F = F[F.experimentally_observed & (F.nelements >= 2)].copy()
F["comp"] = F.composition.apply(json.loads); F["X"] = list(featurize(list(F.comp), EL)[0])  # all elements have complete attributes (QC)
NAMES = prim_names(); EPOCHS = 5 if A.quick else 150

def job(t):
    te = F[F.system == t].drop_duplicates("key"); tr = F[(F.system != t) & ~F.key.isin(te.key)].drop_duplicates("key")
    Xtr, ytr, Xte, yte = np.vstack(tr.X), tr.dft_Ef_observed_min_eV_atom.values, np.vstack(te.X), te.dft_Ef_observed_min_eV_atom.values
    rows = []; rec = lambda m, p, t0, seed=0, extra=None: rows.append(dict(target_system=t, model=m, seed=seed, n_train=len(ytr), n_test=len(yte), MAE=float(np.mean(np.abs(p - yte))), runtime_s=time.time() - t0, **(extra or {})))
    t0 = time.time(); rec("mean", np.full(len(yte), ytr.mean()), t0)
    t0 = time.time(); rec("ridge", make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-3, 3, 13))).fit(Xtr, ytr).predict(Xte), t0)
    for s in [0, 1, 2]:
        t0 = time.time(); rec("random_forest", RandomForestRegressor(300, min_samples_leaf=2, random_state=s, n_jobs=1).fit(Xtr, ytr).predict(Xte), t0, s)
        t0 = time.time(); rec("gradient_boosting", GradientBoostingRegressor(n_estimators=300, max_depth=3, learning_rate=0.05, random_state=s).fit(Xtr, ytr).predict(Xte), t0, s)
        t0 = time.time(); g = GP(NAMES, pop_size=300, generations=40 if not A.quick else 3, seed=s).fit(Xtr, ytr); rec("V03_GP", g.predict(Xte), t0, s, dict(rule=g.to_str()))
    d = tempfile.mkdtemp()
    np.savez(f"{d}/tr.npz", X=Xtr, y=ytr, names=np.array(NAMES)); np.savez(f"{d}/te.npz", X=Xte, y=yte, names=np.array(NAMES))
    for s in ([0] if A.quick else [0, 1]):
        t0 = time.time(); r = subprocess.run([A.xpy, os.path.join(HERE, "phase8", "pysr_runner.py"), f"{d}/tr.npz", f"{d}/te.npz", f"{d}/py{s}.csv", str(s)], capture_output=True, text=True)
        if r.returncode == 0: rec("PySR", pd.read_csv(f"{d}/py{s}.csv").y_pred.values, t0, s, dict(rule=[l for l in r.stdout.splitlines() if l.startswith("EQ")][-1]))
        else: rows.append(dict(target_system=t, model="PySR", seed=s, error=r.stderr[-500:]))
    pd.DataFrame(dict(id=tr.key, composition=tr.formula, y=ytr)).to_csv(f"{d}/rtr.csv", index=False); pd.DataFrame(dict(id=te.key, composition=te.formula, y=yte)).to_csv(f"{d}/rte.csv", index=False)
    t0 = time.time(); r = subprocess.run([A.xpy, os.path.join(HERE, "phase8", "roost_runner.py"), f"{d}/rtr.csv", f"{d}/rte.csv", f"{d}/ro.csv", str(EPOCHS)], capture_output=True, text=True)
    if r.returncode == 0: rec("Roost (matscholar embedding)", pd.read_csv(f"{d}/ro.csv").y_pred.values, t0)
    else: rows.append(dict(target_system=t, model="Roost", error=r.stderr[-500:]))
    return rows

if __name__ == "__main__":
    T0 = time.time(); systems = SYSTEMS[:1] if A.quick else SYSTEMS
    with Pool(min(8, len(systems))) as pool: res = pool.map(job, systems, chunksize=1)
    M = pd.DataFrame([r for x in res for r in x]); M.to_csv(os.path.join(OUT, "regression_metrics.csv"), index=False)
    print(M.groupby("model").MAE.mean().round(3).sort_values()); print("runtime", time.time() - T0)
