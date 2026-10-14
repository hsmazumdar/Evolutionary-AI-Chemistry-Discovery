"""Phase 9: confirmatory statistics per V05_RESEARCH_PROTOCOL.md §7. Unit = system.
One-sided paired Wilcoxon, Cohen's d_z, system-cluster bootstrap 95% CI of the mean difference, Holm across primary tests.
H3 (intersection-union): proposed must beat EACH of 5 controls; the H3 p-value is the max over the 5 one-sided tests.
Writes results/statistics.json and results/statistics_tables.md."""
import os, json, numpy as np, pandas as pd
from scipy.stats import wilcoxon
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); R = os.path.join(HERE, "results")
B = 10000

def paired(a, b, name, metric="recall@100"):
    a, b = a.align(b, join="inner"); d = (a - b).values
    p = wilcoxon(d, alternative="greater").pvalue if np.any(d != 0) else 1.0
    rng = np.random.default_rng(0); bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(B)]
    return dict(test=name, metric=metric, n_systems=len(d), mean_a=a.mean(), mean_b=b.mean(), mean_diff=d.mean(), ci95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                d_z=float(d.mean() / d.std(ddof=1)) if d.std(ddof=1) > 0 else 0.0, wins=int((d > 0).sum()), losses=int((d < 0).sum()), p_one_sided=float(p))

def sysmean(df, method, metric="recall@100", col="method"): return df[df[col] == method].groupby("system")[metric].mean()

def holm(ps):
    o = np.argsort(ps); m = len(ps); adj = np.zeros(m); run = 0
    for i, k in enumerate(o): run = max(run, min(1, (m - i) * ps[k])); adj[k] = run
    return adj

h1 = pd.read_csv(f"{R}/h1/metrics.csv"); h2 = pd.read_csv(f"{R}/h2/metrics.csv"); h3 = pd.read_csv(f"{R}/h3/metrics.csv")
E, S = "EHP (proposed)", "strongest_PU_baseline (inner-selected)"
prim = []
h1A = h1[h1.protocol == "A"]; prim.append(paired(sysmean(h1A, E), sysmean(h1A, S), "H1: EHP > strongest PU baseline (Protocol A)"))
prim.append(paired(sysmean(h2, "PU_RF pooled (source+target)"), sysmean(h2, "PU_RF target-only"), "H2a: PU_RF transfer > target-only (Protocol C)"))
prim.append(paired(sysmean(h2, "EHP pooled (source+target)"), sysmean(h2, "EHP target-only"), "H2b: EHP transfer > target-only (Protocol C)"))
new = h3[h3.kind == "new"]; ctrl = ["scratch", "sequential_finetune", "replay", "V04_archive", "full_data_retrain"]
h3sub = [paired(sysmean(new, "proposed_versioned_memory", col="arm"), sysmean(new, c, col="arm"), f"H3 sub: memory > {c}") for c in ctrl]
worst = max(h3sub, key=lambda r: r["p_one_sided"]); prim.append(dict(worst, test="H3: memory > every control (IUT, max p)"))
adj = holm(np.array([r["p_one_sided"] for r in prim]))
for r, a in zip(prim, adj): r["p_holm"] = float(a); r["supported"] = bool(a < 0.05 and r["mean_diff"] >= 0.02)
# forgetting: per arm, mean drop of recall@100 on a system between when it was new and final episode
old = h3[h3.kind == "old"]; fg = {}
for arm in h3.arm.unique():
    dd = []
    for o in h3.order.unique():
        n = new[(new.arm == arm) & (new.order == o)].set_index("system")["recall@100"]; last = old[(old.arm == arm) & (old.order == o)]; last = last[last.episode == last.episode.max()].set_index("eval_system")["recall@100"]
        dd += list((n.reindex(last.index) - last).values)
    fg[arm] = float(np.mean(dd))
sens = []
for prot, lab in [("B", "Protocol B")]:
    x = h1[h1.protocol == prot]; sens.append(paired(sysmean(x, E), sysmean(x, S), f"H1 sensitivity {lab}"))
