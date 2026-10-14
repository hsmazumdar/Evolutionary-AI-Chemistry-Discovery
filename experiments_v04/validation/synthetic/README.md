# SYNTHETIC controlled contradiction experiments (not chemistry)

Ground truth: y = 0.3 + 1.2·x0 − 0.8·x1·x2 outside exception domain D = {x3 > t}; inside D: y = 0.3 − 1.0·x0 + 1.2·z.
z = x4 (missing=0: observed; missing=1: offered only to S as a candidate variable), or (x4+x5)/2 (missing=2: only partly
recoverable). Observation noise σ; reliability r ~ U(0.2,1), low-r observations get extra noise 0.3(1−r)·N(0,1).
Corruption: a fraction of training labels get ±0.8–1.5 non-reproducible errors (given low reliability when
`rel_informative=True`). Factors varied one at a time around the default (freq 0.15, noise 0.05, missing 1, overlap 0,
corrupt 0). 200 training points, 2000 noise-free test points, 5 seeds per environment. Methods: GP 60 gens,
high-residual specialist, proposed. Same code as Expt-01 (`shared/twopop.py`).
Run: `python reproduce.py`.
