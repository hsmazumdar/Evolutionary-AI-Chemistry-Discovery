# Data credits

All data needed by the demo is inside `data/`; nothing is downloaded at run time.

| file | source | licence |
|---|---|---|
| `poc_Fe-Na-O-P_expt_formulas.csv`, `poc_Fe-Na-O-P_all_entries.csv`, `mp_expt_observed_subset.csv.gz`, `splits_Fe-Na-O-P/` | Materials Project summary data, release 2025-09-25 (AWS OpenData bucket `materialsproject-build`), downloaded 13 Oct 2026. The subset keeps only the 44,686 carbon-free entries flagged experimentally observed (ICSD-matched). | CC-BY-4.0 |
| `elements_118.csv`, `elements_sources.csv` | `mendeleev` Python package (data from IUPAC, NIST ASD, Pyykko 2009, Slater 1964 and others; see `elements_sources.csv`) | MIT |

Please cite: A. Jain et al., "Commentary: The Materials Project", APL Materials 1, 011002 (2013);
L. M. Mentel, *mendeleev* – A Python resource for properties of chemical elements, ions and isotopes (github.com/lmmentel/mendeleev).

All Materials Project energies are DFT-computed (GGA/GGA+U/r2SCAN mixing), not calorimetric measurements.
The `experimentally_observed` flag means the computed structure matches an ICSD entry.
The split files were generated once with fixed seeds and are part of the benchmark definition.
