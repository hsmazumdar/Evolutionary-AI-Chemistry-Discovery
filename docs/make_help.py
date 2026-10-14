"""Builds docs/Help.rtf (run: python docs/make_help.py). Numbers are copied from results/RESULTS.md of the 13 Oct 2026 run."""
import os
def esc(s):
    out = []
    for ch in s:
        if ch in "\\{}": out.append("\\" + ch)
        elif ord(ch) > 127: out.append(f"\\u{ord(ch) if ord(ch) < 32768 else ord(ch) - 65536}?")
        else: out.append(ch)
    return "".join(out)
B = []
def h1(t): B.append(r"\pard\s1\sb240\sa120\f0\fs36\b\cf2 " + esc(t) + r"\b0\cf0\fs22\par")
def h2(t): B.append(r"\pard\s2\sb200\sa80\f0\fs28\b\cf3 " + esc(t) + r"\b0\cf0\fs22\par")
def p(t): B.append(r"\pard\sa100\f0\fs22 " + esc(t) + r"\par")
def bl(t): B.append(r"\pard\li360\fi-240\sa60\f0\fs22 \u8226? " + esc(t) + r"\par")
def mono(t): B.append(r"\pard\li360\sa40\f1\fs20 " + esc(t) + r"\f0\fs22\par")
def table(rows):
    for r in rows: mono("  ".join(f"{c:<{w}}" for c, w in zip(r, [44, 16, 16, 16, 16, 16])))

h1("EvolutionaryChemistry: Help")
p("Demo for prospective PhD scholars. Author: Himanshu Mazumdar, R&D Centre, Dharmsinh Desai University, Nadiad, Gujarat.")

h1("1. Objective")
p("The research question is whether a simple, evolving learning system can build its own knowledge from real scientific data "
  "by observing, finding regularities, keeping a memory of rules, noticing contradictions and revising itself, instead of only reproducing human knowledge.")
p("This proof of concept (POC-1) uses inorganic chemistry. The system sees only measured element attributes (electronegativity, radii, "
  "ionisation energy, mass, density, valence electrons) for the Fe-Na-O-P system. It learns from 60% of the 91 experimentally observed "
  "compounds and is tested on the hidden 40%.")
bl("Discovery B (properties): can evolved, readable equations predict formation energy of unseen compounds?")
bl("Discovery A (existence): can the system re-find hidden real compounds among about 41,000 candidate formulas?")
bl("Contradiction-driven learning: does focusing on reliable compounds the current rule gets wrong improve the rule?")
bl("Periodicity: do element families resembling the periodic table emerge from compound data alone?")

h1("2. Usage")
h2("Launching")
bl("Windows: double-click Launch_Demo.bat. On first run it checks Python 3.10+ and Tkinter, creates .venv in the repo and installs requirements.txt (internet needed once). Then the GUI opens.")
bl("Any OS: python -m venv .venv, activate it, pip install -r requirements.txt, then python gui.py. The command-line benchmark is python run_demo.py (about 1.5 to 3 minutes).")
bl("All data is in data/. Nothing is downloaded while the demo runs.")
h2("Controls (left panel)")
bl("Experiment / split: one of 10 random 60/40 splits, family held out (whole stoichiometry families hidden) or quaternary held out (train on 1 to 3 element compounds, test on 4 element ones).")
bl("GP population and generations: size and length of the evolutionary search (defaults 300 and 40).")
bl("Ablation checkbox: adds oxidation-state charge-balance features, which is prior chemical knowledge. Leave it off for the pure experiment.")
h2("Stages")
bl("1. Evolve rules (live): genetic programming evolves an equation for formation energy. The plot shows training error, the hidden-set error (for teaching only, never used by the learner) and the mean, linear and random-forest baselines.")
bl("2. Discovery A: candidate formulas are ranked by predicted energy above a convex hull built only from training compounds, both over the whole space and restricted to stoichiometry templates seen in training (analogy). Hidden compounds found in the top k are compared with random guessing.")
bl("3. Contradiction-driven cycle: reliable training compounds (2 or more ICSD entries) mispredicted by more than 2.5 times the mean error are flagged and weighted x3 for 20 more generations, then compared with 20 normal generations.")
bl("4. Periodicity clustering: element vectors are learned from co-occurrence in about 44,500 compounds (Fe-Na-O-P-only compounds excluded), then clustered and compared with the true groups (adjusted Rand index).")
bl("Run ALL stages runs 1 to 4 on the chosen split. Full benchmark runs run_demo.py on all 12 splits and refreshes results/.")
h2("Outputs")
bl("Tabs: Live plot, Results & equation, Knowledge memory (each rule with evidence, confidence, limits, contradictions and revision history) and Saved figures. All panels scroll both ways.")
bl("Files in results/: RESULTS.md, property_mae_by_split.csv, discovery_recall_by_split.csv, contradiction_by_split.csv, periodicity.json, memory_*.json/.md and fig1 to fig4 PNG figures.")

