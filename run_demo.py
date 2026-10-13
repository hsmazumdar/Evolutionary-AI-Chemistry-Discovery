#!/usr/bin/env python3
"""One command runs the whole EvolutionaryChemistry demo:   python run_demo.py   (add --quick for a smoke test)
All data is read from ./data (no downloads). All outputs go to ./results."""
import argparse, copy, json, time, glob, os
from math import gcd
from functools import reduce
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from sklearn.linear_model import RidgeCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from evochem.features import load_elements, parse_comp, featurize
from evochem.gp import GP
from evochem.hull import TrainingHull, comp_vec
from evochem.memory import KnowledgeMemory
from evochem import periodicity
from evochem.discovery import CandidateSpace, base_score, choose_lambda, hits, analogy_mask

ap = argparse.ArgumentParser(); ap.add_argument("--quick", action="store_true"); args = ap.parse_args()
POP, GENS, EXTRA = (100, 10, 5) if args.quick else (300, 40, 20)
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, "data"); R = os.path.join(HERE, "results")
os.makedirs(R, exist_ok=True); T0 = time.time(); EL = ["Fe", "Na", "O", "P"]; MAXTOT = 30; KS = [10, 25, 50, 100, 200, 500, 1000]
log = lambda *a: print(f"[{time.time()-T0:6.1f}s]", *a, flush=True)

# ---------------- data ----------------
el = load_elements(os.path.join(D, "elements_118.csv"))
df = pd.read_csv(os.path.join(D, "poc_Fe-Na-O-P_expt_formulas.csv")).sort_values("idx").reset_index(drop=True)
comps = [parse_comp(c) for c in df.composition_reduced]; y = df.formation_energy_per_atom_eV.values
X, fnames = featurize(comps, el); Xo, fnames_o = featurize(comps, el, use_oxidation=True)
splits = {}
for f in sorted(glob.glob(os.path.join(D, "splits_Fe-Na-O-P", "random_split_seed*.json")), key=lambda s: int(s.split("seed")[1][:-5])):
    splits[os.path.basename(f)[:-5]] = json.load(open(f))
splits["family_heldout"] = json.load(open(os.path.join(D, "splits_Fe-Na-O-P", "group_heldout_stoichiometry_family.json")))
splits["quaternary_heldout"] = json.load(open(os.path.join(D, "splits_Fe-Na-O-P", "group_heldout_quaternary.json")))
if args.quick: splits = {k: splits[k] for k in list(splits)[:2] + ["family_heldout"]}
log(f"{len(df)} experimentally observed Fe-Na-O-P formulas, {X.shape[1]} element-attribute features, {len(splits)} splits")

# ---------------- candidate space for Discovery A ----------------
cs = CandidateSpace(EL, el, MAXTOT)
log(f"candidate space: {len(cs.t)} formulas FeaNabOcPd with a+b+c+d<={MAXTOT}")

def mae(a, b): return float(np.mean(np.abs(np.asarray(a) - np.asarray(b))))

