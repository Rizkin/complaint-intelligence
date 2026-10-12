# Brief: Complaint Intelligence

Self-directed project on public data. The customer below is **SIMULATED**: no one at Bank of America was
interviewed or involved. The persona is built from public sources (`docs/discovery/README.md`).

## Persona

**Head of Complaints Triage, consumer deposits and cards, Bank of America, N.A.** (simulated).
Runs a team of analysts who work the complaints the CFPB routes to the bank, plus a few senior reviewers who
handle anything with regulatory or legal exposure. Reports weekly to Compliance on volumes, timeliness and
emerging issues.

## The daily decision

Every morning, for the complaints that arrived yesterday:

1. **Which ones go to a senior reviewer?** Senior time is scarce. Complaints that end in monetary or
   non-monetary relief are the ones where the bank got something wrong, and these are the ones to see first.
2. **Which regulation does each one touch?** Unauthorized debit transfers and other electronic fund transfer
   errors fall under Reg E (12 CFR 1005.11: investigate within 10 business days or give provisional credit,
   up to 45 days). Credit card billing errors fall under Reg Z (12 CFR 1026.13: acknowledge within 30 days,
   resolve within two billing cycles). Deposit account disclosures and fees fall under Reg DD (12 CFR 1030).
   Missing the clock is itself a finding.
3. **Which issue is spiking?** A jump in one issue (for example "Problem with a purchase shown on your
   statement") against the trailing baseline and against peers is an early signal of a process or system failure.

## Why this customer

From `docs/01-data-quality.md`, Jan 2024 to Jun 2026, checking/savings and credit card only:

- 27,041 complaints, balanced across checking (Reg E, Reg DD) and cards (Reg Z).
- **10.4 complaints per $1B of assets**, second-lowest of 11 large banks.
- But **42.5% closed with relief**, against a peer median of about 25%.

A low complaint rate with a high relief rate means a large share of the complaints are valid. Finding those
early is the triage problem worth solving.

## Hypotheses (all UNVALIDATED)

| # | Hypothesis | How it gets tested | By |
|---|------------|--------------------|----|
| H1 | **UNVALIDATED.** A risk score using only fields known on arrival day (product, issue, sub-issue, tags such as Older American or Servicemember, channel, narrative present) puts at least 2x as many later-relief complaints in each day's top 50 as random ordering. | Triage backtest, replayed days, Jan 2024 to Jun 2026 | Fri Oct 16 |
| H2 | **UNVALIDATED.** Consumer-chosen product and issue labels are wrong often enough (at least 10%) that a narrative classifier is worth having, and a small local model reaches a useful macro-F1 against audited labels. | 200-complaint hand audit; `evals/classify.py` on a held-out month (Apr to Jun 2026) | Thu Oct 15 |
| H3 | **UNVALIDATED.** Most relief-bearing complaints map to a small set of deadline-bound sections (Reg E 1005.11, Reg Z 1026.13), so citing the section helps the reviewer act inside the regulatory clock. | 60-item regulation golden set; citation precision | Mon to Tue Oct 19 to 20 |

## Success metrics

| Metric | Target | Source |
|--------|--------|--------|
| Data reconciles | Row counts match every export; 30-day replay with no manual fixes | Week 1 gate |
| Entity matching | Precision at least 0.95, recall at least 0.90 on 100 hand-labeled pairs | Week 1 gate |
| Triage lift | Share of later-relief complaints in the daily top 50, versus random | H1 |
| Classifier | Macro-F1 per product, against both consumer labels and the audited subset | H2 |
| Regulation citations | Precision at least 0.85 on 60 items; every cited section supports its claim | H3, Week 2 gate |
| Analyst agent | At least 75% of 40 questions; judge agrees with my grades at least 85% of the time | Week 2 gate |
| Cost | Under $1 per eval run; cloud at or under $10 | Plan budget |

## Out of scope

- Real bank data, internal case notes or any non-public information.
- Responding to consumers or making legal determinations. The system ranks, cites and proposes; a person decides.
- Products other than checking/savings and credit cards; complaints before 2024.
- Credit bureaus, credit unions and fintechs as customers or peers (they stay in market-wide spike counts).
- Un-masking redacted (`XXXX`) narrative text, ever.
