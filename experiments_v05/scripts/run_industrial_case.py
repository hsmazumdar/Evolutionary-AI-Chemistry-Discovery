"""Phase 10: industrial case - prioritising unexplored Na-Fe-P-O (Na-ion cathode family) compositions.
Rankers trained on ALL observed Fe-Na-O-P formulas: (i) the pre-registered H1 winner class (strongest PU baseline,
inner-selected = template_prior on this system), (ii) PU_RF_leaf1, (iii) EXPLORATORY rank-mean of both.
Each candidate is annotated with Materials Project status. Every candidate NOT experimentally observed in the data is a
COMPUTATIONAL HYPOTHESIS only; DFT values are computed (GGA/GGA+U/r2SCAN), never measured."""
import os, sys, json
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, HERE)
from shared.core import *
S = "Fe-Na-O-P"; cs, pos, _ = space(S); c = pos.cand_idx.values; rn = lambda v: v.argsort().argsort() / len(v)
tp = template_prior(cs, c); rf = pu_generic(RF(1), cs.X, c, 0, 15, 5); hy = 0.5 * rn(tp) + 0.5 * rn(rf)
E_ = pd.read_csv(os.path.join(HERE, "data", f"entries_{S}.csv")); E_["key"] = E_.composition_reduced.apply(lambda s: cs.key({k: v for k, v in json.loads(s).items()}) if set(json.loads(s)) <= set(cs.EL) else None)
mp = E_.dropna(subset=["key"]).groupby("key").agg(mp_entries=("material_id", "count"), mp_ids=("material_id", lambda x: " ".join(sorted(x)[:3])), dft_ehull_min=("energy_above_hull_eV", "min"), dft_Ef_min=("formation_energy_per_atom_eV", "min"))
rows = []
for j in np.argsort(-hy):
    if j in set(c): continue
    t = cs.t[j]; m = mp.loc[[t]].iloc[0] if t in mp.index else None
    rows.append(dict(rank=len(rows) + 1, formula=cs.name(j), contains_Na_Fe_P=all(t[cs.EL.index(e)] > 0 for e in ["Na", "Fe", "P"]),
                     rank_template=int((tp > tp[j]).sum() + 1), rank_PU_RF=int((rf > rf[j]).sum() + 1), V03_charge_imbalance_feature=float(cs.Xo[j, -1]),
                     in_MP_computed=m is not None, mp_ids=m.mp_ids if m is not None else "", dft_ehull_min_eV_atom=m.dft_ehull_min if m is not None else np.nan,
                     dft_Ef_min_eV_atom=m.dft_Ef_min if m is not None else np.nan, status="computational hypothesis (not experimentally observed in dataset)"))
    if sum(r['contains_Na_Fe_P'] for r in rows) >= 50 and len(rows) >= 300: break
D = pd.DataFrame(rows); DQ = D[D.contains_Na_Fe_P].copy(); DQ.insert(1, 'rank_within_quaternary', range(1, len(DQ) + 1)); D = D.head(300); os.makedirs(os.path.join(HERE, "results", "industrial"), exist_ok=True); D.to_csv(os.path.join(HERE, "results", "industrial", "fe_na_p_o_candidates_top300.csv"), index=False)
Q = DQ.head(25); DQ.to_csv(os.path.join(HERE, 'results', 'industrial', 'quaternary_top50.csv'), index=False); open(os.path.join(HERE, "results", "industrial", "top25_quaternary.md"), "w").write(Q.drop(columns=["status", "contains_Na_Fe_P"]).to_markdown(index=False, floatfmt=".3f"))
print(Q.drop(columns=["status"]).to_string()); print("in MP among top300:", D.in_MP_computed.sum(), " quaternary in top300:", D.contains_Na_Fe_P.sum())
