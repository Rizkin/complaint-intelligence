# Data quality: CFPB exports 5-21

Loaded 2026-10-12 with `pipelines/load_raw.py` into `data/cfpb.duckdb` (`raw_complaints`, all VARCHAR).
Profile queries: `pipelines/profile_raw.py`.

## Load reconciliation

17 exports, 13,495,502 rows. Every export's DuckDB row count equals an independent Python `csv` row count
(`load_audit` table, 0 mismatches). All 16 headers identical across exports.

**Scope** (plan: checking/savings + credit card, received 2024-01-01 onward): **428,203 complaints**
(credit card 230,833, checking or savings 197,370). That is 3.2% of 2024+ volume; credit reporting is 88.9%.

## Issues

| # | Issue | Count (in scope unless noted) | Decision |
|---|-------|-------------------------------|----------|
| 1 | **Archive tail has no narratives.** Archive says "through Aug 14, 2026", but rows run to Aug 31. Rows dated Aug 15-31 have 0% narratives. | 8,518 rows | **Flag** `post_cutoff`. Keep for volume/spike metrics, exclude from every narrative task. |
| 2 | **Narrative coverage decays at the end.** Monthly share with narrative: ~55% in early 2024, 28% Feb 2026, 24% Jul 2026, 0% Aug 2026. Overall 47.6% before Aug 15. | 419,685 rows pre-cutoff, 47.6% with narrative | **Flag** `has_narrative`. Pick the held-out classifier month from Apr-Jun 2026 (40-46% coverage), not Jul/Aug. |
| 3 | **Outcomes are right-censored.** `company_response = 'In progress'` jumps to 9.9% in Jul 2026 and 36.6% in Aug 2026. | 7,430 rows | **Flag**. Exclude from the triage backtest label; backtest window ends Jun 2026. |
| 4 | **Credit bureaus filed under "Credit card".** Equifax, TransUnion and Experian are the 8th, 9th and 11th biggest "credit card" companies. | 47,568 rows (11.1% of scope) | **Drop** from the bank scope: not banks, no FDIC certificate, and relief rates (4% to 85%) behave nothing like banks. |
| 5 | **Non-bank companies in bank products.** Credit unions (Navy Federal: NCUA, not FDIC), fintechs and processors (Chime, Block, PayPal, Robinhood, Early Warning/Zelle, FIS, Credit Karma). | Navy Federal alone 18,801; top-40 non-banks ~40k | **Flag** `entity_type`. Out of the customer + peer set; keep for market-wide spike detection. |
| 6 | **Company names mix holding companies and bank charters.** "JPMORGAN CHASE & CO." and "CAPITAL ONE FINANCIAL CORPORATION" are holding companies; "BANK OF AMERICA, NATIONAL ASSOCIATION" and "CITIBANK, N.A." are charters. FDIC certificates belong to charters. | 1,056 distinct company names | **Fix** with the entity-matching table (CFPB name to FDIC cert, Tue Oct 13), measured on 100 hand-labeled pairs. |
| 7 | **PII redaction.** Narratives use `XXXX` / `XX/XX/XXXX`; some ZIP codes are masked as `123XX`. | 156,249 narratives with XXXX; 64,770 masked ZIPs | **Keep as-is.** Never un-mask. Guardrail test (Fri Oct 23) asserts XXXX survives every transform and log. |
| 8 | **No duplicates and no overlap between exports.** Each export covers a clean, non-overlapping date range and `complaint_id` is unique across all 13.5M rows. | 0 duplicate IDs | **No-op today**, but the replay loader still upserts on `complaint_id` so reruns are idempotent. Stated honestly in the case study: dedupe was built, not needed on this archive. |
| 9 | **Sparse optional fields.** `tags` 97% empty (empty means "no tag", not missing); `company_public_response` 43% empty; `sub_issue` 1.6% empty. | see profile | **Keep**. Empty `tags` maps to `none`; don't treat as missing data. |
| 10 | **Volume is rising.** In-scope complaints/month go from ~9k (Jan 2024) to ~15.5k (2026). | 32 months | **Fix** in metrics: spike detection uses rates vs a trailing baseline, and "complaints per $1B assets" uses FDIC assets. |
| 11 | **Schema narrower than the live database.** The archive has 16 columns; the consent and "consumer disputed" fields of the public CCDB are not present. | 16 columns | **Note**. Nothing to fix; don't design features around those fields. |

## Implications for the week

- Customer + 10 peers come from FDIC-insured banks only (issues 4, 5).
- Held-out month for the classifier: one of Apr-Jun 2026 (issue 2).
- Backtest labels: "Closed with monetary relief" or "Closed with non-monetary relief", windows ending Jun 2026 (issue 3).