# ---------------- main loop over splits ----------------
rows, disc, contra, curves, best_eqs = [], [], [], {}, {}
for sname, sp in splits.items():
    tr, te = np.array(sp["train"]), np.array(sp["test"]); seed = int(sp.get("seed", 0))
    res = {"split": sname, "n_train": len(tr), "n_test": len(te)}
    res["mean"] = mae(np.full(len(te), y[tr].mean()), y[te])
    lin = make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-3, 3, 13))).fit(X[tr], y[tr]); res["linear"] = mae(lin.predict(X[te]), y[te])
    rf = RandomForestRegressor(300, random_state=seed, n_jobs=-1).fit(X[tr], y[tr]); res["random_forest"] = mae(rf.predict(X[te]), y[te])
    # --- evolutionary rule discovery (test MAE per generation is logged for the plot only, never used for selection)
    curve = []; mem = KnowledgeMemory(f"Fe-Na-O-P formation energy, split {sname}")
    def cb(gp, g, phase="evolution", reason="lower fitness (error + complexity) found"):
        curve.append((g, gp.history[-1]["train_mae"], mae(gp.predict(X[te]), y[te]), len(gp.best)))
        mem.consider(g, gp.to_str(), len(gp.best), gp.history[-1]["train_mae"], len(tr), phase, reason)
    gp = GP(fnames, pop_size=POP, generations=GENS, seed=seed).fit(X[tr], y[tr], callback=cb)
    res["GP_evolved"] = mae(gp.predict(X[te]), y[te]); res["GP_equation"] = gp.to_str(); res["GP_nodes"] = len(gp.best)
    # --- contradiction-driven learning
    resid = y[tr] - gp.predict(X[tr]); thr = 2.5 * np.mean(np.abs(resid))
    reliable = (df.n_icsd.values[tr] >= 2)
    flag = (np.abs(resid) > thr) & reliable
    contradictions = [{"formula": df.formula[i], "Ef_DFT": float(y[i]), "Ef_rule": float(y[i] - r), "n_icsd": int(df.n_icsd[i])}
                      for i, r, f in zip(tr, resid, flag) if f]
    within = float(np.mean(np.abs(resid) < 0.15))
    mem.annotate_current(confidence={"fraction_train_within_0.15eV": round(within, 3), "train_MAE": round(float(np.mean(np.abs(resid))), 4)},
                         limits={"trained_on": f"{len(tr)} Fe-Na-O-P formulas", "mean_EN_range": [round(float(X[tr, 0].min()), 3), round(float(X[tr, 0].max()), 3)],
                                 "note": "valid only inside the Fe-Na-O-P system and DFT (GGA/GGA+U/r2SCAN) energies"},
                         contradictions=contradictions)
    control = copy.deepcopy(gp); weighted = copy.deepcopy(gp)
    control.fit(X[tr], y[tr], generations=EXTRA)
    w = np.where(flag, 3.0, 1.0)
    curve_len = len(curve)
    weighted.fit(X[tr], y[tr], w=w, generations=EXTRA,
                 callback=lambda g_, i: cb(g_, i, "contradiction-driven", f"re-weighted {int(flag.sum())} contradicting compounds x3"))
    c_after = mae(weighted.predict(X[te]), y[te]); c_ctrl = mae(control.predict(X[te]), y[te])
    fixed = [float(np.abs(y[i] - weighted.predict(X[i:i+1])[0])) for i in tr[flag]]
    contra.append({"split": sname, "n_flagged": int(flag.sum()), "flagged": [c["formula"] for c in contradictions],
                   "test_MAE_before": res["GP_evolved"], "test_MAE_control_continue": c_ctrl, "test_MAE_contradiction_weighted": c_after,
                   "flagged_abs_err_before": float(np.mean(np.abs(resid[flag]))) if flag.any() else None,
                   "flagged_abs_err_after": float(np.mean(fixed)) if fixed else None,
                   "train_MAE_unweighted_after": mae(weighted.predict(X[tr]), y[tr]), "train_MAE_control": mae(control.predict(X[tr]), y[tr])})
    mem.annotate_current(extra={"after_contradiction_cycle_test_note": "test MAE is reported in results only, never used by the learner"})
    mem.save(os.path.join(R, f"memory_{sname}.json"), os.path.join(R, f"memory_{sname}.md")) if sname in ("random_split_seed0", "family_heldout") else None
    # --- ablation: same GP with oxidation-state (charge balance) features
    gpo = GP(fnames_o, pop_size=POP, generations=GENS, seed=seed).fit(Xo[tr], y[tr])
    res["GP_with_oxidation_states"] = mae(gpo.predict(Xo[te]), y[te]); res["GP_ox_equation"] = gpo.to_str()
    curves[sname] = curve; best_eqs[sname] = gp.to_str(); rows.append(res)
    # --- Discovery A (existence): hull from TRAINING compounds only; lam picked by inner CV on training only
    def gp_fp(itr, XX=X, XC=cs.X, names=fnames):
        return GP(names, pop_size=POP, generations=GENS, seed=seed).fit(XX[itr], y[itr]).predict(XC)
    def gpo_fp(itr): return gp_fp(itr, Xo, cs.Xo, fnames_o)
    def rf_fp(itr): return RandomForestRegressor(300, random_state=seed, n_jobs=-1).fit(X[itr], y[itr]).predict(cs.X)
    for mname, fp, full_pred, XX, XC in [("GP+hull", gp_fp, gp.predict(cs.X), X, cs.X), ("GP_ox+hull", gpo_fp, gpo.predict(cs.Xo), Xo, cs.Xo),
                                         ("RF+hull", rf_fp, rf.predict(cs.X), X, cs.X)]:
        e, dd = base_score(full_pred, cs, comps, y, tr, XX[tr], XC)
        d0 = hits(e, cs, comps, tr, te, KS); d0.pop("order"); d0.update(split=sname, method=mname + " (raw)"); disc.append(d0)
        if True:
            lam, inner = choose_lambda(fp, cs, comps, y, XX, XC, tr, seed=seed)
            d1 = hits(e + lam * dd, cs, comps, tr, te, KS); order = d1.pop("order")
            d1.update(split=sname, method=mname + " + domain (inner-CV lam)", lam=lam); disc.append(d1)
    am = analogy_mask(cs, comps, tr); rng_a = np.random.default_rng(seed)
    for mname, sc in [("analogy templates, random order", rng_a.random(len(cs.t))),
                      ("analogy templates ranked by GP+hull", base_score(gp.predict(cs.X), cs, comps, y, tr, X[tr], cs.X)[0]),
                      ("analogy templates ranked by GP_ox+hull", base_score(gpo.predict(cs.Xo), cs, comps, y, tr, Xo[tr], cs.Xo)[0])]:
        d = hits(np.where(am, sc, 1e6 + sc), cs, comps, tr, te, KS); order = d.pop("order")
        d.update(split=sname, method=mname, n_analogy_candidates=int(am.sum())); disc.append(d)
        if sname == "random_split_seed0" and mname.endswith("GP_ox+hull"): top_seed0 = [cs.name(j) for j in order[:20]]
    d = hits(cs.Xo[:, -1], cs, comps, tr, te, KS); d.pop("order"); d.update(split=sname, method="charge_balance_only (uses ox. states)"); disc.append(d)
    if sname == "random_split_seed0": parity = (te, gp.predict(X[te]), rf.predict(X[te]), lin.predict(X[te]))
    log(f"{sname:22s} MAE mean {res['mean']:.3f} lin {res['linear']:.3f} RF {res['random_forest']:.3f} GP {res['GP_evolved']:.3f} GPox {res['GP_with_oxidation_states']:.3f} | {gp.to_str()}")

