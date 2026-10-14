# Entity matching: human review notes (2026-10-15)

## Definition used

A CFPB company **matches** an FDIC institution only if the company **is** that bank or **owns** it (holding company or direct bank subsidiary).

Not matches, because the bank's assets say nothing about the company's complaint load (the benchmark divides complaints by assets):

- **Sponsor/partner banks** of fintechs and lenders (the fintech is not the bank),
- **minority equity** stakes,
- **sister companies** (a broker-dealer next to a bank),
- **international banks** with no FDIC certificate.

Credit unions are NCUA-insured, so they have no FDIC match.

## Merged charters: CFPB keeps the old name

Date-aware overrides in `pipelines/dbt/seeds/entity_overrides.csv` (same pattern as Discover Bank -> Capital One):

| CFPB company | Charter (cert) | Ended |
|---|---|---|
| Synovus Bank | 873 | 2026-01-02 |
| Comerica | 983 | 2026-02-01 |
| Webster Bank, N.A. | 18221 | 2026-08-20 |
| Sandy Spring Bancorp | 4865 | 2025-04-01 |
| Pacific Premier Bancorp | 32172 | 2025-09-01 |
| Independent Bank Group (-> SouthState Bank N.A. 33555) | | 2025-01-01 |
| New York Community Bancorp (-> Flagstar Bank N.A. 32541) | | rename Oct 2024 |

Lesson for the matcher: candidates must include **recently ended** charters, not only active ones.

## Partner/affiliate relationships (user-provided research, NOT verified by me, NOT used in matching)

Kept as notes for a possible bank-affiliation graph; each is a product or financing relationship, not ownership.

| CFPB company | Related bank(s) | Relationship |
|---|---|---|
| Atlanticus | The Bank of Missouri (1617), WebBank (34404) | credit-origination partners |
| Continental Finance | The Bank of Missouri (1617), Celtic Bank (57056) | card issuers |
| Avant | WebBank (34404) | originates Avant-branded credit |
| OneMain | WebBank (34404) | issuer of OneMain cards |
| Gemini / Winklevoss Exchange | WebBank (34404) | Gemini credit card |
| Albert | Stride Bank (4091), Coastal Community Bank | banking and savings partners |
| Upstart | Cross River Bank (58410), FinWise Bank | lending partners |
| Enova | Capital Community Bank (33823), Republic Bank & Trust (23627) | NetCredit partners |
| Fold | Lead Bank (8283), Sutton Bank (5962), Celtic Bank (57056) | account, prepaid, credit card |
| PLS Group | The Bancorp Bank (35444) | prepaid card program |
| Populus Financial | Pathward (30776) | prepaid/Porte/Flare partner |
| Bright Capital / Bright Money | Evolve Bank & Trust (1299), Continental Bank (57571) | deposit partners |
| CapitalJ / Juno | Evolve (1299) | former partner |
| Resurgent Capital Services | Credit One Bank (25620) | historical; current ownership conflicting |
| CL Holdings | Citizens Bank (57958) | credit-facility agent |
| Mitsubishi HC Capital (USA) | MUFG Bank, Ltd. (Japan, no FDIC cert) | minority equity (3.5% + 14.48%) |
| Florida Home Trust Mortgage | FACEBANK International (Puerto Rico) | parent, not FDIC-insured |
| Western Union | Western Union International Bank GmbH (Austria), Banco WU do Brasil | foreign bank subsidiaries, no FDIC cert |

## Owned-bank matches added (Block)

Block, Inc. -> Square Financial Services (59177), an FDIC-insured industrial bank it owns. Most Cash App complaints are **not** about that bank, so it must not
be used as a complaints-per-assets denominator.

## Name collisions rejected (matcher false positives)

Morgan Stanley & Co. LLC (broker-dealer), Halsted Financial (collector), Bridge IT / Brigit (fintech), Lincoln Financial (insurer), Heartland Financial USA
(acquired by UMB 2025), First Credit Corporation, Devon Financial Services, People Trust (CDFI), Barker Financial, National Commercial Services, United Shore
Financial Services, Clayton Holdings, AmeriFirst Financial.

