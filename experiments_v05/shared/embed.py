"""Element co-occurrence embedding (V03 PPMI-SVD) built WITHOUT any compound inside the target system."""
import os, numpy as np, pandas as pd
from functools import lru_cache
from .core import ROOT, featurize
import sys; sys.path.insert(0, ROOT); from evochem import periodicity

@lru_cache(None)
def _mp():
    return pd.read_csv(os.path.join(ROOT, "data", "mp_expt_observed_subset.csv.gz"))

@lru_cache(None)
def embedding(system):
    vocab, embs, n = periodicity.element_embeddings(_mp(), set(system.split("-")), dim=12)
    return vocab, embs["co-occurrence (PPMI-SVD)"]

def emb_features(cs, system):
    vocab, E = embedding(system); ix = {e: i for i, e in enumerate(vocab)}
    V = np.array([E[ix[e]] if e in ix else np.zeros(E.shape[1]) for e in cs.EL])   # (4, d)
    T = np.array(cs.t, float); W = T / T.sum(1, keepdims=True); M = W @ V
    D = np.einsum("ne,ned->nd", W, np.abs(V[None, :, :] - M[:, None, :]))
    return np.hstack([M, D])