tab = pd.DataFrame(rows); tab.to_csv(os.path.join(R, "property_mae_by_split.csv"), index=False)
dtab = pd.DataFrame(disc); dtab.to_csv(os.path.join(R, "discovery_recall_by_split.csv"), index=False)
ctab = pd.DataFrame(contra); ctab.to_csv(os.path.join(R, "contradiction_by_split.csv"), index=False)
json.dump(curves, open(os.path.join(R, "learning_curves.json"), "w"))
json.dump(top_seed0, open(os.path.join(R, "discovery_top20_seed0_analogy_GPox.json"), "w"))

# ---------------- periodicity teaser ----------------
mp = pd.read_csv(os.path.join(D, "mp_expt_observed_subset.csv.gz"))
vocab, embs, n_used = periodicity.element_embeddings(mp, EL)
Zof = el["Z"].to_dict(); labels, kgroups, per = periodicity.evaluate(vocab, embs, Zof, n_null=200 if args.quick else 1000)
json.dump({"n_compounds_used": n_used, "elements": vocab, "true_groups": labels, "k": kgroups,
           "results": per}, open(os.path.join(R, "periodicity.json"), "w"), indent=1)
log(f"periodicity: {len(vocab)} elements, {n_used} compounds, k={kgroups}: " +
    "; ".join(f"{k}: ARI {v['ARI']:.3f} (null {v['ARI_null_mean']:.3f}, p={v['p_value']:.3f}), NN same group {v['nn_same_group']:.2f} vs {v['nn_same_group_null']:.2f}" for k, v in per.items()))

