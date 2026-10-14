"""Triage backtest v0: rank each arrival day's complaints by a risk score; how many that later close WITH RELIEF land in the top K?

Leakage rules
  - features are fields known on the day the complaint arrives (product, sub-product, issue, sub-issue, bank, tags, channel,
    has-narrative, narrative length bucket). Never company_response, timely, public response.
  - each month's model is trained only on complaints that arrived >= 60 days before that month starts (outcomes settled).
  - complaints still "In progress" are excluded; window ends 2026-06-30 (outcomes of later months are right-censored).

Systems: random (day base rate), issue_rate (historical relief rate by issue), logreg (one-hot features, simple linear score).
Metrics per day then aggregated over days: precision@K, lift vs random, recall@K, with a bootstrap CI over days.

Usage: uv run python evals/triage_backtest.py [--k 50] [--start 2024-07-01] [--end 2026-06-30]
"""

import argparse
import json
import os

import duckdb
import numpy as np
import pandas as pd
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression

ap = argparse.ArgumentParser()
ap.add_argument("--k", type=int, default=50)
ap.add_argument("--start", default="2024-07-01")
ap.add_argument("--end", default="2026-06-30")
ap.add_argument("--gap-days", type=int, default=60)
a = ap.parse_args()

con = duckdb.connect("data/cfpb.duckdb", read_only=True)
df = con.execute("""
    SELECT complaint_id, date_received AS d, product, sub_product, issue, sub_issue, fdic_cert, tags, submitted_via,
           has_narrative, length(narrative) AS nlen, is_older_american, is_servicemember, entity_role, got_relief
    FROM analytics.fct_complaint
    WHERE entity_role IN ('customer','peer') AND NOT is_in_progress AND date_received <= DATE '2026-06-30'
""").df()
df["d"] = pd.to_datetime(df["d"])
df["got_relief"] = df["got_relief"].astype(int)
df["nlen_b"] = pd.cut(df["nlen"].fillna(0), [-1, 0, 500, 1000, 2000, 10**9], labels=["none", "<500", "<1000", "<2000", "2000+"]).astype(str)
FEATS = ["product", "sub_product", "issue", "sub_issue", "fdic_cert", "tags", "submitted_via", "has_narrative", "nlen_b"]
for c in FEATS:
    df[c] = df[c].astype(object).where(df[c].notna(), "missing").astype(str)


def dicts(x):
    return x[FEATS].to_dict("records")


months = pd.period_range(a.start, a.end, freq="M")
rows, per_day = [], []
rng = np.random.default_rng(0)
for m in months:
    m0, m1 = m.start_time, m.end_time
    train = df[df.d < m0 - pd.Timedelta(days=a.gap_days)]
    test = df[(df.d >= m0) & (df.d <= m1)].copy()
    if len(train) < 5000 or test.empty:
        continue
    vec = DictVectorizer()
    xtr = vec.fit_transform(dicts(train))
    clf = LogisticRegression(max_iter=200, C=1.0, solver="lbfgs").fit(xtr, train.got_relief)
    test["s_logreg"] = clf.predict_proba(vec.transform(dicts(test)))[:, 1]
    rate_by_issue = train.groupby("issue").got_relief.mean()
    test["s_issue_rate"] = test.issue.map(rate_by_issue).fillna(train.got_relief.mean())
    test["s_random"] = rng.random(len(test))
    for day, g in test.groupby("d"):
        if len(g) <= a.k or g.got_relief.sum() == 0:
            continue
        base = g.got_relief.mean()
        rec = {"day": day, "n": len(g), "relief": int(g.got_relief.sum()), "base_rate": base}
        for name in ("random", "issue_rate", "logreg"):
            top = g.nlargest(a.k, f"s_{name}", keep="all").head(a.k)
            rec[f"prec_{name}"] = top.got_relief.mean()
            rec[f"recall_{name}"] = top.got_relief.sum() / g.got_relief.sum()
        per_day.append(rec)

pdays = pd.DataFrame(per_day)
os.makedirs("evals/results", exist_ok=True)
pdays.to_csv("evals/results/triage_backtest_v0_per_day.csv", index=False)


def boot(col, n=2000):
    v = pdays[col].values
    means = [v[rng.integers(0, len(v), len(v))].mean() for _ in range(n)]
    return [round(float(np.percentile(means, 2.5)), 4), round(float(np.percentile(means, 97.5)), 4)]


out = {"k": a.k, "days": int(len(pdays)), "window": [a.start, a.end], "gap_days": a.gap_days,
       "mean_base_rate": round(float(pdays.base_rate.mean()), 4), "mean_daily_volume": round(float(pdays.n.mean()), 1), "systems": {}}
for name in ("random", "issue_rate", "logreg"):
    p, r = pdays[f"prec_{name}"], pdays[f"recall_{name}"]
    out["systems"][name] = {"precision_at_k": round(float(p.mean()), 4), "precision_ci95": boot(f"prec_{name}"),
                            "lift_vs_base_rate": round(float((p / pdays.base_rate).mean()), 3),
                            "recall_at_k": round(float(r.mean()), 4), "recall_ci95": boot(f"recall_{name}")}
# paired: share of days the model beats random
out["days_logreg_beats_base_rate"] = round(float((pdays.prec_logreg > pdays.base_rate).mean()), 3)
out["days_issue_rate_beats_base_rate"] = round(float((pdays.prec_issue_rate > pdays.base_rate).mean()), 3)
json.dump(out, open("evals/results/triage_backtest_v0.json", "w"), indent=2)
print(json.dumps(out, indent=2))
