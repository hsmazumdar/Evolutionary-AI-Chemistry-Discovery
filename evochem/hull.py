"""Convex hull of formation energy built from TRAINING compounds only (plus elemental references at 0 eV,
which is the definition of formation energy, not data leakage)."""
import numpy as np
from scipy.spatial import ConvexHull

def comp_vec(comp, elements):
    v = np.array([comp.get(e, 0.0) for e in elements], float); return v / v.sum()

class TrainingHull:
    def __init__(self, comps, energies, elements):
        self.el = elements
        X = [comp_vec(c, elements) for c in comps] + list(np.eye(len(elements)))
        E = list(energies) + [0.0] * len(elements)
        P = np.column_stack([np.array(X)[:, 1:], E])  # drop first fraction (sum=1)
        top = np.column_stack([np.eye(len(elements))[:, 1:], np.full(len(elements), 50.0)])  # closes the hull from above
        P = np.vstack([P, top])
        h = ConvexHull(P, qhull_options="QJ")
        eq = h.equations[h.equations[:, -2] < -1e-9]  # lower facets: normal points to -E
        # plane: n.x + n_E*E + d = 0 -> E = -(n.x + d)/n_E
        self.A = -eq[:, :-2] / eq[:, -2:-1]; self.b = -eq[:, -1] / eq[:, -2]

    def hull_energy(self, fracs):
        F = np.atleast_2d(fracs)[:, 1:]
        return (F @ self.A.T + self.b).max(axis=1)