## Results (human verdicts are the gold; ownership-only unless stated)

| Matcher | Test set | Precision | Recall | Notes |
|---|---|---:|---:|---|
| v1 (active charters, loose fuzzy rule) | 100 pairs | 0.787 | 0.822 | complaint-weighted 0.928 / 0.841. Gate (0.95 / 0.90) not met |
| v2 algorithm only (ended charters + acceptance rules) | same 100 pairs | 0.921 | 0.833 | **development check**: rules were tuned after seeing these errors; the 100 are also baked into the overrides |
| **v2 with overrides** | **fresh 50 pairs** (not seen when the rules were written) | **0.900** (18/20) | **0.947** (18/19) | complaint-weighted 0.999 / 0.9996. Recall passes, precision misses by one error |
| v2.1 algorithm only (+ state-conflict rule) | same fresh 50 | 0.947 (18/19) | 0.947 | **post-hoc**: the rule was added after seeing these errors, so this is not a clean test. Needs a new sample |
| v2.2 algorithm only (+ 'National Association' suffix, + name-only match for banks >= $5B) | dev 100 / same fresh 50 | 0.925 / 0.947 | 0.841 / 0.947 | **post-hoc**: found while wiring into dbt (Citibank N.A., Santander Holdings USA were wrongly rejected by v2). Dev-100 and fresh-50 both unchanged or slightly better |

Fresh-50 errors: River Financial Inc (name shared by a Bitcoin fintech and an Alabama bank holding company, 2 complaints) and First Bancorp North Carolina
(fuzzy hit on a South Carolina bank; fixed by the state rule and by an override).

Small-sample caveat: 20 predicted matches mean one error moves precision by 5 points. Treat 0.90 to 0.95 as "near target", not as a precise measurement.

## What the matcher can and cannot do

- Does well: exact bank names, holding-company names, big banks, obvious non-banks.
- Needs overrides: mergers and renames (candidate list now includes charters ended since 2023-12-31, but successor links are manual), parent chains with no FDIC
  holding-company record (HSBC, BMW, Bread, NYCB -> Flagstar), and name collisions between unrelated companies.
- The production table is `entity_match` (algorithm + 33 overrides in `pipelines/dbt/seeds/entity_overrides.csv`); `entity_match_core` is the algorithm alone.

## Wired into dbt (2026-10-15)

Order: `fetch_fdic_all.py` -> `make_entity_overrides.py` -> `entity_match.py` -> `dbt build` (use `--full-refresh` when the entity mapping changes: `fct_complaint` is incremental).

| dbt object | Role |
|---|---|
| `entity_overrides` (seed) | human-reviewed, dated rows |
| `stg_entity_match_core`, `stg_fdic_all_institutions` | staging of the matcher output and the FDIC candidate file |
| `int_company_entity` | company-level, date-aware: overrides first, algorithm for the rest |
| `int_complaint_entity` | per complaint: curated seed (customer/peer/peer_history) > exclusions (bureau, credit union, fintech, processor) > matcher (`other_bank`) > `non_bank` |
| `dim_institution` | every matched bank (137 certs), not only the customer and 10 peers; size from FDIC financials where pulled, else the institution file |
| tests added | no overlapping override dates; every override cert exists in FDIC; no complaint dropped or duplicated; no `unmapped` role |

Effect on complaints (428,172): the former `unmapped` 85,500 became `other_bank` 51,646 (125 certs) and `non_bank` 33,854. The customer, peer, peer_history,
credit_bureau, fintech, credit_union and processor counts are identical to before; 54 of 54 dbt tests pass; incremental `fct_complaint` equals a full rebuild.

Known leftovers (low volume, left for a human override rather than guessed): Provident Financial Services (29) and Nelnet Inc (21) are real bank owners the name
rules still reject; Synovus Bank complaints after 2026-01-02 have no successor row.

