"""E2: first-report year per reduced formula from the public MP provenance collection (2025-09-25), AWS Open Data bucket
materialsproject-build. year = min BibTeX year over non-MP-methodology references of ICSD-linked provenance docs (PREREG_V06 s5)."""
import os, re, json, gzip, hashlib, urllib.request, xml.etree.ElementTree as ET
import pandas as pd
D = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(D, "data", "provenance_raw"); os.makedirs(RAW, exist_ok=True)
B = "https://materialsproject-build.s3.amazonaws.com"; PFX = "collections/2025-09-25/provenance/"
MP_REF_KEYS = re.compile(r"@\w+\{\s*(Jain2013|Ong2013|Ong2015|Mathew2017|Horton2025|Munro2020|Jain2011|Wang2006|Aykol2018|Shen2021)\b", re.I)
MP_DOIS = ("10.1063/1.4812323", "10.1016/j.commatsci.2012.10.028")
def keys():
    out, tok = [], None
    while True:
        u = f"{B}/?list-type=2&prefix={PFX}" + (f"&continuation-token={urllib.parse.quote(tok)}" if tok else "")
        x = ET.fromstring(urllib.request.urlopen(u, timeout=60).read()); ns = {"s": x.tag.split("}")[0][1:]}
        out += [(k.find("s:Key", ns).text, int(k.find("s:Size", ns).text)) for k in x.findall("s:Contents", ns)]
        t = x.find("s:NextContinuationToken", ns)
        if t is None: return out
        tok = t.text
import urllib.parse
K = [k for k in keys() if k[0].endswith(".jsonl.gz")]; man = {}
def red_key(c):
    t = sum(c.values()); return json.dumps({k: round(v / t, 6) for k, v in sorted(c.items())})
rows = []
for k, size in K:
    p = os.path.join(RAW, k.replace("/", "__"))
    if not os.path.exists(p) or os.path.getsize(p) != size: urllib.request.urlretrieve(f"{B}/{k}", p)
    man[k] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    for l in gzip.open(p, "rt"):
        d = json.loads(l)
        if not (d.get("database_IDs") or {}).get("icsd"): continue
        ys = []
        for r in d.get("references") or []:
            if MP_REF_KEYS.search(r) or any(x in r for x in MP_DOIS): continue
            m = re.search(r"year\s*=\s*[{\"]?\s*(\d{4})", r)
            if m and 1800 <= int(m.group(1)) <= 2026: ys.append(int(m.group(1)))
        rows.append(dict(key=red_key(d["composition_reduced"]), material_id=d["material_id"], year=min(ys) if ys else None, n_refs=len(d.get("references") or [])))
R = pd.DataFrame(rows); R.to_csv(os.path.join(D, "data", "provenance_icsd_years_by_material.csv"), index=False)
Y = R.dropna(subset=["year"]).groupby("key").year.min().astype(int).reset_index(); Y.to_csv(os.path.join(D, "data", "first_report_year.csv"), index=False)
json.dump(dict(prefix=PFX, files=man), open(os.path.join(D, "data", "PROVENANCE_MANIFEST.json"), "w"), indent=1)
print("icsd-linked provenance docs", len(R), "with year", int(R.year.notna().sum()), "formulas with year", len(Y))
