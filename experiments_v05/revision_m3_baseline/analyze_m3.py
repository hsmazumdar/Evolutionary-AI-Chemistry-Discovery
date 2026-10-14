"""M3 analysis (exploratory). Compares SynthNN-style composition PU baselines with the frozen arms on identical splits,
using tie-fair expected recall (M1 definition), per-system means, bootstrap CI and two-sided Wilcoxon."""
import os, json, numpy as np, pandas as pd
from scipy.stats import wilcoxon
H = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(H); RES = os.path.join(H, "results"); M1 = os.path.join(V, "revision_m1_ties", "results")
B, T, SP, ST = "BLEND (RF + pooled template)", "TPOOL (pooled template)", "SYNTHNN-POOL (composition PU, pooled)", "SYNTHNN-TARGET (composition PU, target only)"
KEEP = [B, T, "RF alone", "template target-only", "random"]; KS = [10, 50, 100, 500, 1000]; AR = {2: "binary", 3: "ternary", 4: "quaternary"}
def load(s):
    a = pd.read_csv(os.path.join(M1, f"per_test_{s}.csv.gz")); a = a[a.method.isin(KEEP)]
    b = pd.read_csv(os.path.join(RES, f"per_test_m3_{s}.csv.gz")); R = pd.concat([a, b], ignore_index=True); R["study"] = s
    for k in KS: R[f"r@{k}"] = np.clip((k - R.n_greater) / R.n_tied, 0, 1)
    R["rr"] = 1 / (R.n_greater + (R.n_tied + 1) / 2); return R
sm = lambda R, c, m: R[R.method == m].groupby(["system", "split"])[c].mean().groupby("system").mean()
def comp(a, b):
    d = (a - b).values; rng = np.random.default_rng(0); bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(10000)]
    return dict(n=len(d), a=float(a.mean()), b=float(b.mean()), diff=float(d.mean()), ci=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], wins=int((d > 0).sum()), losses=int((d < 0).sum()), p=float(wilcoxon(d).pvalue) if (d != 0).any() else 1.0)
f = lambda c: f"{c['diff']:+.3f} [{c['ci'][0]:+.3f}, {c['ci'][1]:+.3f}], W/L {c['wins']}/{c['losses']}, p {c['p']:.4f}"
A = {s: load(s) for s in ["decisive", "replication"]}; A["pooled29"] = pd.concat(A.values()); out = {}; md = ["# M3 results: SynthNN-style composition PU baseline (exploratory)\n"]
for st, R in A.items():
    o = {}; md.append(f"\n## {st} ({R.system.nunique()} systems), tie-fair expected recall\n\n| arm | R@10 | R@50 | R@100 | R@500 | R@1000 | MRR |\n|---|---|---|---|---|---|---|")
    arms = [B, T, SP, ST, "template target-only", "RF alone", "random"]
    for m in arms:
        v = [sm(R, f"r@{k}", m).mean() for k in KS] + [sm(R, "rr", m).mean()]; o[m] = v
        md.append(f"| {m} | " + " | ".join(f"{x:.3f}" for x in v) + " |")
    md.append("\nPaired comparisons (two-sided):")
    for a, b in [(SP, T), (SP, B), (SP, ST), (SP, "RF alone"), (ST, "template target-only")]:
        for k in [100, 500]:
            c = comp(sm(R, f"r@{k}", a), sm(R, f"r@{k}", b)); o[f"{a} vs {b} @{k}"] = c; md.append(f"- {a} − {b}, recall@{k}: {f(c)}")
    R2 = R[R.method.isin([B, T, SP])].copy(); R2["ar"] = R2.arity.map(AR)
    g = R2.groupby(["method", "system", "ar"])[["r@100", "r@500"]].mean().groupby(["method", "ar"]).mean().unstack().round(3)
    md.append("\nBy arity (recall@100 / recall@500):\n\n| arm | binary | ternary | quaternary |\n|---|---|---|---|")
    for m in g.index: md.append(f"| {m} | " + " | ".join(f"{g.loc[m, ('r@100', a)]:.3f} / {g.loc[m, ('r@500', a)]:.3f}" for a in ["binary", "ternary", "quaternary"]) + " |")
    out[st] = o
mm = pd.concat([pd.read_csv(os.path.join(RES, f"metrics_m3_{s}.csv")) for s in ["decisive", "replication"]])
md.append("\nInner-validation choices (hidden width, unlabelled ratio), count over splits:\n\n" + mm.groupby(["method", "hidden", "ratio"]).size().to_frame("n").to_markdown())
json.dump(out, open(os.path.join(RES, "m3_stats.json"), "w"), indent=1, default=float); open(os.path.join(RES, "m3_tables.md"), "w").write("\n".join(md)); print("\n".join(md))
