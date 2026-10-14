# Expt-05 — Statistical focusing (active observation)

Learner starts with 8 random labelled training compounds and requests 4 more per round up to 40, only from its training
partition (test sealed). GP warm-started, 12 generations × pop 150 per round for every strategy (matched).
Strategies: random; uncertainty (archive disagreement); uncertainty × evidence reliability; diversity (max-min
standardised feature distance); uncertainty + diversity. 16 splits × 3 seeds. Metrics: final test MAE and mean MAE over
the learning curve (area-under-curve proxy).
