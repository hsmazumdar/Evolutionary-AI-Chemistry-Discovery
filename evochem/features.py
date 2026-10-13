"""Feature layer built ONLY from element attributes (no oxidation states unless explicitly asked)."""
import json, re
import numpy as np
import pandas as pd

ATTRS = {  # column -> (short name, scale divisor to keep values O(1))
    "electronegativity_pauling": ("EN", 1.0),
    "atomic_radius_pm": ("rA", 100.0),          # Angstrom
    "covalent_radius_pm": ("rCov", 100.0),      # Angstrom
    "first_ionization_energy_eV": ("IE", 10.0), # 10 eV units
    "atomic_mass": ("mass", 100.0),             # 100 amu units
    "density_g_cm3": ("rho", 10.0),             # 10 g/cm3 units
    "n_valence": ("nval", 10.0),                # outer-shell electrons / 10
}

def _n_valence(cfg: str) -> int:
    """Electrons outside the noble-gas core, parsed from the electron configuration string."""
    cfg = re.sub(r"\[[A-Za-z]+\]", "", str(cfg))
    return sum(int(m.group(2) or 1) for m in re.finditer(r"\d([spdf])(\d*)", cfg))

def load_elements(path):
    el = pd.read_csv(path)
    el["n_valence"] = el["electron_configuration"].map(_n_valence)
    return el.set_index("symbol")

def parse_comp(s):
    d = json.loads(s) if isinstance(s, str) else dict(s)
    return {k: float(v) for k, v in d.items()}

def oxidation_states(el, sym):
    v = el.loc[sym, "common_oxidation_states"]
    return [int(x) for x in str(v).split()] if isinstance(v, str) and v.strip() else []

def charge_balance_features(comp, el):
    """ABLATION ONLY: uses tabulated common oxidation states (chemical prior knowledge).
    Returns (balanced 0/1, min |net charge| per atom) with every element in one oxidation state."""
    import itertools
    syms = list(comp)
    if len(syms) == 1:
        return 1.0, 0.0
    opts = [oxidation_states(el, s) or [0] for s in syms]
    n = np.array([comp[s] for s in syms])
    best = min(abs(float(np.dot(n, c))) for c in itertools.product(*opts))
    return float(best < 1e-6), best / n.sum()

def featurize(comps, el, use_oxidation=False):
    """Composition-weighted mean, weighted mean-absolute-deviation and range of each attribute (vectorised)."""
    import itertools
    syms = sorted({s for c in comps for s in c})
    F = np.array([[c.get(s, 0.0) for s in syms] for c in comps], float)
    N = F.copy(); F = F / F.sum(1, keepdims=True); present = F > 0
    cols, names = [], []
    for col, (short, sc) in ATTRS.items():
        v = el.loc[syms, col].astype(float).values / sc
        m = F @ v
        cols += [m, (F * np.abs(v[None, :] - m[:, None])).sum(1),
                 np.where(present, v, -np.inf).max(1) - np.where(present, v, np.inf).min(1)]
        names += [f"mean_{short}", f"dev_{short}", f"range_{short}"]
    cols.append(present.sum(1).astype(float)); names.append("n_elem")
    if use_oxidation:  # ABLATION ONLY: tabulated common oxidation states = chemical prior knowledge
        opts = [oxidation_states(el, s) or [0] for s in syms]
        best = np.full(len(comps), np.inf)
        for combo in itertools.product(*opts):
            best = np.minimum(best, np.abs(N @ np.array(combo, float)))
        best[present.sum(1) == 1] = 0.0
        cols += [(best < 1e-6).astype(float), best / N.sum(1)]; names += ["charge_balanced", "charge_imbalance"]
    return np.column_stack(cols), names
