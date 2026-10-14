"""Score the entity matcher against the filled verification sheet (your verdicts are the gold).

gold cert per row:  Right -> predicted cert (or none if no bank was predicted);  Wrong - different bank -> correct_cert;
                    Wrong - no FDIC bank exists -> none;  Unsure -> row skipped.
precision = correct / predicted matches;  recall = correct / rows whose gold has a bank.  Reported unweighted and weighted by complaints.
Usage: uv run python evals/eval_entity_match.py [--sheet data/eval/entity_pairs_100.xlsx]
"""

import argparse
import json
import os

import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--sheet", default="data/eval/entity_pairs_100.xlsx")
ap.add_argument("--out", default="evals/results/entity_match_eval.json")
a = ap.parse_args()

df = pd.read_excel(a.sheet, sheet_name="Pairs")
df = df.rename(columns={"correct_cert (if 'Wrong, different bank')": "correct_cert"})
df = df[df["verdict"].notna() & (df["verdict"] != "Unsure")].copy()


def gold(r):
    v = r["verdict"]
    if v == "Right":
        return r["predicted_cert"]
    if v.startswith("Wrong - different"):
        return r["correct_cert"]
    return None


df["gold_cert"] = df.apply(gold, axis=1)
df["pred"] = df["predicted_cert"]
df["pred_has"] = df["pred"].notna()
df["gold_has"] = df["gold_cert"].notna()
df["correct_match"] = df.pred_has & df.gold_has & (df.pred.astype("Int64") == df.gold_cert.astype("Int64"))


def prf(d, w=None):
    w = d[w] if w else 1
    tp = (d.correct_match * w).sum()
    pred_n, gold_n = (d.pred_has * w).sum(), (d.gold_has * w).sum()
    p = float(tp / pred_n) if pred_n else None
    r = float(tp / gold_n) if gold_n else None
    return {"precision": None if p is None else round(p, 4), "recall": None if r is None else round(r, 4)}


res = {"rows_scored": int(len(df)), "unweighted": prf(df), "weighted_by_complaints": prf(df, "complaints"),
       "predicted_matches": int(df.pred_has.sum()), "gold_banks": int(df.gold_has.sum()),
       "gate": {"precision>=0.95": None, "recall>=0.90": None}}
for k, key in (("precision>=0.95", "precision"), ("recall>=0.90", "recall")):
    v = res["unweighted"][key]
    res["gate"][k] = None if v is None else bool(v >= float(k.split(">=")[1]))
errs = df[(df.pred_has != df.gold_has) | (df.pred_has & df.gold_has & ~df.correct_match)]
res["errors"] = errs[["cfpb_company", "complaints", "predicted_cert", "gold_cert", "verdict"]].astype(str).to_dict("records")
os.makedirs(os.path.dirname(a.out), exist_ok=True)
json.dump(res, open(a.out, "w"), indent=2)
print(json.dumps({k: v for k, v in res.items() if k != "errors"}, indent=2))
print(f"{len(errs)} errors:")
print(errs[["cfpb_company", "complaints", "predicted_cert", "gold_cert", "verdict"]].to_string(index=False, max_colwidth=44))
