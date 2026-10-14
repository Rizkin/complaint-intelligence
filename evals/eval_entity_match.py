"""Score the entity matcher against the filled verification sheet (the human's verdicts are the gold).

Strict (primary, ownership): a match is right only if the company IS or OWNS the predicted FDIC bank.
  gold cert per row:  Right -> predicted cert (or none if no bank was predicted);  Wrong - different bank -> correct_cert;
                      Wrong - no FDIC bank exists -> none;  Unsure -> row skipped.
Broad (secondary, owner-or-connected): rows with partner certs (column P) count as having a connected bank, so predicting NO BANK is a miss.
precision = correct / predicted matches;  recall = correct / rows whose gold has a bank.  Unweighted and weighted by complaints.

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

raw = pd.read_excel(a.sheet, sheet_name="Pairs")
raw = raw.rename(columns={"correct_cert (if 'Wrong, different bank')": "correct_cert", "broad_partner_certs (not ownership)": "partners"})
if "partners" not in raw:
    raw["partners"] = None
raw = raw[raw["verdict"].notna() & (raw["verdict"] != "Unsure")].copy()


def gold(r):
    v = r["verdict"]
    if v == "Right":
        return r["predicted_cert"]
    if v.startswith("Wrong - different"):
        return r["correct_cert"]
    return None


def score(df, broad):
    df = df.copy()
    df["gold_cert"] = df.apply(gold, axis=1)
    df["pred_has"] = df["predicted_cert"].notna()
    df["gold_has"] = df["gold_cert"].notna() | (df["partners"].notna() if broad else False)
    same = df["predicted_cert"].astype("Int64") == df["gold_cert"].astype("Int64")
    df["correct_match"] = df.pred_has & df["gold_cert"].notna() & same

    def prf(d, w=None):
        w = d[w] if w else 1
        tp, pn, gn = (d.correct_match * w).sum(), (d.pred_has * w).sum(), (d.gold_has * w).sum()
        return {"precision": round(float(tp / pn), 4) if pn else None, "recall": round(float(tp / gn), 4) if gn else None}

    res = {"rows_scored": int(len(df)), "unweighted": prf(df), "weighted_by_complaints": prf(df, "complaints"),
           "predicted_matches": int(df.pred_has.sum()), "gold_banks": int(df.gold_has.sum()),
           "gate_precision>=0.95": None, "gate_recall>=0.90": None}
    p, r = res["unweighted"]["precision"], res["unweighted"]["recall"]
    res["gate_precision>=0.95"] = None if p is None else bool(p >= 0.95)
    res["gate_recall>=0.90"] = None if r is None else bool(r >= 0.90)
    errs = df[(df.pred_has != df.gold_has) | (df.pred_has & df["gold_cert"].notna() & ~df.correct_match)]
    res["errors"] = errs[["cfpb_company", "complaints", "predicted_cert", "gold_cert", "verdict"]].astype(str).to_dict("records")
    return res


out = {"strict_ownership": score(raw, broad=False), "broad_owner_or_partner": score(raw, broad=True)}
os.makedirs(os.path.dirname(a.out), exist_ok=True)
json.dump(out, open(a.out, "w"), indent=2)
for k, v in out.items():
    print(f"== {k}: rows {v['rows_scored']}, predicted matches {v['predicted_matches']}, gold banks {v['gold_banks']}")
    print("   unweighted", v["unweighted"], "| weighted by complaints", v["weighted_by_complaints"])
    print("   gates: precision>=0.95", v["gate_precision>=0.95"], "| recall>=0.90", v["gate_recall>=0.90"])
    print(f"   {len(v['errors'])} errors")
for e in out["strict_ownership"]["errors"]:
    print("   strict error:", e["cfpb_company"][:44], "| pred", e["predicted_cert"], "| gold", e["gold_cert"], "|", e["verdict"])
