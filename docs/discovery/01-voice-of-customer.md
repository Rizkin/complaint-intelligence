# 01 — Voice of the customer (from the complaint data itself)

Desk-research note 1 of 6 (`W1-DR-01`). The customer is **SIMULATED** (Bank of America, N.A.; see `docs/00-brief.md`).
This note is grounded in the project's own data, not external claims.

## Method

Streamed `CCDB_Export_13_September_2025_through_October_2025.zip` directly from `data/raw/cfpb` (Python stdlib,
no DuckDB — reproducible on any machine with the raw zips). Filter: products credit card + checking/savings,
company contains "BANK OF AMERICA". Outcomes are mature for this window (closed by extraction date).

- Export total: 1,023,636 rows → in scope: 28,366 → **Bank of America: 1,783**

## What the data says (Sep–Oct 2025, BofA, in scope)

**Response mix** (the simulated customer's own outcome distribution):

| Company response | Count | Share |
|---|---:|---:|
| Closed with explanation | 1,060 | 59.4% |
| Closed with monetary relief | 650 | 36.5% |
| Closed with non-monetary relief | 73 | 4.1% |
| **Any relief** | **723** | **40.6%** |

Consistent with the Jan 2024–Jun 2026 benchmark in `docs/01-data-quality.md` (42.5% relief vs peer median ~25%).
Monetary relief outnumbers non-monetary ~9:1.

**Timeliness:** 1,775 of 1,783 "timely" (99.55%). Timeliness on the CFPB channel is table stakes, not a
differentiator. The clocks that actually bite are the internal regulatory ones (below).

**Relief concentrates by issue** (arrival-day fields, which is exactly what H1 needs):

| Issue | Total | With relief | Relief rate |
|---|---:|---:|---:|
| Problem with a purchase shown on your statement | 264 | 158 | **59.8%** |
| Problem with a lender or other company charging your account | 165 | 71 | 43.0% |
| Managing an account | 621 | 246 | 39.6% |
| Closing an account | 153 | 71 | 46.4% |
| Fees or interest | 46 | 26 | 56.5% |
| All BofA in scope | 1,783 | 723 | 40.6% |

Product split: checking/savings 1,118 (40.0% relief), credit card 665 (41.5%) — relief is not a cards-only story.

**The voice, verbatim** (narratives as published; `XXXX` redactions intact; never un-mask):

1. Check holds → monetary relief. *"Deposited 3 separate checks on XX/XX/XXXX. They sent me an email saying
   funds will be available the XXXX, and they did. Then backtracked and withdrew the cleared funds only to put
   another 8 day hold… I have been with this bank ( Bank of America ) twelve years"* (Managing an account /
   Deposits and withdrawals).
2. Card fraud dispute, declined twice, then relief. *"I had fraud charges on XX/XX/XXXX XX/XX/XXXX totalling
   {$9700.00}… 60 charges made over the 2 days… This activity does not follow the pattern of my purchase
   history… This claim has been declined twice by Bank of America despite the hours I have spent"* (Problem
   with a purchase shown on your statement) — a Reg Z 1026.13 billing-error pattern that the bank eventually
   paid on.
3. Unauthorized withdrawals. *"There were unauthorized transactions from my bank of America XXXX account…
   {$990.00} went thu. But the last two were stop"* (Managing an account / Banking errors) — Reg E 1005.11
   territory.
4. Autopay usability. *"BoA app will not allow me to add thr card as a payee at all… I believe they make it
   difficult to pay in order to delay payments and earn more interest"* (Problem when making payments) —
   closed with explanation only; product-experience, not a deadline case.
5. Abrupt account closure. *"Bank of America closed my long-standing credit account without prior notice or
   valid justification… may violate the Fair Credit Reporting Act ( FCRA )"* (Incorrect information on your
   report) — consumer cites the statute themselves.

## What it means for Complaint Intelligence

- **H1 gets direct support:** the consumer-chosen issue label alone separates relief rates (59.8% vs 40.6% vs
  39.6%). An arrival-day risk score should upweight dispute/authorization and fee issues. Still UNVALIDATED
  until the backtest runs.
- **H3 gets texture:** the relief-heavy narratives are deadline-bound error-resolution cases (funds
  availability, unauthorized transfers, billing disputes) — Reg E 1005.11 / Reg Z 1026.13 / Reg DD 1030. The
  60-item golden set should include near-verbatim versions of patterns 1–3 above.
- **H2 scope note:** narratives exist for ~47.6% of pre-cutoff in-scope rows market-wide
  (`docs/01-data-quality.md` issue 2); the classifier only ever applies to that subset. Sampled narratives are
  messy (typos, formatting), which is realistic input for a small local model.
- **Product shape:** the top of the ranking will be dominated by "Managing an account" (35% of volume) while
  the *precision* play is in dispute-flavored issues; the Workshop queue should show both count and relief-rate
  context per issue. Timeliness is not worth modeling; relief is.

## Limits

One export (Sep–Oct 2025), one bank, outcomes as-recorded by the company via the portal (no ground truth on
whether relief was warranted). Narrative quotes are illustrative, not a statistically drawn sample.
