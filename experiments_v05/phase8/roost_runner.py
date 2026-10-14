"""Roost (aviary, CompRhys) composition-only regressor, trained with a plain loop on CPU. Run with venv_v05x.
Usage: python roost_runner.py train.csv test.csv out.csv  (csv columns: id, composition, y)"""
import sys, numpy as np, pandas as pd, torch
from torch.utils.data import DataLoader
from aviary.roost.data import CompositionData, collate_batch
from aviary.roost.model import Roost
torch.manual_seed(0); np.random.seed(0); torch.set_num_threads(1)
tr, te, out = pd.read_csv(sys.argv[1]), pd.read_csv(sys.argv[2]), sys.argv[3]
mu, sd = tr.y.mean(), tr.y.std()
def loader(df, shuffle):
    d = df.rename(columns={"id": "material_id"}).copy(); d["y"] = (d.y - mu) / sd
    return DataLoader(CompositionData(d, {"y": "regression"}, identifiers=("material_id", "composition")), batch_size=32, shuffle=shuffle, collate_fn=collate_batch)
m = Roost(robust=False, n_targets=[1], task_dict={"y": "regression"}, elem_fea_len=64, n_graph=3)
opt = torch.optim.AdamW(m.parameters(), lr=3e-4, weight_decay=1e-6)
for ep in range(int(sys.argv[4]) if len(sys.argv) > 4 else 150):
    m.train()
    for inputs, targets, *_ in loader(tr, True):
        opt.zero_grad(); p = m(*inputs)[0].squeeze(-1); loss = torch.nn.functional.l1_loss(p, targets[0].float().squeeze(-1)); loss.backward(); opt.step()
m.eval(); P = []
with torch.no_grad():
    for inputs, targets, *_ in loader(te, False): P.append(m(*inputs)[0].squeeze(-1).numpy())
te["y_pred"] = np.concatenate(P) * sd + mu; te.to_csv(out, index=False); print("MAE", float(np.mean(np.abs(te.y - te.y_pred))))
