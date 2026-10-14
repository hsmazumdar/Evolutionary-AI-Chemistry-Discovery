"""Shared Stage-1 utilities: data loading, splits, reliability, statistics, provenance.
V03 code in ../evochem is imported read-only and never modified."""
import os, sys, json, hashlib, platform, subprocess, copy
import numpy as np, pandas as pd

V04 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(V04)
sys.path.insert(0, ROOT)
from evochem.features import load_elements, parse_comp, featurize  # noqa: E402
from evochem.gp import GP  # noqa: E402

DATA = os.path.join(ROOT, "data")
SPLITDIR = os.path.join(DATA, "splits_Fe-Na-O-P")

def sha256(path):
    h = hashlib.sha256(); h.update(open(path, "rb").read()); return h.hexdigest()

def load_poc():
    el = load_elements(os.path.join(DATA, "elements_118.csv"))
    df = pd.read_csv(os.path.join(DATA, "poc_Fe-Na-O-P_expt_formulas.csv")).sort_values("idx").reset_index(drop=True)
    comps = [parse_comp(c) for c in df.composition_reduced]
    X, names = featurize(comps, el)
    Xo, names_o = featurize(comps, el, use_oxidation=True)
    y = df.formation_energy_per_atom_eV.values.astype(float)  # DFT-COMPUTED (MP), NOT measured
    return dict(df=df, el=el, comps=comps, X=X, names=names, Xo=Xo, names_o=names_o, y=y)

def reliability(df):
    """Evidence reliability in [0,1] of the claim 'this formula exists experimentally'.
    Several ICSD records of the same structure are NOT independent confirmations: each distinct observed
    polymorph counts 1, extra records of already-counted structures only add 0.25*log(1+extra)."""
    npoly = df.n_polymorphs_observed.clip(lower=1).values.astype(float)
    extra = np.clip(df.n_icsd.values.astype(float) - npoly, 0, None)
    neff = npoly + 0.25 * np.log1p(extra)
    return 1.0 - np.exp(-neff / 1.5)

def group_kfold_splits(df, k=5, seed=0):
    """V04-only extra group-held-out folds: whole stoichiometry families (formula_anonymous) held out."""
    fam = df.formula_anonymous.values; u = np.array(sorted(set(fam)))
    rng = np.random.default_rng(seed); rng.shuffle(u)
    out = {}
    for f in range(k):
        held = set(u[f::k]); te = [i for i in range(len(df)) if fam[i] in held]
        out[f"groupfold{f}"] = {"train": [i for i in range(len(df)) if fam[i] not in held], "test": te}
    return out

def load_splits(df, include_groupfolds=True):
    sp = {}
    for s in range(10):
        sp[f"random_split_seed{s}"] = json.load(open(os.path.join(SPLITDIR, f"random_split_seed{s}.json")))
    sp["family_heldout"] = json.load(open(os.path.join(SPLITDIR, "group_heldout_stoichiometry_family.json")))
    if include_groupfolds: sp.update(group_kfold_splits(df))
    return {k: {"train": np.array(v["train"]), "test": np.array(v["test"])} for k, v in sp.items()}

def inner_split(train, seed, frac=0.25):
    rng = np.random.default_rng(10_000 + seed); p = rng.permutation(train); nv = max(3, int(round(frac * len(train))))
    return np.sort(p[nv:]), np.sort(p[:nv])

def mae(a, b): return float(np.mean(np.abs(np.asarray(a, float) - np.asarray(b, float)))) if len(a) else float("nan")

def boot_ci(x, n=5000, seed=0, alpha=0.05):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    if len(x) == 0: return (float("nan"),) * 3
    rng = np.random.default_rng(seed); m = rng.choice(x, (n, len(x))).mean(1)
    return float(x.mean()), float(np.quantile(m, alpha / 2)), float(np.quantile(m, 1 - alpha / 2))

def paired(a, b):
    """a,b paired per-run errors. Returns mean diff (a-b), 95% bootstrap CI, Wilcoxon p, Cohen dz, wins of a."""
    from scipy.stats import wilcoxon
    a, b = np.asarray(a, float), np.asarray(b, float); d = a - b; d = d[~np.isnan(d)]
    m, lo, hi = boot_ci(d)
    try: p = float(wilcoxon(d).pvalue) if np.any(d != 0) else 1.0
    except ValueError: p = float("nan")
    dz = float(d.mean() / d.std(ddof=1)) if len(d) > 1 and d.std(ddof=1) > 0 else 0.0
    return dict(mean_diff=m, ci_lo=lo, ci_hi=hi, wilcoxon_p=p, cohen_dz=dz, n=int(len(d)), a_better=int((d < 0).sum()), b_better=int((d > 0).sum()))

def holm(ps):
    ps = np.asarray(ps, float); o = np.argsort(ps); adj = np.empty_like(ps); run = 0.0
    for r, i in enumerate(o):
        run = max(run, min(1.0, (len(ps) - r) * ps[i])); adj[i] = run
    return adj

def provenance(extra_files=()):
    def ver(m):
        try: return __import__(m).__version__
        except Exception: return None
    try: commit = subprocess.check_output(["git", "-C", ROOT, "rev-parse", "HEAD"], text=True).strip()
    except Exception: commit = None
    try: dirty = bool(subprocess.check_output(["git", "-C", ROOT, "status", "--porcelain"], text=True).strip())
    except Exception: dirty = None
    files = [os.path.join(DATA, "poc_Fe-Na-O-P_expt_formulas.csv"), os.path.join(DATA, "elements_118.csv")] + \
            sorted(os.path.join(SPLITDIR, f) for f in os.listdir(SPLITDIR)) + list(extra_files)
    return {"python": sys.version.split()[0], "platform": platform.platform(), "cpu_count": os.cpu_count(),
            "packages": {m: ver(m) for m in ["numpy", "pandas", "scipy", "sklearn", "matplotlib", "yaml"]},
            "git_commit": commit, "git_dirty": dirty,
            "dataset_sha256": {os.path.relpath(f, ROOT): sha256(f) for f in files}}

def write_yaml(path, d):
    try:
        import yaml; open(path, "w").write(yaml.safe_dump(d, sort_keys=False))
    except ImportError:
        open(path, "w").write(json.dumps(d, indent=2))

import re as _re
def parse_formula(f):
    """Simple formula parser for MP reduced formulas (supports one level of parentheses and decimals)."""
    f = str(f).replace(" ", "")
    while "(" in f:
        f = _re.sub(r"\(([^()]*)\)([\d.]*)", lambda m: "".join(f"{e}{float(n or 1) * float(m.group(2) or 1):g}" for e, n in _re.findall(r"([A-Z][a-z]?)([\d.]*)", m.group(1))), f)
    d = {}
    for e, n in _re.findall(r"([A-Z][a-z]?)([\d.]*)", f): d[e] = d.get(e, 0.0) + float(n or 1)
    return d

def load_mp_subset():
    m = pd.read_csv(os.path.join(DATA, "mp_expt_observed_subset.csv.gz"))
    m["elset"] = m.elements.str.split().apply(frozenset)
    return m

def system_table(m, elements):
    """All experimentally observed MP compounds within an element system; one row per reduced formula (lowest DFT Ef)."""
    s = frozenset(elements); g = m[m.elset.apply(lambda e: e <= s)].copy()
    g["comp"] = g.formula.apply(parse_formula)
    g["key"] = g.comp.apply(lambda c: tuple(sorted((k, round(v / sum(c.values()), 4)) for k, v in c.items())))
    return g.sort_values("formation_energy_per_atom_eV").drop_duplicates("key").reset_index(drop=True)
