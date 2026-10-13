"""Baseline complaint classifier eval: predict CFPB product and issue from the consumer narrative.

Held-out month: 2026-05 (narrative coverage ~40%). Two systems, same sample, same metrics:
  llm    zero-shot local model through Ollama, constrained JSON output (every label is valid)
  tfidf  TF-IDF + logistic regression trained on 2024-01..2026-02 (no peeking at the held-out month)

Narratives stay in data/eval/ (gitignored). Only metrics and confusion matrices go to evals/results/.

Usage (repo root):
  uv run python evals/classify.py sample                  # build data/eval/heldout_2026_05.parquet
  uv run python evals/classify.py llm   [--limit 50]      # zero-shot LLM predictions
  uv run python evals/classify.py tfidf                   # supervised reference
  uv run python evals/classify.py report                  # macro-F1, confusion matrices -> evals/results/
"""

import argparse
import json
import os
import time

import pandas as pd
import requests

DB = "data/cfpb.duckdb"
DATA = "data/eval"
RESULTS = "evals/results"
SAMPLE = f"{DATA}/heldout_2026_05.parquet"
LABELS = f"{DATA}/labels.json"
HELD_OUT = ("2026-05-01", "2026-05-31")
PER_PRODUCT = 300
SEED = 42
MAX_CHARS = 1500

OLLAMA = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MODEL = os.environ.get("OLLAMA_MODEL", "qwen3.5:2b")

PRODUCTS = ["Checking or savings account", "Credit card"]
ENTITY_ROLES = "('customer','peer')"


def issue_labels(con):
    rows = con.execute(f"""
        SELECT product, issue FROM analytics.fct_complaint
        WHERE entity_role IN {ENTITY_ROLES} AND issue IS NOT NULL
          AND date_received BETWEEN '2024-01-01' AND '2026-02-28'
        GROUP BY 1, 2""").fetchall()
    by_product = {p: sorted(i for q, i in rows if q == p) for p in PRODUCTS}
    all_issues = sorted({i for _, i in rows})
    return by_product, all_issues


def cmd_sample(_):
    import duckdb

    os.makedirs(DATA, exist_ok=True)
    con = duckdb.connect(DB, read_only=True)
    by_product, all_issues = issue_labels(con)
    json.dump({"by_product": by_product, "all_issues": all_issues}, open(LABELS, "w"), indent=1)
    df = con.execute(f"""
        SELECT complaint_id::VARCHAR AS complaint_id, date_received, product, issue, narrative, company
        FROM analytics.fct_complaint
        WHERE entity_role IN {ENTITY_ROLES} AND has_narrative AND issue IS NOT NULL
          AND date_received BETWEEN '{HELD_OUT[0]}' AND '{HELD_OUT[1]}'""").df()
    parts = [g.sample(n=min(PER_PRODUCT, len(g)), random_state=SEED) for _, g in df.groupby("product")]
    out = pd.concat(parts).sort_values("complaint_id").reset_index(drop=True)
    out["narrative"] = out["narrative"].str.slice(0, MAX_CHARS)
    out.to_parquet(SAMPLE)
    print(f"held-out pool {len(df):,} -> sample {len(out)}")
    print(out.groupby("product").size())


def build_prompt(issues):
    return (
        "You classify US consumer complaints about bank accounts and credit cards.\n"
        "Read the complaint and choose:\n"
        f'- product: one of {json.dumps(PRODUCTS)}\n'
        "- issue: the single best issue label from the allowed list.\n"
        "Text like XXXX is redaction, ignore it. Answer with JSON only."
    )


def cmd_llm(args):
    all_issues = json.load(open(LABELS))["all_issues"]
    df = pd.read_parquet(SAMPLE)
    if args.limit:
        df = df.head(args.limit)
    schema = {
        "type": "object",
        "properties": {"product": {"enum": PRODUCTS}, "issue": {"enum": all_issues}},
        "required": ["product", "issue"],
    }
    system = build_prompt(all_issues)
    rows, t0 = [], time.time()
    tok_in = tok_out = 0
    for i, r in enumerate(df.itertuples(), 1):
        payload = {
            "model": MODEL, "stream": False, "think": False, "format": schema,
            "options": {"temperature": 0, "num_ctx": 4096, "num_predict": 80},
            "messages": [
                {"role": "system", "content": system + "\nAllowed issues:\n- " + "\n- ".join(all_issues)},
                {"role": "user", "content": r.narrative},
            ],
        }
        s = time.time()
        try:
            resp = requests.post(f"{OLLAMA}/api/chat", json=payload, timeout=180).json()
            out = json.loads(resp["message"]["content"])
            pred_p, pred_i, err = out.get("product"), out.get("issue"), None
            tok_in += resp.get("prompt_eval_count", 0)
            tok_out += resp.get("eval_count", 0)
        except Exception as e:  # record failures, never drop rows
            pred_p = pred_i = None
            err = str(e)[:120]
        rows.append({"complaint_id": r.complaint_id, "pred_product": pred_p, "pred_issue": pred_i,
                     "seconds": time.time() - s, "error": err})
        if i % 25 == 0:
            print(f"{i}/{len(df)}  {time.time() - t0:6.0f}s  avg {(time.time() - t0) / i:.2f}s/item", flush=True)
    out_df = pd.DataFrame(rows)
    out_df.to_parquet(f"{DATA}/pred_llm.parquet")
    meta = {"model": MODEL, "items": len(out_df), "errors": int(out_df.error.notna().sum()),
            "total_seconds": round(time.time() - t0, 1), "prompt_tokens": tok_in, "completion_tokens": tok_out,
            "cost_usd": 0.0}
    os.makedirs(RESULTS, exist_ok=True)
    json.dump(meta, open(f"{RESULTS}/llm_run_meta.json", "w"), indent=2)
    print(meta)


