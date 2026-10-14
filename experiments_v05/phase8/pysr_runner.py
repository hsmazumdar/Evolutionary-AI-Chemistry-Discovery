"""PySR symbolic regression baseline (run with venv_v05x). Usage: python pysr_runner.py train.npz test.npz out.csv seed"""
import sys, numpy as np, pandas as pd
from pysr import PySRRegressor
a, b = np.load(sys.argv[1]), np.load(sys.argv[2]); seed = int(sys.argv[4])
m = PySRRegressor(niterations=40, populations=8, population_size=50, maxsize=20, binary_operators=["+", "-", "*", "/"], unary_operators=["sqrt", "square"],
                  random_state=seed, deterministic=True, parallelism="serial", progress=False, verbosity=0, model_selection="best", temp_equation_file=True)
m.fit(a["X"], a["y"], variable_names=[str(n) for n in a["names"]])
p = m.predict(b["X"]); pd.DataFrame(dict(y=b["y"], y_pred=p)).to_csv(sys.argv[3], index=False)
print("EQ", m.sympy(), "MAE", float(np.mean(np.abs(b["y"] - p))))
