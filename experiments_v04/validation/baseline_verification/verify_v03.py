"""Stage-1 step (a): re-run the unchanged V03 benchmark in a clean git worktree of the V03 commit and compare
every output with the committed results/. Usage: python verify_v03.py [--rerun-dir DIR]"""
import argparse, os, sys, glob, subprocess, json, filecmp
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from shared.common import ROOT, provenance
ap = argparse.ArgumentParser(); ap.add_argument("--rerun-dir", default=None); ap.add_argument("--commit", default="a3b1daa"); a = ap.parse_args()
OUT = os.path.dirname(os.path.abspath(__file__))
d = a.rerun_dir
if d is None:
    d = os.path.join("/tmp", "v03_verify"); subprocess.run(["git", "-C", ROOT, "worktree", "add", "-f", d, a.commit], check=False)
    subprocess.run([sys.executable, "run_demo.py"], cwd=d, check=True)
rows = []
for f in sorted(glob.glob(os.path.join(ROOT, "results", "*"))):
    b = os.path.basename(f); g = os.path.join(d, "results", b)
    if filecmp.cmp(f, g, shallow=False): rows.append((b, "byte-identical", 0.0)); continue
    if b.endswith(".csv"):
        A, B = pd.read_csv(f), pd.read_csv(g); num = A.select_dtypes("number").columns
        md = float(np.nanmax(np.abs(A[num].values - B[num].values))); same_txt = A.drop(columns=num).equals(B.drop(columns=num))
        rows.append((b, f"numeric max |diff| = {md:.2e}; text columns identical = {same_txt}", md))
    elif b.endswith(".json"):
        A, B = json.load(open(f)), json.load(open(g)); A.pop("created", None); B.pop("created", None)
        rows.append((b, "identical except 'created' timestamp" if A == B else "CONTENT DIFFERS", 0.0 if A == B else 1.0))
    else:
        la, lb = open(f, encoding="utf-8").read().splitlines(), open(g, encoding="utf-8").read().splitlines()
        dl = [(x, y) for x, y in zip(la, lb) if x != y]
        rows.append((b, "differs only in lines: " + " | ".join(f"{x!r} vs {y!r}" for x, y in dl), 0.0 if all(x.startswith("Runtime") for x, _ in dl) else 1.0))
L = ["# V03 baseline verification (Stage 1, step a)", "", f"Re-run of unchanged V03 code (commit {a.commit}) in a clean worktree; compared with committed `results/`.", "",
     "| file | result |", "|---|---|"] + [f"| {b} | {r} |" for b, r, _ in rows]
bad = [b for b, _, s in rows if s > 1e-9]
L += ["", "**Verdict:** " + ("all V03 numbers reproduced (differences only in runtime/timestamps and floating-point round-off <= 1e-12)." if all(s < 1e-12 for *_, s in rows) else f"discrepancies in: {bad}")]
L += ["", "Provenance:", "```json", json.dumps(provenance(), indent=1), "```"]
open(os.path.join(OUT, "v03_reproduction.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L[:20]))
