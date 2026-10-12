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
| 12 | **Merged charter still used as a CFPB company name.** FDIC closed Discover Bank (cert 5649) on 2025-05-18 (merged into Capital One), but CFPB keeps filing complaints under "DISCOVER BANK" through 2026. | Discover in scope: 6,834 rows, ~270/month both before and after the merger | **Fix** with a date-aware mapping (`valid_from` / `valid_to` in `pipelines/seeds/entity_map_seed.csv`): pre-merger rows map to 5649, later rows roll up to Capital One (4297). Discover leaves the peer set; TD Bank replaces it. |
| 13 | **One CFPB name, two FDIC charters.** "TD BANK US HOLDING COMPANY" owns TD Bank N.A. (18409, deposits) and TD Bank USA N.A. (33947, store cards). The complaint does not say which. | 6,566 rows | **Map to 18409** and note the ambiguity; a product-aware rule (card to 33947) is a possible v2 test case for entity matching. |
| 14 | **FDIC record missing the holding company.** Comenity Capital Bank (Bread Financial's charter) has an empty `NAMEHCR`, so name-to-holding-company matching can't find it. | 8,226 Bread rows | **Fix** with a manual seed row; add to the 100 hand-labeled pairs as a hard case. |

## Implications for the week

- Customer + 10 peers come from FDIC-insured banks only (issues 4, 5, 12-14).
- Held-out month for the classifier: one of Apr-Jun 2026 (issue 2).
- Backtest labels: "Closed with monetary relief" or "Closed with non-monetary relief", windows ending Jun 2026 (issue 3).

## Customer and peers (decided 2026-10-12)

Customer: **Bank of America, N.A.** (cert 3510). Peers, the next 10 FDIC-insured banks by in-scope volume:
Capital One (4297, incl. Discover after 2025-05-18), JPMorgan Chase (628), Citibank (7213), Wells Fargo (3511),
Synchrony (27314), American Express (27471), U.S. Bank (6548), Goldman Sachs Bank USA (33124),
Comenity Capital / Bread (57570), TD Bank (18409).

Excluded: credit bureaus, Navy Federal (NCUA-insured credit union), fintechs and processors (issues 4, 5).

First benchmark (`pipelines/peer_benchmark.py`, Jan 2024 to Jun 2026, FDIC average assets over the same quarters):

| Bank | Complaints | Per $1B assets | % closed with relief |
|------|-----------:|---------------:|---------------------:|
| Comenity Capital (Bread) | 7,639 | 584.1 | 52.0 |
| Synchrony | 17,201 | 152.4 | 24.0 |
| Capital One | 38,840 | 69.1 | 18.2 |
| American Express | 12,581 | 62.4 | 23.1 |
| TD Bank | 6,059 | 16.7 | 36.5 |
| Citibank | 29,724 | 16.6 | 48.2 |
| Wells Fargo | 27,125 | 15.4 | 20.4 |
| Goldman Sachs | 8,003 | 13.0 | 27.5 |
| U.S. Bank | 8,103 | 12.1 | 29.6 |
| **Bank of America (customer)** | **27,041** | **10.4** | **42.5** |
| JPMorgan Chase | 35,676 | 9.7 | 16.0 |

Read with care: per-asset rates favor big universal banks and punish card monolines (Comenity, Synchrony).
The customer's story is the relief rate: second-lowest complaint rate, but 42.5% closed with relief against a
peer median of about 25%. That supports a triage hypothesis: many of its complaints are valid, so ranking
the likely-relief ones first has real value.
