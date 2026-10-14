"""Regenerate all V05 figures from results/ CSVs (no re-training)."""
import os, numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); R, FIG = os.path.join(HERE, "results"), os.path.join(HERE, "figures"); os.makedirs(FIG, exist_ok=True)
h1 = pd.read_csv(f"{R}/h1/metrics.csv"); M = ["EHP (proposed)", "strongest_PU_baseline (inner-selected)", "template_prior", "PU_RF_leaf1", "PU_RF_ox (prior)", "random"]
for prot in "AB":
    P = h1[(h1.protocol == prot) & h1.method.isin(M)].groupby(["system", "method"])["recall@100"].mean().unstack()[M]
    ax = P.plot.bar(figsize=(11, 4), width=0.8); ax.set_ylabel("recall@100 (mean over splits)"); ax.set_title(f"H1 discovery, Protocol {prot}"); plt.tight_layout(); plt.savefig(f"{FIG}/h1_recall100_protocol{prot}.png", dpi=130); plt.close()
h3 = pd.read_csv(f"{R}/h3/metrics.csv"); n = h3[h3.kind == "new"].groupby(["episode", "arm"])["recall@100"].mean().unstack()
ax = n.plot(marker="o", figsize=(7, 4)); ax.set_xlabel("stream episode"); ax.set_ylabel("recall@100 on new system (mean of 3 orders)"); ax.set_title("H3 memory arms"); plt.tight_layout(); plt.savefig(f"{FIG}/h3_new_system_recall.png", dpi=130); plt.close()
p8 = f"{R}/phase8/regression_metrics.csv"
if os.path.exists(p8):
    G = pd.read_csv(p8).groupby(["target_system", "model"]).MAE.mean().unstack(); G = G[G.mean().sort_values().index]
    ax = G.plot.box(figsize=(9, 4), rot=20); ax.set_ylabel("MAE, DFT Ef (eV/atom)"); ax.set_title("Phase 8: leave-one-system-out regression"); plt.tight_layout(); plt.savefig(f"{FIG}/phase8_regression_mae.png", dpi=130); plt.close()
ab = f"{R}/exploratory/ablation_metrics.csv"
if os.path.exists(ab):
    A = pd.read_csv(ab).groupby("method")["recall@100"].mean().sort_values(); ax = A.plot.barh(figsize=(7, 4)); ax.set_xlabel("recall@100 (Protocol A)"); ax.set_title("Exploratory ablations"); plt.tight_layout(); plt.savefig(f"{FIG}/exploratory_ablations.png", dpi=130); plt.close()
print(sorted(os.listdir(FIG)))
