#!/usr/bin/env python3
"""EvolutionaryChemistry demo GUI (Tkinter + embedded matplotlib). Launch with Launch_Demo.bat on Windows
or `python gui.py` anywhere. Every number shown is computed live from the data in ./data."""
import os, sys, json, glob, copy, threading, queue, subprocess, itertools
from math import gcd
from functools import reduce
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from sklearn.linear_model import RidgeCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from evochem.features import load_elements, parse_comp, featurize
from evochem.gp import GP
from evochem.hull import TrainingHull, comp_vec
from evochem.memory import KnowledgeMemory
from evochem import periodicity
from evochem.discovery import CandidateSpace, base_score, hits, analogy_mask

D, R = os.path.join(HERE, "data"), os.path.join(HERE, "results"); os.makedirs(R, exist_ok=True)
EL, MAXTOT, KS = ["Fe", "Na", "O", "P"], 30, [10, 25, 50, 100, 200, 500, 1000]
mae = lambda a, b: float(np.mean(np.abs(np.asarray(a) - np.asarray(b))))

class Data:
    def __init__(self):
        self.el = load_elements(os.path.join(D, "elements_118.csv"))
        self.df = pd.read_csv(os.path.join(D, "poc_Fe-Na-O-P_expt_formulas.csv")).sort_values("idx").reset_index(drop=True)
        self.comps = [parse_comp(c) for c in self.df.composition_reduced]; self.y = self.df.formation_energy_per_atom_eV.values
        self.X, self.fn = featurize(self.comps, self.el); self.Xo, self.fno = featurize(self.comps, self.el, True)
        self.splits = {}
        for f in sorted(glob.glob(os.path.join(D, "splits_Fe-Na-O-P", "*.json"))):
            self.splits[os.path.basename(f)[:-5]] = json.load(open(f))
        self.cands = None

    def candidates(self):
        if self.cands is None: self.cands = CandidateSpace(EL, self.el, MAXTOT)
        return self.cands

AUTHOR = "Conceived and directed by Himanshu Mazumdar, R&D Centre, Dharmsinh Desai University"
AI_NOTE = "Code developed with AI assistance"
PAL = dict(bg="#F4F7FB", panel="#E8F0FA", banner="#D6E6F5", btn="#DDEBF7", btn_hover="#C5DDF2", stage="#E3F4E8",
           stage_hover="#CBEBD5", warm="#FCEBD9", warm_hover="#F8D9B8", help="#EEE3F7", help_hover="#DECBF0", text="#1F2D3D")
UI = ("Segoe UI", 10) if sys.platform.startswith("win") else ("DejaVu Sans", 10)
MONO = ("Consolas", 10) if sys.platform.startswith("win") else ("DejaVu Sans Mono", 10)

class ScrollArea(ttk.Frame):
    """Frame with horizontal + vertical scrollbars; put content in .inner (shown at native size)."""
    def __init__(self, master):
        super().__init__(master, style="Panel.TFrame")
        self.cv = tk.Canvas(self, bg="white", highlightthickness=0)
        vs = ttk.Scrollbar(self, orient="vertical", command=self.cv.yview); hs = ttk.Scrollbar(self, orient="horizontal", command=self.cv.xview)
        self.cv.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        self.cv.grid(row=0, column=0, sticky="nsew"); vs.grid(row=0, column=1, sticky="ns"); hs.grid(row=1, column=0, sticky="ew")
        self.rowconfigure(0, weight=1); self.columnconfigure(0, weight=1)
        self.inner = tk.Frame(self.cv, bg="white"); self.cv.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self.cv.configure(scrollregion=self.cv.bbox("all")))
        for w in (self.cv, self.inner):
            w.bind("<Enter>", lambda e: self._wheel(True)); w.bind("<Leave>", lambda e: self._wheel(False))
    def _wheel(self, on):
        if on:
            self.cv.bind_all("<MouseWheel>", lambda e: self.cv.yview_scroll(int(-e.delta / 120), "units"))
            self.cv.bind_all("<Shift-MouseWheel>", lambda e: self.cv.xview_scroll(int(-e.delta / 120), "units"))
            self.cv.bind_all("<Button-4>", lambda e: self.cv.yview_scroll(-1, "units")); self.cv.bind_all("<Button-5>", lambda e: self.cv.yview_scroll(1, "units"))
        else:
            for k in ("<MouseWheel>", "<Shift-MouseWheel>", "<Button-4>", "<Button-5>"): self.cv.unbind_all(k)

