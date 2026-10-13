# EvolutionaryChemistry: can a simple evolving system learn real chemistry?

A small, runnable demonstration for prospective PhD scholars joining the research programme on
**evolutionary AI and autonomous scientific discovery** at the R&D Centre, Dharmsinh Desai University, Nadiad
(Prof. Himanshu S. Mazumdar).

> *Can an artificial learning system progressively develop its own knowledge through observation, statistical analysis,
> reasoning, contradiction and evolution, instead of only reproducing existing human knowledge?*

This repository is **proof-of-concept 1 (POC-1)** of that question. It's deliberately small and honest. Every number
below comes from `python run_demo.py` on real data, and the weak results are reported alongside the good ones.
Expect a starting point with real open problems. This is not a finished system.

## Quick start

**Windows:** double-click `Launch_Demo.bat`. The first run creates `.venv` and installs the pinned requirements
(internet needed once). After that the GUI opens. You need Python 3.10+ from python.org with Tcl/Tk (the default option).

**Any OS:**
```bash
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run_demo.py        # full benchmark, ~1.5 min on an 8-core CPU, writes results/
python gui.py             # interactive GUI
python run_demo.py --quick  # 30-second smoke test
```
The repository is self-contained. Everything is read from `data/` and nothing is downloaded at run time.

### The GUI
Choose a split, then run the stages one by one:
1. **Evolve rules (live).** Watch genetic programming evolve an equation generation by generation, against the mean,
   linear and random-forest baselines.
2. **Discovery A.** Rank about 41,000 candidate Fe–Na–O–P formulas and count how many hidden real compounds come up near the top.
3. **Contradiction cycle.** Flag reliable compounds that the current rule gets badly wrong, re-weight them, re-evolve and compare.
4. **Periodicity.** Learn element "families" from compound data alone and compare them with the periodic table.

There's an ablation checkbox that adds oxidation-state (charge-balance) features. The tabs show the evolved equation,
the results tables, the **knowledge memory** (rules with evidence, confidence, limits, contradictions and revision history)
and the saved figures. *Full benchmark* runs `run_demo.py` on all 12 splits.

## The experiment
* **Elements:** Fe, Na, O, P (steelmaking, phosphates, Na-ion cathodes such as NaFePO4).
* **Compounds:** the 91 distinct formulas in this system that Materials Project marks *experimentally observed*
  (structure matched to ICSD). These are 4 elements plus 87 binary, ternary and quaternary compounds.
* **Input to the learner:** element attributes only (Pauling electronegativity, atomic and covalent radius, first
  ionisation energy, mass, density, valence-electron count from the electron configuration). For each compound they are
  combined into composition-weighted mean, mean deviation and range: 22 features, plus 2 more in the ablation.
  **No oxidation states, groups or chemical rules in the main run.**
* **Target:** DFT formation energy per atom.
* **Splits** (fixed, in `data/splits_Fe-Na-O-P/`): 10 seeded random 60/40 splits; a *family* split where whole
  stoichiometry families (AB2, A2B3C4…) are hidden; and a *quaternary* split (train on 1–3-element compounds,
  predict the 4-element ones).
* **No leakage:** the convex hull used for stability is rebuilt from the training compounds only. The learner never sees the
  hidden compounds. The hidden-set error curve in the plots is only for teaching and is never used for selection.

## Results (from `results/RESULTS.md`, run of 13 Oct 2026)

### 1. Evolutionary rule discovery: formation-energy error on hidden compounds (MAE, eV/atom)
| split | mean predictor | linear (ridge) | random forest | **evolved equation (GP)** | GP + oxidation states |
|---|---|---|---|---|---|
| 10 random 60/40 | 0.624 ± 0.062 | **0.197 ± 0.018** | 0.239 ± 0.045 | 0.305 ± 0.049 | 0.206 ± 0.046 |
| families held out | 0.787 | 0.328 | **0.280** | 0.293 | 0.551 |
| 4-element held out | 0.861 | 0.204 | 0.531 | 0.343 | **0.195** |

The evolved equations are 50–60% better than the mean predictor and readable, but on random splits they are **not yet
as accurate as plain linear regression** on all 22 features. They hold up better than linear when whole families are hidden.
The evolved rule from split 0 has 8 nodes:

`Ef = 0.552 − 0.476 · ( n_elem + (dev_rCov / mean_rA) · mean_EN² )`

That reads as: formation energy becomes more negative with more elements, a larger spread in covalent radius and higher
average electronegativity. Each split evolves a *different* equation (see RESULTS.md), and that variation is a research question in itself.
Supplying oxidation states (prior chemical knowledge) helps on random and 4-element splits but hurts on the family split.

