"""Build the 100-pair entity-matching verification sheet (xlsx with dropdowns) from pipelines/entity_match.py output.

Selection (seed 11), so both precision and recall can be measured and the volume-weighted view matters:
  40  high-volume names (n >= 100), any prediction
  30  low-volume names the matcher MATCHED            -> measures precision on the tail
  30  low-volume names it REJECTED but whose name looks bank-like -> measures missed matches (recall)

You judge: is the predicted FDIC bank the right one for that CFPB company? Gold answers are your answers.
Usage: uv run python evals/make_entity_sheet.py [--out data/eval/entity_pairs_100.xlsx]
"""

import argparse
import json
import re

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="data/eval/entity_pairs_100.xlsx")
a = ap.parse_args()

df = pd.read_csv("data/eval/entity_match.csv")
df["alts"] = df.alt_candidates.map(json.loads)
bank_like = re.compile(r"BANK|BANCORP|BANCSHARES|TRUST|SAVINGS|FEDERAL|FINANCIAL|BANC|CAPITAL", re.I)

big = df[df.n_complaints >= 100]
tail_matched = df[(df.n_complaints < 100) & df.cert.notna()]
tail_rejected = df[(df.n_complaints < 100) & df.cert.isna() & df.company.map(lambda x: bool(bank_like.search(x)))]
parts = [big.sample(n=min(40, len(big)), random_state=11),
         tail_matched.sample(n=min(30, len(tail_matched)), random_state=11),
         tail_rejected.sample(n=min(30, len(tail_rejected)), random_state=11)]
pick = pd.concat(parts).drop_duplicates("company")
extra = df[~df.company.isin(pick.company)].sample(n=100 - len(pick), random_state=11) if len(pick) < 100 else pick.iloc[0:0]
pick = pd.concat([pick, extra]).sample(frac=1, random_state=11).reset_index(drop=True)

wb = Workbook()
ws = wb.active
ws.title = "Pairs"
cols = ["#", "cfpb_company", "complaints", "predicted_cert", "predicted_bank", "state", "holding_company", "assets_bn", "score",
        "alt_1 (cert | name | score)", "alt_2", "alt_3",
        "verdict", "correct_cert (if 'Wrong, different bank')", "note"]
ws.append(cols)


def alt(r, i):
    al = [x for x in r.alts if x["cert"] != r.cert]
    return f'{al[i]["cert"]} | {al[i]["name"]} | {al[i]["score"]}' if len(al) > i else ""


for i, r in enumerate(pick.itertuples(), 1):
    ws.append([i, r.company, int(r.n_complaints), None if pd.isna(r.cert) else int(r.cert),
               r.institution if pd.notna(r.institution) else "(no bank predicted)", r.state if pd.notna(r.state) else "",
               r.holding_company if pd.notna(r.holding_company) else "", None if pd.isna(r.assets_bn) else float(r.assets_bn),
               float(r.score), alt(r, 0), alt(r, 1), alt(r, 2), None, None, None])

fill = PatternFill("solid", fgColor="1F4E78")
for c in ws[1]:
    c.font = Font(bold=True, color="FFFFFF")
    c.fill = fill
    c.alignment = Alignment(wrap_text=True, vertical="center")
for k, v in {"A": 5, "B": 40, "C": 11, "D": 13, "E": 38, "F": 7, "G": 30, "H": 10, "I": 7, "J": 46, "K": 40, "L": 40, "M": 30, "N": 22, "O": 28}.items():
    ws.column_dimensions[k].width = v
for row in ws.iter_rows(min_row=2):
    for c in row:
        c.alignment = Alignment(wrap_text=True, vertical="top")
ws.freeze_panes = "C2"
dv = DataValidation(type="list", formula1='"Right,Wrong - different bank,Wrong - no FDIC bank exists,Unsure"', allow_blank=True)
ws.add_data_validation(dv)
dv.add(f"M2:M{len(pick) + 1}")

guide = wb.create_sheet("Guide", 0)
for line in [
    "Entity matching check (plan: Tue Oct 13, 2.5 h; pre-filled here so it is a review, about 20 min).",
    "Each row: a company name from the CFPB complaints and the FDIC bank my matcher picked (or 'no bank predicted').",
    "Pick a verdict:",
    "  Right: the prediction is correct. If no bank was predicted, 'Right' means this company really has no FDIC-insured bank (credit union, fintech, collector, bureau...).",
    "  Wrong - different bank: type the correct FDIC certificate in the next column (alt_1..3 show the matcher's other candidates; or look up the cert at FDIC BankFind).",
    "  Wrong - no FDIC bank exists: the predicted bank is wrong and the company has no FDIC bank.",
    "  Unsure: skip it (excluded from the score).",
    "Hints: holding company -> its main deposit-taking bank (e.g. JPMorgan Chase & Co. -> JPMorgan Chase Bank, N.A.).",
    "Credit unions are NCUA-insured, not FDIC, so they have no match. Fintechs usually partner with a bank but are not one.",
    "Save the file in place. The score is computed by evals/eval_entity_match.py.",
]:
    guide.append([line])
guide.column_dimensions["A"].width = 150
wb.save(a.out)
print(f"wrote {a.out}: {len(pick)} rows; predicted-match {int(pick.cert.notna().sum())}, predicted-no-bank {int(pick.cert.isna().sum())}; "
      f"covers {pick.n_complaints.sum():,} complaints")