h1("3. Results (run of 13 Oct 2026)")
h2("Formation-energy error on hidden compounds (MAE, eV/atom)")
table([["split", "mean", "linear", "rand. forest", "evolved GP", "GP+ox.states"],
       ["10 random 60/40 (mean ± sd)", "0.624±0.062", "0.197±0.018", "0.239±0.045", "0.305±0.049", "0.206±0.046"],
       ["families held out", "0.787", "0.328", "0.280", "0.293", "0.551"],
       ["4-element held out", "0.861", "0.204", "0.531", "0.343", "0.195"]])
p("Example evolved rule (split 0, 8 nodes): Ef = 0.552 - 0.476 * (n_elem + (dev_rCov / mean_rA) * mean_EN^2).")
p("Interpretation: the evolved equations are readable and cut the error of the mean predictor by about half, but on random splits they are "
  "less accurate than plain linear regression. They hold up better when whole families are hidden. Each split evolves a different equation.")
h2("Discovery A: hidden compounds found (mean of 10 splits, about 33 hidden among about 41,300 candidates)")
table([["method", "top 100", "top 200", "top 1000"],
       ["random guessing", "0.08", "0.16", "0.8"],
       ["evolved rule + training hull, whole space", "0.0", "0.0", "0.1"],
       ["analogy templates, random order", "0.4", "1.5", "7.4"],
       ["analogy + evolved rule (ox. states) + hull", "2.0", "3.0", "7.4"],
       ["charge balance only", "0.5", "1.2", "7.8"]])
p("Interpretation: ranking the whole space by predicted energy fails, because rules learned only from real compounds extrapolate to absurd formulas "
  "and their error (about 0.3 eV/atom) is far larger than the stability scale (about 0.05 eV/atom). The analogy generator gives about 25 times random in "
  "the top 100, but that is still only about 6% of the hidden compounds. A candidate missing from the database is unknown, not impossible.")
h2("Contradiction-driven learning")
p("About 2.2 compounds are flagged per split (e.g. NaO2/NaO3, P2O5, Na3PO4). Their error falls from 0.76 to 0.56 eV/atom, but hidden-set MAE is "
  "0.300 ± 0.057 with re-weighting versus 0.296 ± 0.042 without (better on 6 of 10 splits). There is no overall gain: an open research problem.")
h2("Periodicity teaser")
p("81 elements, 20 clusters. The co-occurrence embedding gives adjusted Rand index 0.53 (random 0.001, 95th percentile 0.034, p < 0.001). The nearest neighbour is in the same group "
  "51% of the time (random 6%). Halogens with chalcogens, lanthanides with Sc and Y, actinides, Pt-group metals and Mo/W/Nb/Ta emerge as families. Alkali metals are only partly grouped.")
h2("Honest limitations")
bl("Energies are DFT-computed (Materials Project), not measured. 'Experimentally observed' means the structure matches an ICSD entry.")
bl("Only 91 compounds: no 3- or 4-element system in Materials Project has 100 or more observed formulas. Results vary between splits.")
bl("Evolution here is classical GP plus a memory log. Evolving the learning strategy itself is future work.")

h1("4. About")
p("EvolutionaryChemistry POC-1 demo. Prof. Himanshu Mazumdar, R&D Centre, Dharmsinh Desai University, Nadiad, Gujarat, India.")
p("Code: MIT licence. Data: Materials Project (CC-BY-4.0) and mendeleev (MIT). See DATA_CREDITS.md.")

hdr = (r"{\rtf1\ansi\ansicpg1252\deff0{\fonttbl{\f0\fswiss Segoe UI;}{\f1\fmodern Consolas;}}"
       r"{\colortbl;\red0\green0\blue0;\red22\green58\blue95;\red30\green90\blue138;}"
       r"{\stylesheet{\s0 Normal;}{\s1\fs36\b heading 1;}{\s2\fs28\b heading 2;}}" "\n")
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "Help.rtf"), "w", encoding="ascii").write(hdr + "\n".join(B) + "\n}\n")
print("wrote Help.rtf")
