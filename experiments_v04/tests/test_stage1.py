import os, sys, json, subprocess, hashlib
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.common import load_poc, load_splits, reliability, inner_split, paired, holm, ROOT, GP
from shared.twopop import fit_two_population, predict_two_population
from shared.memory_v04 import HypothesisMemory

P = load_poc(); SPL = load_splits(P["df"])

def test_v03_files_unchanged_vs_v03_commit():
    out = subprocess.run(["git", "-C", ROOT, "diff", "--name-only", "a3b1daa", "--", "evochem", "data", "results", "run_demo.py", "gui.py"], capture_output=True, text=True).stdout
    assert out.strip() == "", out

def test_splits_disjoint_and_cover():
    for k, s in SPL.items():
        assert not set(s["train"]) & set(s["test"]), k

def test_groupfolds_hold_out_whole_families():
    fam = P["df"].formula_anonymous.values
    for k, s in SPL.items():
        if k.startswith("groupfold"): assert not set(fam[s["train"]]) & set(fam[s["test"]])

def test_reliability_sublinear_in_duplicate_records():
    import pandas as pd
    d = pd.DataFrame(dict(n_polymorphs_observed=[1, 1, 2], n_icsd=[1, 10, 2])); r = reliability(d)
    assert r[0] < r[1] < 1 and r[2] > r[1]  # 10 records of 1 structure < 2 independent structures

def test_inner_split_inside_train():
    tr = SPL["random_split_seed0"]["train"]; f, v = inner_split(tr, 0)
    assert set(f) | set(v) == set(tr) and not set(f) & set(v)

def test_two_population_never_sees_test_labels():
    cfg = dict(pop=30, gens_G=3, gens_S=2, inner_val_frac=0.25, archive_k=5, contradiction_frac=0.15, min_contradictions=4, gate_depth=2, gate_min_leaf=2, accept_margin=0.005)
    s = SPL["random_split_seed0"]; y2 = P["y"].copy(); y2[s["test"]] = 1e6   # poison test labels
    rel = reliability(P["df"])
    m1, i1, _ = fit_two_population(P["X"], P["Xo"], P["y"], rel, s["train"], 0, cfg, P["names"], P["names_o"])
    m2, i2, _ = fit_two_population(P["X"], P["Xo"], y2, rel, s["train"], 0, cfg, P["names"], P["names_o"])
    assert i1["G_rule"] == i2["G_rule"] and i1["accepted"] == i2["accepted"]

def test_paired_and_holm():
    r = paired([1, 2, 3, 4.0], [2, 3, 4, 5.0]); assert r["mean_diff"] == -1 and r["a_better"] == 4
    assert list(holm([0.01, 0.04])) == [0.02, 0.04]

def test_memory_versions_and_retirement():
    g = GP(P["names"], pop_size=30, generations=2, seed=0).fit(P["X"], P["y"]); hm = HypothesisMemory()
    hm.update(g, [(t, (0.0, 1.0)) for t in g.pop[:8]], P["X"], P["y"], 0)
    assert len([h for h in hm.h if h["status"] == "active"]) <= hm.max_active
    mu, sd = hm.predict(g, P["X"], return_std=True); assert np.all(sd > 0) and mu.shape == P["y"].shape
