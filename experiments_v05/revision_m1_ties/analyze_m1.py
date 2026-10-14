"""M1 analysis (exploratory sensitivity). Re-scores rankings with fair tie handling:
 stable   = original pre-registered rule (np.argsort stable -> candidate enumeration order)
 avgrank  = each test formula gets the mean rank of its tie group, rank = n_greater + (n_tied+1)/2
 expected = exact expectation under uniform random tie-breaking, P(rank<=k) = clip((k-n_greater)/n_tied, 0, 1)
 randomS  = 100 seeds of random tie-breaking (joint permutation inside each tie group), paired stats per seed"""
import os, json, numpy as np, pandas as pd
from scipy.stats import wilcoxon
H = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(H, "results")
KS = [10, 50, 100, 500, 1000]; B, T = "BLEND (RF + pooled template)", "TPOOL (pooled template)"
def comp(a, b, alt):
    d = (a - b).values; rng = np.random.default_rng(0); bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(10000)]
    nz = d[d != 0]; p = float(wilcoxon(d, alternative=alt).pvalue) if len(nz) else 1.0
    return dict(n=len(d), mean_a=float(a.mean()), mean_b=float(b.mean()), diff=float(d.mean()), ci95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                wins=int((d > 0).sum()), losses=int((d < 0).sum()), ties=int((d == 0).sum()), p=p, alternative=alt)
def recall_tables(R):
    out = {}
    for k in KS:
        R[f"stable@{k}"] = (R.stable_rank <= k).astype(float)
        R[f"avgrank@{k}"] = ((R.n_greater + (R.n_tied + 1) / 2) <= k).astype(float)
        R[f"expected@{k}"] = np.clip((k - R.n_greater) / R.n_tied, 0, 1)
    return R
def random_ranks(R, seed):
    rng = np.random.default_rng(seed); r = R.n_greater.values.astype(float).copy()
    for _, idx in R.groupby(["system", "split", "method", "n_greater", "n_tied"]).indices.items():
        t = int(R.n_tied.values[idx[0]]); r[idx] += 1 + rng.choice(t, len(idx), replace=False)
    return r