# ---------------- figures ----------------
rand = tab[tab.split.str.startswith("random")]
c0 = np.array(curves["random_split_seed0"])
fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(c0[:, 0], c0[:, 1], label="train MAE (what the learner sees)"); ax.plot(c0[:, 0], c0[:, 2], label="hidden-40% MAE (never used by learner)")
ax.axvline(GENS - 0.5, color="gray", ls=":"); ax.text(GENS, ax.get_ylim()[1] * 0.95, "contradiction-driven\ncycle", fontsize=8, va="top")
ax.axhline(rand[rand.split == "random_split_seed0"]["mean"].iloc[0], color="k", ls="--", lw=0.8, label="mean-predictor baseline")
ax.set_xlabel("generation"); ax.set_ylabel("MAE formation energy (eV/atom)"); ax.set_title("Evolution of the best rule (split seed0)"); ax.legend(fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(R, "fig1_learning_curve.png"), dpi=130); plt.close(fig)

te, pg, pr, pl = parity
fig, axs = plt.subplots(1, 3, figsize=(12, 4), sharex=True, sharey=True)
for ax, p, nm in zip(axs, [pg, pr, pl], ["Evolved equation (GP)", "Random forest", "Linear (ridge)"]):
    ax.scatter(y[te], p, s=18); lo, hi = y.min() - 0.2, 0.3; ax.plot([lo, hi], [lo, hi], "k--", lw=0.8)
    ax.set_title(f"{nm}\nhidden-40% MAE {mae(p, y[te]):.3f} eV/atom"); ax.set_xlabel("DFT formation energy (eV/atom)")
axs[0].set_ylabel("predicted"); fig.tight_layout(); fig.savefig(os.path.join(R, "fig2_parity_seed0.png"), dpi=130); plt.close(fig)

fig, ax = plt.subplots(figsize=(7, 4)); dr = dtab[dtab.split.str.startswith("random")]
for m in dr.method.unique():
    if "(raw)" in m: continue
    s = dr[dr.method == m]; ax.plot(KS, [s[f"hits@{k}"].mean() for k in KS], "o-", label=m)
ax.plot(KS, [dr[dr.method == "GP+hull (raw)"][f"random@{k}"].mean() for k in KS], "k--", label="random guessing")
ax.set_xscale("log"); ax.set_xlabel("top-k candidates examined"); ax.set_ylabel("hidden real compounds found (mean of 10 splits)")
ax.set_title(f"Discovery A: re-finding hidden compounds among {int(dr.N_ranked.mean())} candidates"); ax.legend(fontsize=7)
fig.tight_layout(); fig.savefig(os.path.join(R, "fig3_recall_at_k.png"), dpi=130); plt.close(fig)

from sklearn.decomposition import PCA
E = embs["co-occurrence (PPMI-SVD)"]; P2 = PCA(2, random_state=0).fit_transform(E / np.linalg.norm(E, axis=1, keepdims=True))
cl = per["co-occurrence (PPMI-SVD)"]["clusters"]
fig, axs = plt.subplots(1, 2, figsize=(13, 6))
groups = sorted(set(labels), key=lambda g: (g.isalpha(), int(g) if g.isdigit() else 0, g)); cmap = plt.get_cmap("tab20")
for ax, col, title in [(axs[0], [groups.index(g) for g in labels], "coloured by TRUE periodic group"),
                       (axs[1], cl, "coloured by LEARNED cluster")]:
    ax.scatter(P2[:, 0], P2[:, 1], c=col, cmap=cmap, s=60)
    for (a, b), s in zip(P2, vocab): ax.annotate(s, (a, b), fontsize=7, xytext=(2, 2), textcoords="offset points")
    ax.set_title(title); ax.set_xticks([]); ax.set_yticks([])
fig.suptitle(f"Element map learned only from compound co-occurrence (ARI vs groups = {per['co-occurrence (PPMI-SVD)']['ARI']:.2f})")
fig.tight_layout(); fig.savefig(os.path.join(R, "fig4_element_map.png"), dpi=130); plt.close(fig)

