"""M2 (exploratory, data already seen): recall by formula arity (binary/ternary/quaternary) for every arm, decisive (9)
and replication (20) studies. Uses the per-test-formula ranks re-generated in revision_m1_ties (identical to the frozen
runs) and the tie-fair 'expected' recall from M1 (plus stable recall for reference). Within each system, recall for an
arity stratum = hits / test formulas of that arity pooled over the 5 splits; systems with no test formula of that arity
are excluded from that stratum's mean. Paired BLEND-vs-TPOOL tests use systems with >=1 formula in the stratum."""
import os, json, numpy as np, pandas as pd
from scipy.stats import wilcoxon
H = os.path.dirname(os.path.abspath(__file__)); M1 = os.path.join(os.path.dirname(H), "revision_m1_ties", "results"); RES = os.path.join(H, "results"); os.makedirs(RES, exist_ok=True)
B, T = "BLEND (RF + pooled template)", "TPOOL (pooled template)"; AR = {2: "binary", 3: "ternary", 4: "quaternary"}
def load(s):
    R = pd.read_csv(os.path.join(M1, f"per_test_{s}.csv.gz")); R["study"] = s
    for k in [100, 500]:
        R[f"exp@{k}"] = np.clip((k - R.n_greater) / R.n_tied, 0, 1); R[f"st@{k}"] = (R.stable_rank <= k).astype(float)
    R["rr_exp"] = 1.0 / (R.n_greater + (R.n_tied + 1) / 2); return R
A = pd.concat([load("decisive"), load("replication")]); A["arity_name"] = A.arity.map(AR)
md = ["# M2 results: recall by formula arity (exploratory; data already seen)\n", "Tie-fair expected recall (M1) unless marked 'stable'. Positives are test formulas of each split (40% of observed multi-element formulas).\n"]
out = {}
for study, R in [("decisive", A[A.study == "decisive"]), ("replication", A[A.study == "replication"]), ("pooled29", A)]:
    one = R[R.method == T]; cnt = one.groupby(["system", "arity_name"]).key.nunique().unstack(fill_value=0)
    md.append(f"\n## {study} ({R.system.nunique()} systems)\n")
    md.append("Distinct observed test formulas per system (union over 5 splits) by arity: " + ", ".join(f"{a} median {cnt[a].median():.0f} (range {cnt[a].min()}–{cnt[a].max()}, total {cnt[a].sum()})" for a in ["binary", "ternary", "quaternary"] if a in cnt) + "\n")
    nq5 = int((cnt.get("quaternary", 0) >= 5).sum()); md.append(f"Systems with ≥5 distinct quaternary test formulas: {nq5} of {len(cnt)}. Share of all test positives (formula×split): " + ", ".join(f"{a} {100*(one.arity_name==a).mean():.0f}%" for a in ["binary", "ternary", "quaternary"]) + "\n")
    S = R.groupby(["method", "system", "arity_name"])[["exp@100", "exp@500", "st@100", "rr_exp"]].mean().reset_index()
    tab = S.groupby(["method", "arity_name"])[["exp@100", "exp@500", "st@100", "rr_exp"]].mean().unstack().round(3)
    nsys = S[S.method == T].groupby("arity_name").system.nunique()
    md.append("\n| method | " + " | ".join(f"{a} R@100 / R@500 / MRR" for a in ["binary", "ternary", "quaternary"]) + " |\n|---|---|---|---|")
    for m in tab.index:
        md.append(f"| {m} | " + " | ".join(f"{tab.loc[m, ('exp@100', a)]:.3f} / {tab.loc[m, ('exp@500', a)]:.3f} / {tab.loc[m, ('rr_exp', a)]:.3f}" for a in ["binary", "ternary", "quaternary"]) + " |")
    md.append(f"\n(n systems contributing: " + ", ".join(f"{a} {nsys.get(a, 0)}" for a in ["binary", "ternary", "quaternary"]) + ")\n")
    o = {"counts": cnt.to_dict(), "n_systems_quat_ge5": nq5, "table": {f"{m}|{c[0]}|{c[1]}": float(tab.loc[m, c]) for m in tab.index for c in tab.columns}}
    md.append("\nBLEND − TPOOL by arity (paired over systems with ≥1 test formula of that arity, two-sided Wilcoxon, bootstrap 95% CI):\n")
    for a in ["binary", "ternary", "quaternary"]:
        for k in ["exp@100", "exp@500"]:
            p = S[(S.arity_name == a)].pivot(index="system", columns="method", values=k)[[B, T]].dropna(); d = (p[B] - p[T]).values
            if len(d) == 0: continue
            rng = np.random.default_rng(0); bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(10000)]
            pv = float(wilcoxon(d).pvalue) if (d != 0).any() else 1.0
            o[f"diff_{a}_{k}"] = dict(n=len(d), diff=float(d.mean()), ci=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], wins=int((d > 0).sum()), losses=int((d < 0).sum()), p=pv)
            md.append(f"- {a} {k.replace('exp','recall')}: {d.mean():+.3f} [{np.percentile(bs,2.5):+.3f}, {np.percentile(bs,97.5):+.3f}], W/L {(d>0).sum()}/{(d<0).sum()} (n={len(d)}), p {pv:.4f}")
    out[study] = o
json.dump(out, open(os.path.join(RES, "m2_stats.json"), "w"), indent=1, default=str)
open(os.path.join(RES, "m2_tables.md"), "w").write("\n".join(md)); print("\n".join(md))