def cmd_tfidf(_):
    import duckdb
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression

    con = duckdb.connect(DB, read_only=True)
    train = con.execute(f"""
        SELECT product, issue, narrative FROM analytics.fct_complaint
        WHERE entity_role IN {ENTITY_ROLES} AND has_narrative AND issue IS NOT NULL
          AND date_received BETWEEN '2024-01-01' AND '2026-02-28'""").df()
    train["narrative"] = train["narrative"].str.slice(0, MAX_CHARS)
    test = pd.read_parquet(SAMPLE)
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=3, max_features=200_000, sublinear_tf=True)
    xtr, xte = vec.fit_transform(train.narrative), vec.transform(test.narrative)
    preds = {}
    for col in ("product", "issue"):
        clf = LogisticRegression(max_iter=300, C=5.0)
        clf.fit(xtr, train[col])
        preds[f"pred_{col}"] = clf.predict(xte)
    pd.DataFrame({"complaint_id": test.complaint_id, **preds}).to_parquet(f"{DATA}/pred_tfidf.parquet")
    print(f"train {len(train):,} narratives; predicted {len(test)}")


def macro_f1(y, p, labels):
    from sklearn.metrics import f1_score
    return float(f1_score(y, p, labels=labels, average="macro", zero_division=0))


def cmd_report(_):
    from sklearn.metrics import classification_report, confusion_matrix

    os.makedirs(RESULTS, exist_ok=True)
    gold = pd.read_parquet(SAMPLE)[["complaint_id", "product", "issue"]]
    summary = {"held_out_month": "2026-05", "sample": len(gold), "systems": {}}
    for name in ("llm", "tfidf"):
        path = f"{DATA}/pred_{name}.parquet"
        if not os.path.exists(path):
            continue
        d = gold.merge(pd.read_parquet(path), on="complaint_id")
        d["pred_product"] = d["pred_product"].fillna("<none>")
        d["pred_issue"] = d["pred_issue"].fillna("<none>")
        sysrep = {}
        # product
        sysrep["product_macro_f1"] = macro_f1(d["product"], d["pred_product"], PRODUCTS)
        sysrep["product_accuracy"] = float((d["product"] == d["pred_product"]).mean())
        cm = confusion_matrix(d["product"], d["pred_product"], labels=PRODUCTS)
        pd.DataFrame(cm, index=[f"true: {p}" for p in PRODUCTS], columns=[f"pred: {p}" for p in PRODUCTS]) \
            .to_csv(f"{RESULTS}/confusion_product_{name}.csv")
        # issue, overall and per product (gold-product slice)
        labels = sorted(set(d["issue"]))
        sysrep["issue_macro_f1"] = macro_f1(d["issue"], d["pred_issue"], labels)
        sysrep["issue_accuracy"] = float((d["issue"] == d["pred_issue"]).mean())
        for prod in PRODUCTS:
            s = d[d["product"] == prod]
            ls = sorted(set(s["issue"]))
            sysrep[f"issue_macro_f1 | {prod}"] = macro_f1(s["issue"], s["pred_issue"], ls)
            sysrep[f"issue_accuracy | {prod}"] = float((s["issue"] == s["pred_issue"]).mean())
        rep = classification_report(d["issue"], d["pred_issue"], labels=labels, output_dict=True, zero_division=0)
        pd.DataFrame(rep).T.round(3).to_csv(f"{RESULTS}/issue_report_{name}.csv")
        top_conf = (d[d["issue"] != d["pred_issue"]].groupby(["issue", "pred_issue"]).size()
                    .sort_values(ascending=False).head(15).reset_index(name="n"))
        top_conf.to_csv(f"{RESULTS}/issue_top_confusions_{name}.csv", index=False)
        sysrep["parse_failures"] = int((d["pred_product"] == "<none>").sum())
        summary["systems"][name] = {k: round(v, 4) if isinstance(v, float) else v for k, v in sysrep.items()}
    json.dump(summary, open(f"{RESULTS}/classify_baseline.json", "w"), indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("sample")
    p = sub.add_parser("llm")
    p.add_argument("--limit", type=int)
    sub.add_parser("tfidf")
    sub.add_parser("report")
    a = ap.parse_args()
    {"sample": cmd_sample, "llm": cmd_llm, "tfidf": cmd_tfidf, "report": cmd_report}[a.cmd](a)