# ---------------- summary ----------------
def ms(s): return f"{s.mean():.3f} ± {s.std():.3f}"
L = ["# Results (generated by run_demo.py, do not edit by hand)", "", f"Runtime: {time.time()-T0:.0f} s. GP population {POP}, {GENS} generations (+{EXTRA} contradiction cycle).", "",
     "## Formation-energy MAE on hidden compounds (eV/atom)", "", "| split | n test | mean | linear | random forest | evolved GP | GP + ox. states |", "|---|---|---|---|---|---|---|",
     f"| 10 random 60/40 (mean ± sd) | {int(rand.n_test.mean())} | {ms(rand['mean'])} | {ms(rand.linear)} | {ms(rand.random_forest)} | {ms(rand.GP_evolved)} | {ms(rand.GP_with_oxidation_states)} |"]
for _, r in tab[~tab.split.str.startswith("random")].iterrows():
    L.append(f"| {r.split} | {r.n_test} | {r['mean']:.3f} | {r.linear:.3f} | {r.random_forest:.3f} | {r.GP_evolved:.3f} | {r.GP_with_oxidation_states:.3f} |")
L += ["", "## Evolved equations", ""] + [f"- **{k}**: `{v}`" for k, v in best_eqs.items()]
L += ["", "## Discovery A: hidden compounds found in top-k (mean over 10 random splits)", "",
      "| method | " + " | ".join(f"top {k}" for k in KS) + " | median rank |", "|---|" + "---|" * (len(KS) + 1)]
for m in dr.method.unique():
    s = dr[dr.method == m]; L.append(f"| {m} | " + " | ".join(f"{s[f'hits@{k}'].mean():.1f}" for k in KS) + f" | {s.median_rank.mean():.0f} |")
L.append("| random guessing | " + " | ".join(f"{dr[f'random@{k}'].mean():.2f}" for k in KS) + " | – |")
L.append(f"\nAnalogy candidates per split: {dr.n_analogy_candidates.mean():.0f}. Raw = whole 41k space ranked by predicted energy above the training hull.")
L.append(f"\nHidden multi-element compounds per split: {dr.n_hidden_multi.mean():.1f}, of which inside the candidate space: {dr.n_hidden_in_space.mean():.1f}; candidates ranked: {dr.N_ranked.mean():.0f}.")
cr = ctab[ctab.split.str.startswith("random")]
L += ["", "## Contradiction-driven learning (random splits)", "",
      f"- Flagged reliable contradictions per split: {cr.n_flagged.mean():.1f}",
      f"- Hidden-40% MAE: before {ms(cr.test_MAE_before)}, continue normally {ms(cr.test_MAE_control_continue)}, continue with contradictions weighted x3 {ms(cr.test_MAE_contradiction_weighted)}",
      f"- Weighted beat control on {int((cr.test_MAE_contradiction_weighted < cr.test_MAE_control_continue - 1e-9).sum())}/{len(cr)} splits, tied on {int((abs(cr.test_MAE_contradiction_weighted - cr.test_MAE_control_continue) <= 1e-9).sum())}",
      f"- Error on the flagged compounds themselves: {cr.flagged_abs_err_before.mean():.3f} -> {cr.flagged_abs_err_after.mean():.3f} eV/atom"]
L += ["", "## Periodicity teaser", "", f"{len(vocab)} elements, {n_used} experimentally observed MP compounds (Fe-Na-O-P-only compounds excluded), clustered into k={kgroups} clusters (= number of true groups present).", "",
      "| embedding | ARI | ARI random (mean / 95th pct) | p | nearest neighbour in same group | random |", "|---|---|---|---|---|---|"]
for k, v in per.items():
    L.append(f"| {k} | {v['ARI']:.3f} | {v['ARI_null_mean']:.3f} / {v['ARI_null_p95']:.3f} | {v['p_value']:.3f} | {v['nn_same_group']:.2f} | {v['nn_same_group_null']:.2f} |")
open(os.path.join(R, "RESULTS.md"), "w").write("\n".join(L) + "\n")
log("done; see results/RESULTS.md")
