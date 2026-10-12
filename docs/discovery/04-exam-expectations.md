# 04 — What a "good" complaint management system must do (exam expectations)

Desk-research note 4 of 6 (`W1-DR-01`). Sources: CFPB Supervision and Examination Manual, OCC Comptroller's
Handbook, Federal Reserve Consumer Compliance Handbook. Customer SIMULATED.

## Sources

- CFPB **Supervision and Examination Manual** (consumerfinance.gov), incl. the "Compliance management review —
  examination procedures" chapter (updated Aug 2017; manual Version 2, 924 pp.).
- OCC **Comptroller's Handbook, "Compliance Management Systems"** booklet (June 2018; occ.gov).
- Federal Reserve **Consumer Compliance Handbook** (federalreserve.gov, 499 pp.) — the companion examiner
  reference.
- Law-firm and advisory summaries of exam preparation (Venable; Bridgeforce, Apr 2025).

## The expected system, synthesized

Both the CFPB and OCC frames converge on the same structure:

1. **Board and management oversight** — governance, accountability, reporting on compliance (and complaint)
   performance upward.
2. **Compliance program** — policies, procedures, training, monitoring/testing, and a **consumer complaint
   response** program as a named component.
3. **Complaint response, as examiners assess it:** track complaints; investigate and resolve; **respond within
   the portal/regulatory clocks**; and — the differentiating expectation — **use complaint data to identify
   systemic issues, drive root-cause analysis, and feed corrective action**. Complaints are treated as an
   *early indicator of control weakness*: a complaint program that closes cases but never surfaces root causes
   is itself a finding.
4. CFPB added an **information technology** section to the CMS review in 2021 (compliance systems and data
   lineage are now in scope).

Escalation path: CMS deficiencies observed in exam can be referred to enforcement (Venable's exam-survival
summary) — note 03's consent orders are where this ends up.

## What it means for Complaint Intelligence

The flagship maps cleanly onto the examiner's checklist, which is the strongest available proxy for what the
simulated customer is measured on:

| Exam expectation | Flagship feature |
|---|---|
| Track, investigate, resolve | Ontology `Complaint` objects; Workshop queue; Escalate/Assign/Mark-reviewed **actions** (every write logged — the audit trail examiners ask for) |
| Respond within clocks | Regulation mapping cites 1005.11 / 1026.13 / 1030 with the deadline each triggers |
| Identify systemic issues from complaint data | Spike detection vs trailing baseline and peers |
| Root cause → corrective action | Issue/sub-issue rollups linked to `Institution` + `Regulation Section` objects; action log as corrective-action evidence |
| Oversight reporting | The persona's weekly volume/timeliness/emerging-issue pack becomes a query, not a scramble |

- **Boundaries re-confirmed:** exam materials describe the *institution's* obligations — our system ranks,
  cites, and proposes; the human decides (per `docs/00-brief.md` out-of-scope). The agent must never be
  positioned as making legal determinations; eval questions should be phrased as analyst-support.
- **Demo framing for the simulated stakeholder:** "when the examiner asks to see your complaint program, this
  is the system view: intake to root cause, every write logged."
- **Ontology design nudge:** an `owner` property on Complaint (already planned) matches the accountability
  expectation; a corrective-action link from complaint clusters would match it fully.

## Limits

Synthesized from handbook structure and secondary summaries, not a clause-by-clause read of the 924-page
manual; the June 2018 OCC CMS booklet is the current cited version but booklet dates should be re-checked
before the case study quotes them.