### 2. Discovery A: re-finding hidden real compounds (mean over 10 random splits)
About 41,300 unseen candidate formulas Fe_a Na_b O_c P_d (a+b+c+d ≤ 30), with about 33 hidden real compounds among them.

| method | top 100 | top 200 | top 1000 |
|---|---|---|---|
| random guessing | 0.08 | 0.16 | 0.8 |
| evolved equation + training hull, whole space | 0.0 | 0.0 | 0.1 |
| analogy (re-use training stoichiometry templates), random order | 0.4 | 1.5 | 7.4 |
| **analogy + evolved equation (with ox. states) + training hull** | **2.0** | **3.0** | 7.4 |
| charge balance only (uses oxidation states) | 0.5 | 1.2 | 7.8 |

**An honest negative result:** ranking the whole space by predicted energy fails. Rules learned only from real
compounds extrapolate to absurd formulas such as NaO29, and an error of about 0.3 eV/atom is far larger than the roughly
0.05 eV/atom that separates stable from unstable. Adding a second, *analogical* hypothesis generator (reuse stoichiometries
the system has seen) gives about 25× enrichment over random in the top 100, but it still recovers only about 6% of the hidden compounds there.
**Unknown ≠ impossible:** a top-ranked candidate that's missing from the database may simply never have been made.

### 3. Contradiction-driven learning
After evolution, *reliable* training compounds (≥2 ICSD entries) that the rule mispredicts by more than 2.5× its mean
error are flagged. Typical examples are NaO2/NaO3 (superoxide/ozonide), P2O5 and Na3PO4. They get 3× weight for 20 more generations,
compared with 20 normal generations.
* Error on the flagged compounds: 0.76 → 0.56 eV/atom (the system does learn them).
* Hidden-set MAE: 0.296 ± 0.042 (normal) vs 0.300 ± 0.057 (contradiction-weighted). Better on 6 of 10 splits, **no
  significant overall gain.** Making contradictions *useful*, rather than just fitting them, is an open PhD-level problem.

### 4. Periodicity teaser: no periodic table supplied
Element vectors were learned only from which elements co-occur in 44,515 experimentally observed compounds (Fe–Na–O–P-only compounds excluded),
then clustered into as many clusters as there are true groups (20). The comparison is with IUPAC groups, with lanthanides and actinides as separate families.

| embedding | adjusted Rand index | random (95th pct) | nearest neighbour in same group |
|---|---|---|---|
| co-occurrence | **0.53** | 0.03 | 51% (random 6%) |
| formation-energy profile | 0.22 | 0.03 | 40% |

Halogens and chalcogens, lanthanides with Sc/Y, actinides, the Pt-group metals and Mo/W/Nb/Ta come out as families without any
group information. Alkali metals are only partly grouped (K and Cs fall elsewhere).

Figures in `results/`: `fig1_learning_curve.png`, `fig2_parity_seed0.png`, `fig3_recall_at_k.png`, `fig4_element_map.png`.
The knowledge memory is in `results/memory_*.json|md`.

## Honest limitations
* **The energies are DFT-computed** (Materials Project GGA/GGA+U/r2SCAN), not measured. "Experimentally observed" means
  the structure is ICSD-matched.
* **Small data:** no 3- or 4-element system in Materials Project has 100 or more experimentally observed formulas (the maximum is 97),
  so POC-1 uses 91. Results move noticeably between splits (see the ± values).
* The "evolutionary" part here is classical GP plus a memory log. Evolving the *learning strategy itself* hasn't been done yet.
* Formulas only: polymorphs, temperature and pressure are ignored.

## Exercises for students
1. Beat linear regression with GP: add constants optimisation, multi-objective (accuracy vs size) selection or an island model.
2. Make contradictions useful: spawn a *specialist* rule for the contradicting region instead of re-weighting.
3. Teach existence directly: use MP's *theoretical* (unobserved) entries from training compositions as weak negatives.
4. Let the system rediscover charge balance: can GP discover a feature equivalent to oxidation-state balance?
5. Use the learned element embeddings as features for property prediction. Does "self-discovered periodicity" help?
6. Repeat the study for H-N-O-S (sulfuric and nitric acid chemistry) or validate against measured enthalpies.

## Repository layout
```
run_demo.py         one-command benchmark -> results/
gui.py              Tkinter GUI;  Launch_Demo.bat  Windows launcher
evochem/            features.py  gp.py  hull.py  discovery.py  memory.py  periodicity.py
data/               all input data (see DATA_CREDITS.md)
results/            tables, figures, knowledge memory from the last run
```
Licence: MIT (code). Data: Materials Project CC-BY-4.0, mendeleev MIT. See `DATA_CREDITS.md`.