def sysmean(R, col, m): return R[R.method == m].groupby(["system", "split"])[col].mean().groupby("system").mean()
f = lambda r: f"{r['diff']:+.3f} [{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}], W/L/T {r['wins']}/{r['losses']}/{r['ties']}, p {r['p']:.4f}"
out = {}; md = ["# M1 results: fair tie-breaking (exploratory sensitivity; pre-registered results unchanged)\n"]
Rs = {s: recall_tables(pd.read_csv(os.path.join(RES, f"per_test_{s}.csv.gz"))) for s in ["decisive", "replication"]}
Rs["pooled29"] = pd.concat([Rs["decisive"], Rs["replication"]])
for study, R in Rs.items():
    o = {}; md.append(f"\n## Study: {study} ({R.system.nunique()} systems)\n")
    ts = R[R.method == T]; tb = R[R.method == B]
    o["tie_stats"] = dict(TPOOL_median_tie_group=float(ts.n_tied.median()), TPOOL_mean_tie_group=float(ts.n_tied.mean()), TPOOL_frac_test_in_tie_gt1=float((ts.n_tied > 1).mean()),
                          BLEND_median_tie_group=float(tb.n_tied.median()), BLEND_frac_test_in_tie_gt1=float((tb.n_tied > 1).mean()))
    md.append(f"Tie groups of test formulas: TPOOL median size {o['tie_stats']['TPOOL_median_tie_group']:.0f} (mean {o['tie_stats']['TPOOL_mean_tie_group']:.1f}), {100*o['tie_stats']['TPOOL_frac_test_in_tie_gt1']:.0f}% of test formulas tied with ≥1 other candidate; BLEND median {o['tie_stats']['BLEND_median_tie_group']:.0f}, {100*o['tie_stats']['BLEND_frac_test_in_tie_gt1']:.0f}% tied.\n")
    alt0 = "greater" if study != "pooled29" else "two-sided"
    md.append("\n| scoring | k | BLEND | TPOOL | BLEND−TPOOL [95% CI], W/L/T, Wilcoxon p | \n|---|---|---|---|---|")
    for sc in ["stable", "avgrank", "expected"]:
        for k in KS:
            alt = alt0 if k == 100 else "two-sided"; c = comp(sysmean(R, f"{sc}@{k}", B), sysmean(R, f"{sc}@{k}", T), alt); o[f"{sc}@{k}"] = c
            md.append(f"| {sc} | {k} | {c['mean_a']:.3f} | {c['mean_b']:.3f} | {f(c)} ({alt}) |")
    # other arms under expected scoring
    md.append("\n**All arms, recall@100 (stable → expected under fair ties):**\n")
    for m in sorted(R.method.unique()):
        a, e = sysmean(R, "stable@100", m).mean(), sysmean(R, "expected@100", m).mean(); o.setdefault("arms", {})[m] = dict(stable=float(a), expected=float(e))
        md.append(f"- {m}: {a:.3f} → {e:.3f}")
    c = comp(sysmean(R, "expected@100", "TPOOL + RF tie-break only"), sysmean(R, "expected@100", T), "two-sided"); o["lexRF_vs_TPOOL_expected@100"] = c
    md.append(f"\nExploratory control, TPOOL with RF used only as tie-breaker vs TPOOL (fair ties), recall@100: {f(c)}")
    c = comp(sysmean(R, "expected@100", B), sysmean(R, "expected@100", "TPOOL + RF tie-break only"), "two-sided"); o["BLEND_vs_lexRF_expected@100"] = c
    md.append(f"\nBLEND vs TPOOL+RF-tie-break-only, recall@100 (fair ties): {f(c)}\n")
    # random seeds
    seeds = []; RR = R.copy()
    for sd in range(100):
        RR["rr"] = random_ranks(RR, sd)
        row = {}
        for k in [100, 500]:
            RR[f"r@{k}"] = (RR.rr <= k).astype(float)
            c = comp(sysmean(RR, f"r@{k}", B), sysmean(RR, f"r@{k}", T), alt0 if k == 100 else "two-sided"); row[f"diff@{k}"] = c["diff"]; row[f"p@{k}"] = c["p"]; row[f"wins@{k}"] = c["wins"]; row[f"losses@{k}"] = c["losses"]
            row[f"TPOOL@{k}"] = c["mean_b"]; row[f"BLEND@{k}"] = c["mean_a"]
        seeds.append(row)
    S = pd.DataFrame(seeds); o["random_seeds"] = {c: dict(mean=float(S[c].mean()), p2_5=float(S[c].quantile(.025)), p97_5=float(S[c].quantile(.975))) for c in S}
    o["random_seeds"]["frac_success@100"] = float(((S["p@100"] < 0.05) & (S["diff@100"] >= 0.02)).mean()); o["random_seeds"]["frac_p_lt_0.05@100"] = float((S["p@100"] < 0.05).mean())
    rs = o["random_seeds"]
    md.append(f"\n**Random tie-breaking, 100 seeds:** recall@100 TPOOL {rs['TPOOL@100']['mean']:.3f} [{rs['TPOOL@100']['p2_5']:.3f}, {rs['TPOOL@100']['p97_5']:.3f}], BLEND {rs['BLEND@100']['mean']:.3f}; "
              f"diff {rs['diff@100']['mean']:+.3f} (seed 2.5–97.5%: {rs['diff@100']['p2_5']:+.3f} to {rs['diff@100']['p97_5']:+.3f}); Wilcoxon p median-ish mean {rs['p@100']['mean']:.3f} (range {rs['p@100']['p2_5']:.3f}–{rs['p@100']['p97_5']:.3f}); "
              f"fraction of seeds meeting the pre-registered rule (p<0.05 and diff≥0.02): {rs['frac_success@100']:.2f}; p<0.05 alone: {rs['frac_p_lt_0.05@100']:.2f}. recall@500 diff {rs['diff@500']['mean']:+.3f} ({rs['diff@500']['p2_5']:+.3f} to {rs['diff@500']['p97_5']:+.3f}).\n")
    out[study] = o
json.dump(out, open(os.path.join(RES, "m1_stats.json"), "w"), indent=1, default=float)
open(os.path.join(RES, "m1_tables.md"), "w").write("\n".join(md)); print("\n".join(md))