def scroll_text(master, font):
    f = ttk.Frame(master, style="Panel.TFrame")
    t = tk.Text(f, wrap="none", font=font, bg="white", fg=PAL["text"], relief="flat", padx=8, pady=6)
    vs = ttk.Scrollbar(f, orient="vertical", command=t.yview); hs = ttk.Scrollbar(f, orient="horizontal", command=t.xview)
    t.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
    t.grid(row=0, column=0, sticky="nsew"); vs.grid(row=0, column=1, sticky="ns"); hs.grid(row=1, column=0, sticky="ew")
    f.rowconfigure(0, weight=1); f.columnconfigure(0, weight=1); return f, t

def style_app(root):
    st = ttk.Style(root)
    try: st.theme_use("clam")
    except tk.TclError: pass
    root.configure(bg=PAL["bg"])
    st.configure(".", font=UI, background=PAL["bg"], foreground=PAL["text"])
    st.configure("Panel.TFrame", background=PAL["panel"]); st.configure("Banner.TFrame", background=PAL["banner"])
    st.configure("Panel.TLabel", background=PAL["panel"]); st.configure("Head.TLabel", background=PAL["panel"], font=(UI[0], 10, "bold"))
    st.configure("Banner.TLabel", background=PAL["banner"], font=(UI[0], 14, "bold"), foreground="#163A5F")
    st.configure("Author.TLabel", background=PAL["banner"], font=(UI[0], 10, "italic"), foreground="#35506B")
    st.configure("Status.TLabel", background=PAL["panel"], foreground="#0B6B3A"); st.configure("Note.TLabel", background=PAL["panel"], foreground="#5A6470")
    st.configure("Panel.TCheckbutton", background=PAL["panel"]); st.map("Panel.TCheckbutton", background=[("active", PAL["panel"])])
    for name, k in [("TButton", "btn"), ("Stage.TButton", "stage"), ("Warm.TButton", "warm"), ("Help.TButton", "help")]:
        st.configure(name, background=PAL[k], foreground=PAL["text"], padding=(8, 5), borderwidth=1, relief="flat", font=UI)
        st.map(name, background=[("pressed", PAL[k + "_hover"]), ("active", PAL[k + "_hover"])])
    st.configure("TNotebook", background=PAL["bg"]); st.configure("TNotebook.Tab", padding=(12, 5), background=PAL["btn"])
    st.map("TNotebook.Tab", background=[("selected", "white"), ("active", PAL["btn_hover"])])

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title("Evolutionary Chemistry Demo - concept: Himanshu Mazumdar")
        self.geometry("1320x840"); self.q = queue.Queue(); self.busy = False; self.state = {}
        style_app(self); self.status = tk.StringVar(value="Loading data ...")
        ban = ttk.Frame(self, style="Banner.TFrame", padding=(12, 8)); ban.pack(side="top", fill="x")
        tb = ttk.Frame(ban, style="Banner.TFrame"); tb.pack(side="left", fill="x", expand=True)
        ttk.Label(tb, text="EvolutionaryChemistry: evolutionary knowledge discovery on real inorganic data (Fe-Na-O-P)", style="Banner.TLabel").pack(anchor="w")
        ttk.Label(tb, text=AUTHOR, style="Author.TLabel").pack(anchor="w")
        ttk.Label(tb, text=AI_NOTE, style="Author.TLabel").pack(anchor="w")
        ttk.Button(ban, text="Help", style="Help.TButton", command=self.open_help).pack(side="right")
        left = ttk.Frame(self, padding=10, style="Panel.TFrame"); left.pack(side="left", fill="y")
        ttk.Label(left, text="Experiment / split", style="Head.TLabel").pack(anchor="w")
        self.split = tk.StringVar(); self.cb = ttk.Combobox(left, textvariable=self.split, width=34, state="readonly"); self.cb.pack(anchor="w")
        self.pop, self.gens = tk.IntVar(value=300), tk.IntVar(value=40)
        for lab, var, lo, hi in [("GP population", self.pop, 50, 2000), ("generations", self.gens, 5, 500)]:
            f = ttk.Frame(left, style="Panel.TFrame"); f.pack(anchor="w", pady=2); ttk.Label(f, text=lab, width=14, style="Panel.TLabel").pack(side="left")
            ttk.Spinbox(f, from_=lo, to=hi, textvariable=var, width=7).pack(side="left")
        self.ox = tk.BooleanVar(value=False)
        ttk.Checkbutton(left, text="Ablation: add oxidation-state\n(charge-balance) features", variable=self.ox, style="Panel.TCheckbutton").pack(anchor="w", pady=4)
        ttk.Label(left, text="Stages", style="Head.TLabel").pack(anchor="w", pady=(8, 0))
        for txt, fn in [("1. Evolve rules (live)", self.stage_evolve), ("2. Discovery A: existence (recall@k)", self.stage_discovery),
                        ("3. Contradiction-driven cycle", self.stage_contra), ("4. Periodicity clustering", self.stage_period),
                        ("Run ALL stages on this split", self.stage_all)]:
            ttk.Button(left, text=txt, command=fn, width=36, style="Stage.TButton").pack(anchor="w", pady=2)
        ttk.Label(left, text="Benchmark & results", style="Head.TLabel").pack(anchor="w", pady=(8, 0))
        ttk.Button(left, text="Full benchmark: all 12 splits (CLI, ~minutes)", command=self.run_cli, width=36, style="Warm.TButton").pack(anchor="w", pady=2)
        ttk.Button(left, text="Show saved results/RESULTS.md", command=self.show_saved, width=36).pack(anchor="w", pady=2)
        ttk.Button(left, text="Help (objective, usage, results)", command=self.open_help, width=36, style="Help.TButton").pack(anchor="w", pady=2)
        ttk.Label(left, textvariable=self.status, wraplength=270, style="Status.TLabel").pack(anchor="w", pady=10)
        ttk.Label(left, wraplength=270, style="Note.TLabel", text="Honesty notes: energies are DFT-computed (Materials Project), "
                  "not measured. 91 compounds only. The hidden-40% error curve is shown for teaching; the learner never sees it. "
                  "A compound missing from the database is UNKNOWN, not impossible.").pack(anchor="w")
        nb = ttk.Notebook(self); nb.pack(side="right", fill="both", expand=True, padx=(0, 6), pady=6)
        pa = ScrollArea(nb); nb.add(pa, text="Live plot")
        self.fig = Figure(figsize=(10, 7), dpi=100); self.canvas = FigureCanvasTkAgg(self.fig, master=pa.inner)
        w = self.canvas.get_tk_widget(); w.configure(width=1000, height=700); w.pack()
        f, self.txt = scroll_text(nb, MONO); nb.add(f, text="Results & equation")
        f, self.mem = scroll_text(nb, (MONO[0], 9)); nb.add(f, text="Knowledge memory")
        ff = ttk.Frame(nb, style="Panel.TFrame"); nb.add(ff, text="Saved figures")
        bar = ttk.Frame(ff, style="Panel.TFrame", padding=4); bar.pack(fill="x")
        self.figsel = ttk.Combobox(bar, state="readonly", width=50); self.figsel.pack(side="left")
        ttk.Button(bar, text="Refresh list", command=self.refresh_figs).pack(side="left", padx=6)
        self.figsel.bind("<<ComboboxSelected>>", lambda e: self.show_png())
        ia = ScrollArea(ff); ia.pack(fill="both", expand=True); self.imglab = tk.Label(ia.inner, bg="white"); self.imglab.pack()
        self.after(100, self.poll); self.run_bg(self._load)

    def open_help(self):
        p = os.path.join(HERE, "docs", "Help.rtf")
        if not os.path.exists(p): messagebox.showerror("Help", f"Missing {p}"); return
        self.help_viewer(p)  # always available in-app
        try:
            if sys.platform.startswith("win"): os.startfile(p)
            elif sys.platform == "darwin": subprocess.Popen(["open", p])
            else: subprocess.Popen(["xdg-open", p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            self.status.set(f"Could not open Help.rtf with the default app ({e}); showing it in-app.")

    def help_viewer(self, path):
        import re
        top = tk.Toplevel(self); top.title("Help: EvolutionaryChemistry"); top.geometry("900x700"); top.configure(bg=PAL["bg"])
        f, t = scroll_text(top, UI); f.pack(fill="both", expand=True); t.configure(wrap="word")
        t.tag_configure("h1", font=(UI[0], 16, "bold"), foreground="#163A5F", spacing3=6)
        t.tag_configure("h2", font=(UI[0], 13, "bold"), foreground="#1E5A8A", spacing1=8, spacing3=4)
        t.tag_configure("mono", font=MONO)
        raw = open(path, encoding="ascii", errors="replace").read()
        raw = raw[raw.find("\\pard"):]  # skip header (font/colour/style tables)
        for para in re.split(r"\\par(?![a-z])", raw):
            tag = "h1" if re.search(r"\\s1(?!\d)", para) else "h2" if re.search(r"\\s2(?!\d)", para) else "mono" if re.search(r"\\f1(?!\d)", para) else ""
            para = re.sub(r"\\'([0-9a-f]{2})", lambda m: bytes.fromhex(m.group(1)).decode("cp1252"), para)
            para = re.sub(r"\\u(-?\d+)\?", lambda m: chr(int(m.group(1)) % 65536), para)
            para = para.replace("\\tab", "    ").replace("\\line", "\n")
            para = re.sub(r"\\[a-zA-Z]+-?\d* ?", "", para).replace("{", "").replace("}", "").replace("\r", "").replace("\n", "")
            t.insert("end", para + "\n", tag)
        t.configure(state="disabled")
        ttk.Button(top, text="Close", command=top.destroy).pack(pady=4)
        return top

    # ---------- threading helpers ----------
    def run_bg(self, fn):
        if self.busy: messagebox.showinfo("Busy", "A stage is still running."); return
        self.busy = True
        def w():
            try: fn()
            except Exception as e:
                import traceback; self.q.put(("text", "\nERROR: " + traceback.format_exc())); self.q.put(("status", f"Error: {e}"))
            finally: self.busy = False
        threading.Thread(target=w, daemon=True).start()
    def poll(self):
        try:
            while True:
                kind, val = self.q.get_nowait()
                if kind == "status": self.status.set(val)
                elif kind == "text": self.txt.insert("end", val); self.txt.see("end")
                elif kind == "mem": self.mem.delete("1.0", "end"); self.mem.insert("end", val)
                elif kind == "plot": val(); self.canvas.draw_idle()
                elif kind == "splits": self.cb["values"] = val; self.split.set("random_split_seed0"); self.refresh_figs()
        except queue.Empty: pass
        self.after(80, self.poll)
    def say(self, s): self.q.put(("text", s + "\n"))

    def _load(self):
        self.d = Data(); self.q.put(("splits", list(self.d.splits)))
        self.q.put(("status", f"Ready: {len(self.d.df)} experimentally observed Fe-Na-O-P formulas, {self.d.X.shape[1]} element-attribute features."))
        self.say(f"EvolutionaryChemistry demo. {AUTHOR}. {AI_NOTE}. Data loaded from ./data (Materials Project CC-BY-4.0, mendeleev MIT).\n")
    def _split(self):
        sp = self.d.splits[self.split.get()]; return np.array(sp["train"]), np.array(sp["test"]), int(sp.get("seed", 0))
    def _XF(self): return (self.d.Xo, self.d.fno) if self.ox.get() else (self.d.X, self.d.fn)

    # ---------- stage 1 ----------
    def stage_evolve(self): self.run_bg(self._evolve)
    def _evolve(self):
        d = self.d; tr, te, seed = self._split(); X, fn = self._XF(); y = d.y; name = self.split.get()
        self.q.put(("status", f"Evolving rules on {name} ...")); self.say(f"=== Stage 1: rule evolution on {name} ({len(tr)} train / {len(te)} hidden), oxidation features: {self.ox.get()} ===")
        mean = mae(np.full(len(te), y[tr].mean()), y[te])
        lin = make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-3, 3, 13))).fit(X[tr], y[tr])
        rf = RandomForestRegressor(300, random_state=seed, n_jobs=-1).fit(X[tr], y[tr])
        mem = KnowledgeMemory(f"Fe-Na-O-P formation energy, split {name} (GUI)"); curve = []
        def cb(gp, g):
            curve.append((g, gp.history[-1]["train_mae"], mae(gp.predict(X[te]), y[te])))
            mem.consider(g, gp.to_str(), len(gp.best), gp.history[-1]["train_mae"], len(tr), "evolution", "lower fitness found")
            if g % 2 == 0 or g == self.gens.get() - 1:
                c = np.array(curve)
                def draw(c=c, eq=gp.to_str()):
                    self.fig.clf(); ax = self.fig.add_subplot(111)
                    ax.plot(c[:, 0], c[:, 1], label="train MAE (learner sees)"); ax.plot(c[:, 0], c[:, 2], label="hidden-40% MAE (never used)")
                    for v, l, s in [(mean, "mean baseline", ":"), (mae(lin.predict(X[te]), y[te]), "linear", "--"), (mae(rf.predict(X[te]), y[te]), "random forest", "-.")]:
                        ax.axhline(v, ls=s, color="gray", lw=0.9); ax.text(0, v, " " + l, fontsize=7, va="bottom")
                    ax.set_xlabel("generation"); ax.set_ylabel("MAE (eV/atom)"); ax.set_title(eq[:110], fontsize=8); ax.legend(fontsize=8)
                self.q.put(("plot", draw))
        gp = GP(fn, pop_size=self.pop.get(), generations=self.gens.get(), seed=seed).fit(X[tr], y[tr], callback=cb)
        self.state.update(gp=gp, rf=rf, mem=mem, split=name, ox=self.ox.get())
        self.say(f"Hidden-40% MAE (eV/atom): mean {mean:.3f} | linear {mae(lin.predict(X[te]), y[te]):.3f} | random forest {mae(rf.predict(X[te]), y[te]):.3f} | evolved GP {mae(gp.predict(X[te]), y[te]):.3f}")
        self.say(f"Best evolved rule ({len(gp.best)} nodes):\n  {gp.to_str()}\n")
        self._save_mem(mem, name); self.q.put(("status", "Stage 1 done."))
    def _save_mem(self, mem, name):
        p = os.path.join(R, f"gui_memory_{name}"); mem.save(p + ".json", p + ".md"); self.q.put(("mem", open(p + ".md", encoding="utf-8").read()))
    def _need(self):
        if "gp" not in self.state or self.state["split"] != self.split.get() or self.state["ox"] != self.ox.get():
            self._evolve()

    # ---------- stage 2 ----------
    def stage_discovery(self): self.run_bg(self._discovery)
    def _discovery(self):
        self._need(); d = self.d; tr, te, seed = self._split(); self.q.put(("status", "Discovery A: ranking ~41k candidate formulas ..."))
        cs = d.candidates(); ox = self.ox.get(); Xc = cs.Xo if ox else cs.X; X = d.Xo if ox else d.X
        e, _ = base_score(self.state["gp"].predict(Xc), cs, d.comps, d.y, tr, X[tr], Xc)
        er, _ = base_score(self.state["rf"].predict(cs.X), cs, d.comps, d.y, tr, d.X[tr], cs.X)
        am = analogy_mask(cs, d.comps, tr); rnd_s = np.random.default_rng(seed).random(len(e))
        out = {"GP + training hull (whole space)": hits(e, cs, d.comps, tr, te, KS), "RF + training hull (whole space)": hits(er, cs, d.comps, tr, te, KS),
               "analogy templates, random order": hits(np.where(am, rnd_s, 1e6), cs, d.comps, tr, te, KS),
               "analogy templates ranked by GP+hull": hits(np.where(am, e, 1e6 + e), cs, d.comps, tr, te, KS)}
        r0 = out["analogy templates ranked by GP+hull"]; hid = {cs.ix[cs.key(d.comps[i])] for i in te if cs.key(d.comps[i]) in cs.ix}
        self.say(f"=== Stage 2: Discovery A on {self.split.get()}: {r0['N_ranked']} unseen candidates, {r0['n_hidden_in_space']} hidden real compounds, {int(am.sum())} analogy candidates ===")
        self.say("Top-20 proposals (analogy + GP; * = real hidden compound): " + ", ".join(cs.name(j) + ("*" if j in hid else "") for j in r0["order"][:20]))
        self.say(f"{'top-k':38s}" + "".join(f"{k:>7}" for k in KS))
        for nm, v in out.items(): self.say(f"{nm:38s}" + "".join(f"{v[f'hits@{k}']:>7}" for k in KS))
        self.say(f"{'random guessing':38s}" + "".join(f"{r0[f'random@{k}']:>7.2f}" for k in KS))
        self.say("Note: candidates not in the database are UNKNOWN, not impossible; a 'miss' may be an undiscovered compound.\n")
        def draw():
            self.fig.clf(); ax = self.fig.add_subplot(111)
            for nm, v in out.items(): ax.plot(KS, [v[f"hits@{k}"] for k in KS], "o-", label=nm)
            ax.plot(KS, [r0[f"random@{k}"] for k in KS], "k--", label="random"); ax.set_xscale("log"); ax.set_xlabel("top-k"); ax.set_ylabel("hidden compounds found"); ax.legend(fontsize=8)
            ax.set_title(f"Discovery A: {r0['n_hidden_in_space']} hidden compounds among {r0['N_ranked']} candidates")
        self.q.put(("plot", draw)); self.q.put(("status", "Stage 2 done."))

    # ---------- stage 3 ----------
    def stage_contra(self): self.run_bg(self._contra)
    def _contra(self):
        self._need(); d = self.d; tr, te, _ = self._split(); X, _ = self._XF(); y = d.y; gp = self.state["gp"]; mem = self.state["mem"]
        resid = y[tr] - gp.predict(X[tr]); flag = (np.abs(resid) > 2.5 * np.mean(np.abs(resid))) & (d.df.n_icsd.values[tr] >= 2)
        cons = [{"formula": d.df.formula[i], "Ef_DFT": float(y[i]), "Ef_rule": float(y[i] - r), "n_icsd": int(d.df.n_icsd[i])} for i, r, f in zip(tr, resid, flag) if f]
        mem.annotate_current(contradictions=cons)
        self.say(f"=== Stage 3: contradiction-driven cycle on {self.split.get()} ===\nReliable (>=2 ICSD entries) training compounds the rule mispredicts by >2.5x its mean error:")
        for c in cons: self.say(f"  {c['formula']:14s} DFT {c['Ef_DFT']:+.3f}  rule {c['Ef_rule']:+.3f} eV/atom")
        n = 20; ctrl = copy.deepcopy(gp).fit(X[tr], y[tr], generations=n)
        w = copy.deepcopy(gp)
        w.fit(X[tr], y[tr], w=np.where(flag, 3.0, 1.0), generations=n,
              callback=lambda g_, i: mem.consider(len(gp.history) + i, g_.to_str(), len(g_.best), g_.history[-1]["train_mae"], len(tr), "contradiction-driven", f"{int(flag.sum())} contradictions weighted x3"))
        a, b, c = mae(gp.predict(X[te]), y[te]), mae(ctrl.predict(X[te]), y[te]), mae(w.predict(X[te]), y[te])
        self.say(f"Hidden-40% MAE: before {a:.3f} | +{n} gens normal {b:.3f} | +{n} gens contradiction-weighted {c:.3f}  -> {'helped' if c < b else 'did not help'} on this split")
        if flag.any(): self.say(f"Error on flagged compounds: {np.mean(np.abs(resid[flag])):.3f} -> {np.mean(np.abs(y[tr][flag] - w.predict(X[tr][flag]))):.3f} eV/atom")
        self.say(f"New rule: {w.to_str()}\n"); self._save_mem(mem, self.split.get())
        def draw():
            self.fig.clf(); ax = self.fig.add_subplot(111); ax.bar(["before", "continue\nnormally", "contradiction\nweighted"], [a, b, c], color=["gray", "C0", "C1"])
            ax.set_ylabel("hidden-40% MAE (eV/atom)"); ax.set_title("Contradiction-driven learning (one split; see RESULTS.md for 10)")
        self.q.put(("plot", draw)); self.q.put(("status", "Stage 3 done."))

    # ---------- stage 4 ----------
    def stage_period(self): self.run_bg(self._period)
    def _period(self):
        self.q.put(("status", "Learning element embeddings from ~44k compounds ..."))
        mp = pd.read_csv(os.path.join(D, "mp_expt_observed_subset.csv.gz"))
        vocab, embs, n = periodicity.element_embeddings(mp, EL); labels, k, per = periodicity.evaluate(vocab, embs, self.d.el["Z"].to_dict(), n_null=300)
        self.say(f"=== Stage 4: periodicity teaser: {len(vocab)} elements from {n} compounds (Fe-Na-O-P-only compounds excluded), k={k} ===")
        for nm, v in per.items():
            self.say(f"{nm:32s} ARI {v['ARI']:.3f} (random {v['ARI_null_mean']:.3f}, p={v['p_value']:.3f}); nearest neighbour same group {v['nn_same_group']:.2f} vs random {v['nn_same_group_null']:.2f}")
        v = per["co-occurrence (PPMI-SVD)"]; cl = np.array(v["clusters"])
        for c in sorted(set(cl)): self.say(f"  cluster {c:2d}: " + " ".join(f"{e}({g})" for e, g, cc in zip(vocab, labels, cl) if cc == c))
        self.say("(element(true group)). No group/period information was given to the learner.\n")
        from sklearn.decomposition import PCA
        E = embs["co-occurrence (PPMI-SVD)"]; P = PCA(2, random_state=0).fit_transform(E / np.linalg.norm(E, axis=1, keepdims=True))
        def draw():
            self.fig.clf(); ax = self.fig.add_subplot(111); ax.scatter(P[:, 0], P[:, 1], c=cl, cmap="tab20", s=50)
            for (a, b), s, g in zip(P, vocab, labels): ax.annotate(f"{s}", (a, b), fontsize=7)
            ax.set_title(f"Learned element map (colour = learned cluster), ARI vs groups {v['ARI']:.2f}"); ax.set_xticks([]); ax.set_yticks([])
        self.q.put(("plot", draw)); self.q.put(("status", "Stage 4 done."))

    def stage_all(self): self.run_bg(lambda: (self._evolve(), self._discovery(), self._contra(), self._period()))

    # ---------- CLI / saved ----------
    def run_cli(self):
        def w():
            self.q.put(("status", "Running full benchmark (run_demo.py) ...")); self.say("=== Full benchmark: python run_demo.py ===")
            p = subprocess.Popen([sys.executable, "-u", os.path.join(HERE, "run_demo.py")], cwd=HERE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in p.stdout: self.q.put(("text", line))
            p.wait(); self.q.put(("status", f"Benchmark finished (exit {p.returncode}).")); self.show_saved(); self.refresh_figs()
        self.run_bg(w)
    def show_saved(self):
        p = os.path.join(R, "RESULTS.md")
        self.q.put(("text", ("\n" + open(p, encoding="utf-8").read()) if os.path.exists(p) else "No results/RESULTS.md yet: run the full benchmark.\n"))
        m = os.path.join(R, "memory_random_split_seed0.md")
        if os.path.exists(m): self.q.put(("mem", open(m, encoding="utf-8").read()))
    def refresh_figs(self):
        self.figsel["values"] = sorted(os.path.basename(p) for p in glob.glob(os.path.join(R, "*.png")))
    def show_png(self):
        self._img = tk.PhotoImage(file=os.path.join(R, self.figsel.get())); self.imglab.configure(image=self._img)

if __name__ == "__main__":
    app = App()
    if "--smoke" in sys.argv:  # automated test: run all stages with a small GP, then quit
        app.pop.set(80); app.gens.set(6)
        def go():
            if not hasattr(app, "d"): return app.after(300, go)
            app.stage_all(); wait()
        def wait():
            if app.busy: return app.after(500, wait)
            out = app.txt.get("1.0", "end"); print(out); app.fig.savefig(os.path.join(R, "gui_smoke.png"))
            print("SMOKE", "OK" if "ERROR" not in out and "Stage 4" in out else "FAIL"); app.destroy()
        app.after(500, go)
    app.mainloop()
