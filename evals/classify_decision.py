"""Decision-model eval: Ollama /v1/systemone (Ollama >= 0.40) with typed `choice` questions.

One request per complaint carries two questions over the same text (product, issue); the model reads once and returns a
probability per option. We keep: raw argmax issue, a product-constrained issue (argmax over the issues valid for the
predicted product), and the full probability vectors (for ensembling and triage confidence later).

Usage (inside the docker wrapper; needs pandas, pyarrow, requests):
  evals/docker_run.sh python evals/classify_decision.py --model tev1:0.8b-q8_0 --tag tev1_0.8b [--limit 20]
Writes data/eval/pred_<tag>.parquet and evals/results/run_meta_<tag>.json. Report with: evals/classify.py report
"""

import argparse
import json
import os
import re
import time

import pandas as pd
import requests

DATA, RESULTS = "data/eval", "evals/results"
SAMPLE, LABELS = f"{DATA}/heldout_2026_05.parquet", f"{DATA}/labels.json"
OLLAMA = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

PRODUCT_CRITERIA = {
    "checking_savings": "A checking or savings account: debit card, ATM, deposits, overdraft, account fees, electronic transfers.",
    "credit_card": "A credit card account: statement charges, interest and fees, billing disputes, payments, card rewards.",
}
PRODUCT_NAMES = {"checking_savings": "Checking or savings account", "credit_card": "Credit card"}


def slug(label):
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")[:60]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()

    labels = json.load(open(LABELS))
    all_issues = labels["all_issues"]
    key_of = {i: slug(i) for i in all_issues}
    assert len(set(key_of.values())) == len(all_issues), "issue slugs collide"
    issue_of = {v: k for k, v in key_of.items()}
    valid = {PRODUCT_NAMES[k]: {key_of[i] for i in labels["by_product"][PRODUCT_NAMES[k]]} for k in PRODUCT_NAMES}

    questions = {
        "product": {"type": "choice", "instructions": "Which product is this consumer complaint about?",
                    "criteria": PRODUCT_CRITERIA},
        "issue": {"type": "choice",
                  "instructions": "Which CFPB issue category best fits this complaint? Pick the broad category unless a specific one clearly applies.",
                  "criteria": {key_of[i]: i for i in all_issues}},
    }

    df = pd.read_parquet(SAMPLE)
    if a.limit:
        df = df.head(a.limit)
    rows, t0 = [], time.time()
    tok_in = 0
    for i, r in enumerate(df.itertuples(), 1):
        s = time.time()
        rec = {"complaint_id": r.complaint_id, "error": None}
        try:
            resp = requests.post(f"{OLLAMA}/v1/systemone", json={"model": a.model, "state": r.narrative, "questions": questions},
                                 timeout=300)
            resp.raise_for_status()
            j = resp.json()
            ans = j["answers"]
            pp = ans["product"]["probabilities"]
            ip = ans["issue"]["probabilities"]
            pred_p = PRODUCT_NAMES[max(pp, key=pp.get)]
            raw_i = max(ip, key=ip.get)
            cons_i = max((k for k in ip if k in valid[pred_p]), key=lambda k: ip[k])
            rec.update(pred_product=pred_p, pred_issue=issue_of[raw_i], pred_issue_c=issue_of[cons_i],
                       product_conf=float(ans["product"].get("confidence", 0)), issue_conf=float(ans["issue"].get("confidence", 0)),
                       issue_probs=json.dumps({issue_of[k]: round(v, 5) for k, v in ip.items()}),
                       product_probs=json.dumps({PRODUCT_NAMES[k]: round(v, 5) for k, v in pp.items()}))
            tok_in += j.get("usage", {}).get("input_tokens", 0)
        except Exception as e:  # keep failures visible, never drop rows
            rec.update(pred_product=None, pred_issue=None, pred_issue_c=None, error=str(e)[:150])
        rec["seconds"] = time.time() - s
        rows.append(rec)
        if i % 25 == 0:
            print(f"{i}/{len(df)}  {time.time() - t0:6.0f}s  avg {(time.time() - t0) / i:.2f}s/item", flush=True)

    out = pd.DataFrame(rows)
    os.makedirs(RESULTS, exist_ok=True)
    out.to_parquet(f"{DATA}/pred_{a.tag}.parquet")
    meta = {"model": a.model, "endpoint": "/v1/systemone", "items": len(out), "errors": int(out.error.notna().sum()),
            "total_seconds": round(time.time() - t0, 1), "input_tokens": tok_in, "cost_usd": 0.0,
            "median_seconds_per_item": round(float(out.seconds.median()), 2)}
    json.dump(meta, open(f"{RESULTS}/run_meta_{a.tag}.json", "w"), indent=2)
    print(meta)


if __name__ == "__main__":
    main()
