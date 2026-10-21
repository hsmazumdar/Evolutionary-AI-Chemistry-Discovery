"""V06 confirmatory analysis exactly as PREREG_V06 s3-s5 (written before outcomes were inspected)."""
import os, json, numpy as np, pandas as pd
from scipy.stats import wilcoxon
D = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(D, "results"); rng = np.random.default_rng(20261021)
def boot(d): d = np.asarray(d); return np.percentile([d[rng.integers(0, len(d), len(d))].mean() for _ in range(10000)], [2.5, 97.5])
def holm(p):
    o = np.argsort(p); m = len(p); adj = np.empty(m); run = 0
    for i, j in enumerate(o): run = max(run, (m - i) * p[j]); adj[j] = min(1, run)
    return adj
def test(diff, alt):
    d = np.asarray(diff); p = wilcoxon(d, zero_method="pratt", alternative=alt).pvalue; lo, hi = boot(d)
    return dict(n=len(d), mean_diff=float(d.mean()), ci_lo=float(lo), ci_hi=float(hi), wins=int((d > 0).sum()), losses=int((d < 0).sum()), zeros=int((d == 0).sum()), p=float(p))
def per_sys(M, subset, metric):
    return M[M.subset == subset].groupby(["system", "method"])[metric].mean().unstack()
E1 = pd.read_csv(f"{R}/metrics_e1.csv"); out = {}
A100, A500 = per_sys(E1, "all", "recall@100"), per_sys(E1, "all", "recall@500")
out["H6.1"] = test(A100["BLEND (RF + TPOOL)"] - A100["TPOOL"], "greater")
out["H6.2"] = test(A500["BLEND (RF + TPOOL)"] - A500["TPOOL"], "greater")
h3 = test(A100["BEST-LEARNED (inner-selected)"] - A100["TPOOL"], "less"); out["H6.3"] = h3
nv = E1[(E1.subset == "novel") & (E1.method == "TPOOL")].groupby("system").n_test.sum(); elig = nv[nv >= 3].index
N500 = per_sys(E1, "novel", "recall@500").loc[elig]
out["H6.4"] = test(N500["BLEND (RF + TPOOL)"] - N500["TPOOL"], "greater"); out["H6.4"]["eligible_systems"] = len(elig); out["H6.4"]["confirmatory"] = bool(len(elig) >= 30)
fam = ["H6.1", "H6.2", "H6.3", "H6.4"] if out["H6.4"]["confirmatory"] else ["H6.1", "H6.2", "H6.3"]
for h, a in zip(fam, holm(np.array([out[h]["p"] for h in fam]))): out[h]["holm_p"] = float(a)
for h in ["H6.1", "H6.2", "H6.4"]:
    o = out[h]; o["supported"] = bool(o.get("holm_p", 1) < 0.05 and o["mean_diff"] >= 0.02 and o["ci_lo"] > 0) if o.get("confirmatory", True) else None
o = out["H6.3"]; o["supported"] = bool(o["holm_p"] < 0.05 and o["mean_diff"] <= -0.02 and o["ci_hi"] < 0)
o["best_learned_counts"] = E1[(E1.method == "BEST-LEARNED (inner-selected)") & (E1.subset == "all")].best_learned.value_counts().to_dict()
if os.path.exists(f"{R}/metrics_e2.csv"):
    E2 = pd.read_csv(f"{R}/metrics_e2.csv"); nt = E2[(E2.subset == "all") & (E2.method == "TPOOL")].set_index("system").n_test; el2 = nt[nt >= 5].index
    T = per_sys(E2, "all", "recall@100").loc[el2]; h5 = test(T["BLEND (RF + TPOOL)"] - T["TPOOL"], "greater"); h5["eligible_systems"] = len(el2)
    h5["supported"] = bool(h5["p"] < 0.05 and h5["mean_diff"] >= 0.02 and h5["ci_lo"] > 0); out["H6.5"] = h5
    tab2 = pd.DataFrame({k: per_sys(E2, "all", k).loc[el2].mean() for k in ["recall@100", "recall@500", "recall@1000"]}).round(3); tab2.to_csv(f"{R}/e2_arms.csv")
json.dump(out, open(f"{R}/hypotheses.json", "w"), indent=1)
tab = pd.DataFrame({f"{s} R@{k}": per_sys(E1, s, f"recall@{k}").loc[elig if s == "novel" else slice(None)].mean() for s in ("all", "novel") for k in (10, 100, 500, 1000)}).round(3)
tab["stable R@100"] = per_sys(E1, "all", "stable_recall@100").mean().round(3); tab.sort_values("all R@100", ascending=False).to_csv(f"{R}/e1_arms.csv")
print(json.dumps(out, indent=1)); print(tab.sort_values("all R@100", ascending=False).to_string())
