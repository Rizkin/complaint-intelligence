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
