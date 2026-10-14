"""V05 unit/integration tests (fast; run with `pytest experiments_v05/tests`)."""
import os, sys, json, hashlib
import numpy as np, pandas as pd, pytest
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, HERE)
from shared.core import *

def test_manifest_hashes():
    M = json.load(open(os.path.join(HERE, "data", "MANIFEST.json"))); h = lambda f: hashlib.sha256(open(os.path.join(HERE, "data", f), "rb").read()).hexdigest()
    assert h("formulas_v05.csv") == M["formulas_v05_sha256"]
    for s_, info in M["systems"].items(): assert h(f"entries_{s_}.csv") == info["entries_sha256"], s_
    assert M["publication_dates"].startswith("UNAVAILABLE")

def test_dataset_labels_and_carbon_free():
    F = formulas()
    assert not any("C" in s.split("-") for s in F.system.unique())
    assert (F[F.experimentally_observed].n_icsd_unique > 0).all() and (F[~F.experimentally_observed].n_icsd_unique == 0).all()
    assert {"dft_Ef_min_eV_atom", "measured_dHf_eV_atom"} <= set(F.columns)
    assert sorted(F.system.unique()) == sorted(SYSTEMS) and len(SYSTEMS) == 9

def test_splits_disjoint_and_frozen():
    for prot in "AB":
        for sid, tr, te in splits("Fe-Na-O-P", prot):
            assert len(np.intersect1d(tr, te)) == 0 and tr.dtype.kind == "i" and te.dtype.kind == "i"
    a, b = splits("Fe-Na-O-P", "A"), splits("Fe-Na-O-P", "A")
    assert all((x[2] == y[2]).all() for x, y in zip(a, b))

def test_family_holdout_no_family_leak():
    cs, pos, _ = space("Fe-Na-O-P"); fam = pos.formula_anonymous.values
    for sid, tr, te in splits("Fe-Na-O-P", "B"): assert not (set(fam[tr]) & set(fam[te]))

def test_rank_metrics_perfect_and_excludes_train():
    s = np.arange(100, dtype=float); m = rank_metrics(s, np.array([99]), np.array([98, 97]))
    assert m["recall@10"] == 1.0 and m["N_ranked"] == 99 and m["MRR"] == pytest.approx((1 + 0.5) / 2)

def test_ehp_primitive_only_and_runs():
    names = prim_names(); assert not any("ox" in n.lower() or "charge" in n.lower() for n in names)
    cs, pos, _ = space("Fe-Na-O-P"); c = pos.cand_idx.values[:30]
    e = EHP(names, pop=20, gens=2, bags=1, seed=0); H = e.fit(cs.X, c); s = e.score(cs.X, H, e.val)
    assert len(H) >= 1 and s.shape == (len(cs.t),) and np.isfinite(s).all()

def test_template_prior_counts():
    cs, pos, _ = space("Fe-Na-O-P"); c = pos.cand_idx.values; tp = template_prior(cs, c)
    assert tp[c].max() >= 1 and np.isfinite(tp).all()

def test_qc_results_pass():
    p = os.path.join(HERE, "results", "dataset_qc.json")
    if not os.path.exists(p): pytest.skip("run scripts/dataset_qc.py first")
    chk = json.load(open(p))["checks"]; assert all(v for k, v in chk.items() if isinstance(v, bool))
