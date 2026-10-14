"""Pre-registered analysis of results/metrics.csv -> results/stats.json, results/tables.md"""
import os, json, numpy as np, pandas as pd
from scipy.stats import wilcoxon
D = os.path.dirname(os.path.abspath(__file__)); M = pd.read_csv(f"{D}/results/metrics.csv")
P = lambda m, k="recall@100": M[M.method == m].groupby("system")[k].mean()
def comp(a, b, alt):
    d = (a - b).values; rng = np.random.default_rng(0); bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(10000)]
    return dict(n=len(d), mean_a=a.mean(), mean_b=b.mean(), diff=d.mean(), ci95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], d_z=float(d.mean() / d.std(ddof=1)),
                wins=int((d > 0).sum()), losses=int((d < 0).sum()), p=float(wilcoxon(d, alternative=alt).pvalue), alternative=alt)
B, T = "BLEND (RF + pooled template)", "TPOOL (pooled template)"
prim = comp(P(B), P(T), "greater"); prim["success"] = bool(prim["p"] < 0.05 and prim["diff"] >= 0.02)
sec = {k: comp(P(B, k), P(T, k), "two-sided") for k in ["recall@10", "recall@50", "recall@500", "recall@1000", "MRR"]}
sec["strict-leakage recall@100"] = comp(P("BLEND strict-leakage"), P("TPOOL strict-leakage"), "two-sided")
sec["BLEND vs RF alone recall@100"] = comp(P(B), P("RF alone"), "two-sided")
wdist = M[M.method == B].w.value_counts().sort_index().to_dict()
json.dump(dict(primary=prim, secondary=sec, chosen_w=wdist), open(f"{D}/results/stats.json", "w"), indent=1, default=float)
ks = ["recall@10", "recall@50", "recall@100", "recall@500", "recall@1000", "MRR", "median_rank", "precision@100_observed", "enrichment@100"]
overall = M.groupby(["method", "system"])[ks].mean().groupby("method").mean().sort_values("recall@100", ascending=False)
per = M.groupby(["system", "method"])["recall@100"].mean().unstack()[[B, T, "RF alone", "template target-only", "random"]]; per["BLEND−TPOOL"] = per[B] - per[T]
f = lambda r: f"{r['diff']:+.3f} [{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}], d_z {r['d_z']:+.2f}, W/L {r['wins']}/{r['losses']}, p ({r['alternative']}) {r['p']:.4f}"
md = f"## Primary (confirmatory)\nBLEND {prim['mean_a']:.3f} vs TPOOL {prim['mean_b']:.3f}: diff {f(prim)}; **success = {prim['success']}**\n\n## Secondary (exploratory)\n" + "".join(f"- {k}: {f(v)}\n" for k, v in sec.items()) + f"\nChosen w ({int(sum(wdist.values()))} splits): {wdist}\n\n## All metrics (mean over systems)\n" + overall.round(3).to_markdown() + "\n\n## Per-system recall@100 (mean of 5 splits)\n" + per.round(3).to_markdown()
open(f"{D}/results/tables.md", "w").write(md); print(md)
