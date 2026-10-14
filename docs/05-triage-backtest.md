# Triage backtest v0

**Question (hypothesis H1 in `docs/00-brief.md`, UNVALIDATED at the time):** if each arrival day's complaints are ranked by a risk score that uses only
fields known on arrival, how many of the complaints that later close **with relief** land in the day's top 50, versus random?

## Setup

| Item | Value |
|------|-------|
| Population | bank-scope complaints (customer + 10 peers), checking/savings and credit card, mean 253 per day |
| Window | 2024-07-01 to 2026-06-30, 730 arrival days with at least 50 complaints and one relief outcome |
| Label | `got_relief` = closed with monetary or non-monetary relief; complaints still "In progress" excluded; window ends 2026-06-30 (later outcomes right-censored) |
| Base rate | 28.7% of complaints end with relief (mean over days) |
| Features (all known on arrival) | product, sub-product, issue, sub-issue, bank (FDIC cert), tags (Older American, Servicemember), channel, has narrative, narrative length bucket |
| Not used | `company_response`, `timely_response`, public response, anything after arrival |
| Leakage control | each month's model trains only on complaints that arrived at least 60 days before the month starts |
| K | 50 per day |
| Systems | `random`; `issue_rate` (historical relief rate of the complaint's issue); `logreg` (one-hot features, logistic regression, refit monthly) |

## Results (mean over 730 days, bootstrap 95% CI over days)

| System | Precision@50 | Lift vs base rate | Recall@50 |
|--------|-------------:|------------------:|----------:|
| random | 0.282 [0.277, 0.287] | 0.98x | 0.239 [0.230, 0.248] |
| issue_rate | 0.380 [0.374, 0.386] | 1.35x | 0.316 [0.305, 0.327] |
| **logreg** | **0.500 [0.493, 0.506]** | **1.78x** | **0.406 [0.395, 0.418]** |

- The linear score beats the day's base rate on **100% of days** (issue-rate rule: 92%).
- In plain terms: out of 50 complaints picked per day, about 25 end with relief, versus about 14 at random. A reviewer working the top 50 catches 41% of the
  day's relief cases while reading 20% of the volume.
- Random recall (0.239) is above 50/253 = 0.197 only because days with fewer than 50 complaints were excluded; compare systems, not to the theoretical.

## Verdict on H1

H1 asked for **at least 2x** the random count in the top 50. v0 reaches **1.78x** (precision 0.50 vs 0.28), so **H1 is not met at v0**; it is close and the model is
deliberately simple. Reported as measured, not rounded up.

## What to try next (cheap, in this order)

1. Add the narrative: TF-IDF of the text is known on arrival (it is not an outcome). The classifier work showed text carries a lot of signal.
2. Bank-level history as a feature (each bank's trailing relief rate, computed with the same 60-day gap).
3. Interactions (issue x bank, product x tags) or a gradient-boosted model.
4. Regulation triggers from the decision model (Reg E "unauthorized transaction", Reg Z "billing error") as features, once the 60-item golden set exists.

## Caveats

- Relief is a noisy proxy for "needed a senior reviewer": it measures the bank's own decision, including policy changes over time.
- Top-50 of ~253 is 20% of the day. For the customer bank alone (~30 complaints a day) the equivalent is top 6; not run in v0.
- The 60-day gap is conservative; it costs some early-window accuracy and removes outcome leakage.

Code: `evals/triage_backtest.py`. Results: `evals/results/triage_backtest_v0.json`, `triage_backtest_v0_per_day.csv`.
Reproduce: `uv run python evals/triage_backtest.py` (about 45 s).
