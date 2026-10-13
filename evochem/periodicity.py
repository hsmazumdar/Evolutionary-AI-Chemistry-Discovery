"""Periodicity teaser: learn element embeddings ONLY from how elements behave in compounds
(who they co-occur with and the formation energies of those compounds). No group/period input."""
import json, itertools
import numpy as np, pandas as pd
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import adjusted_rand_score
from sklearn.decomposition import PCA

def iupac_group(Z):
    if 57 <= Z <= 71: return "Ln"
    if 89 <= Z <= 103: return "An"
    if Z == 1: return "1"
    if Z == 2: return "18"
    starts = [(3, 2), (11, 2), (19, 0), (37, 0), (55, 0), (87, 0)]
    for s, _ in starts[::-1]:
        if Z >= s: off = Z - s; break
    if s in (3, 11):
        return str(off + 1) if off < 2 else str(off + 11)
    if s in (55, 87):
        if off < 2: return str(off + 1)
        off -= 14  # skip f-block
        return str(off + 1)
    return str(off + 1)

def element_embeddings(mp, exclude_subset_of, min_count=40, dim=12):
    mp = mp[mp.experimentally_observed.astype(str) == "True"]
    ex = set(exclude_subset_of)
    els = mp.elements.str.split()
    keep = ~els.map(lambda e: set(e) <= ex)
    mp, els = mp[keep], els[keep]
    counts = pd.Series([e for es in els for e in es]).value_counts()
    vocab = sorted(counts[counts >= min_count].index)
    ix = {e: i for i, e in enumerate(vocab)}; n = len(vocab)
    C = np.zeros((n, n)); S = np.zeros((n, n))
    for es, ef in zip(els, mp.formation_energy_per_atom_eV.values):
        es = [e for e in es if e in ix]
        for a, b in itertools.permutations(es, 2):
            C[ix[a], ix[b]] += 1; S[ix[a], ix[b]] += ef
    tot = C.sum(); pr = C.sum(1, keepdims=True) / tot
    with np.errstate(divide="ignore", invalid="ignore"):
        ppmi = np.maximum(np.log((C / tot) / (pr @ pr.T)), 0); ppmi = np.nan_to_num(ppmi)
        meanE = np.where(C > 0, S / np.maximum(C, 1), 0.0)
    U, s, _ = np.linalg.svd(ppmi); emb_co = U[:, :dim] * np.sqrt(s[:dim])
    U2, s2, _ = np.linalg.svd(meanE - meanE.mean(0)); emb_E = U2[:, :dim] * s2[:dim]
    z = lambda A: (A - A.mean(0)) / (A.std(0) + 1e-9)
    return vocab, {"co-occurrence (PPMI-SVD)": emb_co, "partner formation energy (SVD)": emb_E,
                   "combined": np.hstack([z(emb_co), z(emb_E)])}, len(mp)

def evaluate(vocab, embs, Zof, n_null=1000, seed=0):
    labels = [iupac_group(Zof[e]) for e in vocab]
    k = len(set(labels)); rng = np.random.default_rng(seed); out = {}
    for name, E in embs.items():
        En = E / (np.linalg.norm(E, axis=1, keepdims=True) + 1e-12)
        cl = AgglomerativeClustering(n_clusters=k, linkage="average", metric="cosine").fit_predict(En)
        ari = adjusted_rand_score(labels, cl)
        null = np.array([adjusted_rand_score(rng.permutation(labels), cl) for _ in range(n_null)])
        sim = En @ En.T; np.fill_diagonal(sim, -9); nn = sim.argmax(1)
        lab = np.array(labels); nn_same = float((lab[nn] == lab).mean())
        nn_null = float(np.mean([(p[nn] == p).mean() for p in (rng.permutation(lab) for _ in range(n_null))]))
        out[name] = {"ARI": float(ari), "ARI_null_mean": float(null.mean()), "ARI_null_p95": float(np.percentile(null, 95)),
                     "p_value": float((null >= ari).mean()), "nn_same_group": nn_same, "nn_same_group_null": nn_null,
                     "clusters": cl.tolist(), "nearest_neighbour": [vocab[j] for j in nn]}
    return labels, k, out
