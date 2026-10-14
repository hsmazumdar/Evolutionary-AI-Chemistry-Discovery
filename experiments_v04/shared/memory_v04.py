"""V04 versioned competing-hypothesis memory. A NEW module (V03 evochem/memory.py is untouched so V03 outputs
remain byte-reproducible). Every hypothesis keeps versions (re-fitted coefficients), evidence, confidence,
status (active / retired) and a revision log. Several hypotheses compete; none is final."""
import json
import numpy as np

class HypothesisMemory:
    def __init__(self, max_active=5, retire_ratio=1.5, revise_tol=0.02, top_ensemble=3):
        self.h = []; self.log = []; self.max_active, self.retire_ratio, self.revise_tol, self.top = max_active, retire_ratio, revise_tol, top_ensemble

    def _active(self): return [h for h in self.h if h["status"] == "active"]

    def update(self, gp, candidates, X, y, episode):
        """candidates: list of (tree, scale). X,y: evidence available now (replay buffer + new episode)."""
        n_rev = n_ret = n_new = 0
        for h in self._active():                      # 1) revise existing hypotheses against new evidence
            a, b = gp._scale(gp._eval(h["tree"], X), y, np.ones(len(y)))
            m = float(np.mean(np.abs(y - (a + b * gp._eval(h["tree"], X)))))
            old = h["versions"][-1]
            if abs(a - old["a"]) + abs(b - old["b"]) > self.revise_tol:
                h["versions"].append(dict(episode=episode, a=float(a), b=float(b), mae=m)); n_rev += 1
                self.log.append(dict(episode=episode, id=h["id"], event="revised", mae_before=old["mae"], mae_after=m))
            else: h["versions"][-1]["mae"] = m
        known = {h["str"] for h in self.h}
        for t, sc in candidates:                      # 2) admit new competing hypotheses
            s = gp.to_str(t, sc)
            if s in known: continue
            a, b = gp._scale(gp._eval(t, X), y, np.ones(len(y))); m = float(np.mean(np.abs(y - (a + b * gp._eval(t, X)))))
            self.h.append(dict(id=f"H{len(self.h):03d}", str=s, tree=t, nodes=len(t), status="active", born=episode,
                               versions=[dict(episode=episode, a=float(a), b=float(b), mae=m)])); n_new += 1; known.add(s)
        act = sorted(self._active(), key=lambda h: h["versions"][-1]["mae"])
        best = act[0]["versions"][-1]["mae"]
        for i, h in enumerate(act):                   # 3) retire dominated hypotheses (kept in memory, status changed)
            if i >= self.max_active or h["versions"][-1]["mae"] > self.retire_ratio * best:
                h["status"] = "retired"; h["retired_episode"] = episode; n_ret += 1
                self.log.append(dict(episode=episode, id=h["id"], event="retired", mae=h["versions"][-1]["mae"]))
        tau = max(1e-3, float(np.median([h["versions"][-1]["mae"] for h in self._active()])))
        for h in self._active(): h["confidence"] = float(np.exp(-h["versions"][-1]["mae"] / tau))
        z = sum(h["confidence"] for h in self._active())
        for h in self._active(): h["confidence"] /= z
        self.resid_scale = best
        return dict(revised=n_rev, retired=n_ret, new=n_new, active=len(self._active()))

    def predict(self, gp, X, return_std=False):
        act = sorted(self._active(), key=lambda h: -h["confidence"])[: self.top]
        w = np.array([h["confidence"] for h in act]); w = w / w.sum()
        P = np.array([h["versions"][-1]["a"] + h["versions"][-1]["b"] * gp._eval(h["tree"], X) for h in act])
        mu = w @ P
        if not return_std: return mu
        sd = np.sqrt(w @ (P - mu) ** 2 + (1.25 * self.resid_scale) ** 2)
        return mu, sd

    def to_json(self):
        return dict(hypotheses=[{k: v for k, v in h.items() if k != "tree"} for h in self.h], revision_log=self.log)