for m in ["recall@50", "recall@500", "MRR"]: sens.append(paired(sysmean(h1A, E, m), sysmean(h1A, S, m), f"H1 sensitivity {m}", m))
a, b = sysmean(h1A, E), sysmean(h1A, S)
for lab, keep in [("excl. Fe-Na-O-P", lambda s: s != "Fe-Na-O-P"), ("excl. H-containing", lambda s: "H" not in s.split("-"))]:
    k = [s for s in a.index if keep(s)]; sens.append(paired(a[k], b[k], f"H1 sensitivity {lab}"))
# exploratory, two-sided reading: EHP vs each baseline (Protocol A) and the reverse direction for H1
expl = [paired(sysmean(h1A, S), sysmean(h1A, E), "Exploratory: strongest PU baseline > EHP (Protocol A)")]
expl.append(paired(sysmean(h2, "template_prior pooled"), sysmean(h2, "template_prior target-only"), "Exploratory (not pre-registered model): template prior pooled > target-only"))
out = dict(primary=prim, h3_subtests=h3sub, forgetting_mean_drop_recall100=fg, sensitivity=sens, exploratory=expl)
json.dump(out, open(f"{R}/statistics.json", "w"), indent=1, default=float)
def tab(rows, holmcol=False):
    s = "| test | n | mean A | mean B | diff | 95% CI | d_z | W/L | p (1-sided) |" + (" p Holm | supported |" if holmcol else "") + "\n|" + "---|" * (9 + 2 * holmcol) + "\n"
    for r in rows: s += f"| {r['test']} | {r['n_systems']} | {r['mean_a']:.3f} | {r['mean_b']:.3f} | {r['mean_diff']:+.3f} | [{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}] | {r['d_z']:+.2f} | {r['wins']}/{r['losses']} | {r['p_one_sided']:.4f} |" + (f" {r['p_holm']:.4f} | {'YES' if r['supported'] else 'no'} |" if holmcol else "") + "\n"
    return s
md = "## Primary (Holm across 4 tests)\n" + tab(prim, True) + "\n## H3 sub-tests\n" + tab(h3sub) + "\n## Forgetting (mean recall@100 drop, new→final)\n" + "\n".join(f"- {k}: {v:+.3f}" for k, v in fg.items()) + "\n\n## Sensitivity\n" + tab(sens) + "\n## Exploratory\n" + tab(expl)
open(f"{R}/statistics_tables.md", "w").write(md); print(md)

# ---- Phase 8 regression benchmark (exploratory; two-sided; system = unit; lower MAE better) ----
from scipy.stats import wilcoxon as _w
rp = f"{R}/phase8/regression_metrics.csv"
if os.path.exists(rp):
    G = pd.read_csv(rp); P = G.groupby(["model", "target_system"]).MAE.mean().unstack(0); rows = []
    for m in P.columns:
        rng = np.random.default_rng(0); v = P[m].values; bs = [v[rng.integers(0, len(v), len(v))].mean() for _ in range(B)]
        d = (P[m] - P["V03_GP"]).values; p = _w(d).pvalue if m != "V03_GP" and np.any(d != 0) else np.nan
        rows.append(dict(model=m, mean_MAE=v.mean(), ci95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], diff_vs_V03_GP=d.mean(), p_two_sided_vs_GP=p, runtime_s_total=float(G[G.model == m].runtime_s.sum())))
    rows.sort(key=lambda r: r["mean_MAE"]); out["phase8_regression"] = rows; json.dump(out, open(f"{R}/statistics.json", "w"), indent=1, default=float)
    md += "\n## Phase 8 regression (DFT Ef, eV/atom, leave-one-system-out; exploratory, two-sided vs V03 GP)\n| model | mean MAE | 95% CI | diff vs GP | p | runtime s |\n|---|---|---|---|---|---|\n"
    md += "".join(f"| {r['model']} | {r['mean_MAE']:.3f} | [{r['ci95'][0]:.3f}, {r['ci95'][1]:.3f}] | {r['diff_vs_V03_GP']:+.3f} | {r['p_two_sided_vs_GP']:.4f} | {r['runtime_s_total']:.0f} |\n" for r in rows)
    open(f"{R}/statistics_tables.md", "w").write(md); print(md[md.index("## Phase 8"):])
