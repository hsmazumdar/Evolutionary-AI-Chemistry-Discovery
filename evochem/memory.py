"""Associative / evolutionary knowledge memory: every rule the system adopts is stored with its evidence,
confidence, limits of validity, contradictions and revision history. Nothing is ever marked 'final'."""
import json, datetime
import numpy as np

class KnowledgeMemory:
    def __init__(self, context):
        self.data = {"context": context, "created": datetime.datetime.now().isoformat(timespec="seconds"),
                     "principle": "No rule is permanent; every rule can be revised when evidence demands.",
                     "rules": [], "revision_history": []}
        self._current = None

    def consider(self, gen, rule_str, size, train_mae, n_train, phase, reason):
        if self._current is not None and self.data["rules"][self._current]["rule"] == rule_str:
            return
        rid = len(self.data["rules"])
        rule = {"id": f"R{rid:03d}", "rule": rule_str, "adopted_generation": gen, "phase": phase,
                "complexity_nodes": size, "status": "active",
                "evidence": {"n_training_compounds": n_train, "train_MAE_eV_per_atom": round(train_mae, 4)},
                "confidence": None, "limits": None, "contradictions": []}
        if self._current is not None:
            old = self.data["rules"][self._current]; old["status"] = "superseded"
            old["superseded_by"] = rule["id"]; old["superseded_at_generation"] = gen
            self.data["revision_history"].append({"generation": gen, "from": old["id"], "to": rule["id"],
                "reason": reason, "train_MAE_before": old["evidence"]["train_MAE_eV_per_atom"],
                "train_MAE_after": round(train_mae, 4)})
        self.data["rules"].append(rule); self._current = rid

    def annotate_current(self, confidence=None, limits=None, contradictions=None, extra=None):
        r = self.data["rules"][self._current]
        if confidence is not None: r["confidence"] = confidence
        if limits is not None: r["limits"] = limits
        if contradictions is not None: r["contradictions"] = contradictions
        if extra: r.update(extra)

    def save(self, json_path, md_path):
        with open(json_path, "w", encoding="utf-8") as f: json.dump(self.data, f, indent=2)
        d = self.data; L = [f"# Knowledge memory: {d['context']}", "", f"_{d['principle']}_", "",
             f"{len(d['rules'])} rules adopted, {len(d['revision_history'])} revisions.", "",
             "| id | gen | phase | status | nodes | train MAE | rule |", "|---|---|---|---|---|---|---|"]
        for r in d["rules"]:
            L.append(f"| {r['id']} | {r['adopted_generation']} | {r['phase']} | {r['status']} | {r['complexity_nodes']} | "
                     f"{r['evidence']['train_MAE_eV_per_atom']} | `{r['rule']}` |")
        final = [r for r in d["rules"] if r["status"] == "active"]
        if final:
            r = final[-1]; L += ["", f"## Current active rule {r['id']}", "", f"`{r['rule']}`", "",
                 f"- Evidence: {r['evidence']}", f"- Confidence: {r['confidence']}", f"- Limits: {r['limits']}",
                 "- Contradictions (reliable training compounds this rule mispredicts badly):"]
            for c in r["contradictions"]:
                L.append(f"  - {c['formula']}: DFT {c['Ef_DFT']:+.3f}, rule {c['Ef_rule']:+.3f} eV/atom (ICSD entries: {c['n_icsd']})")
        L += ["", "## Revision history", ""]
        for h in d["revision_history"]:
            L.append(f"- gen {h['generation']}: {h['from']} -> {h['to']} ({h['reason']}; train MAE {h['train_MAE_before']} -> {h['train_MAE_after']})")
        open(md_path, "w", encoding="utf-8").write("\n".join(L) + "\n")
