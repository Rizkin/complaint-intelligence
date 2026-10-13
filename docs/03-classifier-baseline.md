# Classifier baseline (v0, zero-shot local model)

Task: given a consumer complaint narrative, predict the CFPB **product** (2 classes in scope) and **issue** (24 labels in the
2024-01 to 2026-02 training window). Labels are what the consumer chose at filing, so they are noisy (see the audit below).

## Setup

| Item | Value |
|------|-------|
| Held-out month | 2026-05 (3,739 bank-scope complaints with narratives; coverage ~40%, before the narrative cutoff decay) |
| Sample | 600, stratified 300 per product, seed 42, narrative cut at 1,500 chars |
| System | `qwen3.5:2b` through Ollama on the RTX 3050 (4 GB), temperature 0, thinking off, JSON-schema constrained output (every label is valid) |
| Prompt | one system prompt: task, product list, one combined allowed-issue list, "ignore XXXX redaction" |
| Run | 600 items, 0 errors, 931 s (1.55 s per item), 285,737 prompt tokens, 16,348 completion tokens, $0 |
| Code | `evals/classify.py` (`sample`, `llm`, `tfidf`, `report`), `evals/llm_docker.sh`, results in `evals/results/` |

The LLM step runs in a Docker container because the Windows Ollama listens on its own loopback: WSL cannot reach it, a container can
(`--add-host=host.docker.internal:host-gateway`).

## Results (held-out 2026-05, n = 600)

| Metric | LLM zero-shot v0 |
|--------|-----------------:|
| Product macro-F1 | **0.861** |
| Product accuracy | 0.862 |
| Issue macro-F1 (24 labels) | **0.122** |
| Issue accuracy | 0.143 |
| Issue macro-F1, checking/savings only | 0.100 (accuracy 0.080) |
| Issue macro-F1, credit card only | 0.173 (accuracy 0.207) |

Product confusion (rows true, columns predicted):

| | pred checking/savings | pred credit card |
|---|---:|---:|
| true checking/savings | 272 | 28 |
| true credit card | 55 | 245 |

Per-class issue report: `evals/results/issue_report_llm.csv`. Top issue confusions: `evals/results/issue_top_confusions_llm.csv`.

## Top 3 failure patterns

1. **Issues from the wrong product (26.7% of predictions).** 160 of 600 predicted issues are not valid for the product the model itself predicted
   (e.g. "Closing your account", a card label, on a checking complaint). One shared label list invites this. Restricting the issue list to the predicted
   product is a one-line change and the first fix to try.
2. **Two attractor labels swallow the distribution.** "Problem with fraud alerts or security freezes" is predicted for 24.8% of complaints and "Problem caused by
   your funds being low" for 22.7%, against gold shares of well under 5% each. The vague, common label "Managing an account" (28.0% of gold) is almost never predicted;
   the top confusions are Managing an account -> fraud alerts (50 times) and -> funds being low (47). The model matches literal keywords ("fraud", "unauthorized", "low balance")
   instead of the CFPB taxonomy. Fix candidates: short label definitions with a "default to the broad label" rule, a few shots per label, a two-stage prompt.
3. **Product mistakes are mostly card complaints read as checking (55 of 83 errors, 13.8% overall).** Many mention "my bank account" or a bank name. Several
   look like consumer mis-filing rather than model error, which is what the 200-complaint audit measures; it caps the macro-F1 any model can reach against these labels.

## Reading the numbers

- Product at 0.86 is usable as a first routing signal; issue at 0.12 is not. A 2B zero-shot model with a flat 24-label list is the floor, which is the point of a baseline.
- The consumer-chosen issue is itself ambiguous (a fraud claim filed as "Managing an account"). Expect the achievable ceiling on issue to be well below 1.0 even with a perfect model.

## Next

- [ ] TF-IDF + logistic regression reference (same sample): numbers below once finished.
- [ ] 200-complaint hand audit of the held-out month -> label-noise estimate; re-score against the audited subset and report both numbers (plan risk row 3).
- [ ] Improvement cycle (Week 2): product-conditioned issue list, label definitions, few-shot; re-measure on the same 600.
