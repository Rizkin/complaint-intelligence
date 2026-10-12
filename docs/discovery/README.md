# Discovery: desk research, no outreach

Decision (2026-10-12): no discovery calls. Customer understanding comes from public sources,
and every stakeholder session is labeled SIMULATED. This is the plan's own fallback (risks table, page 26).

## Sources (all public)

| # | Source | What it tells you | Output file |
|---|--------|-------------------|-------------|
| 1 | CFPB complaint data: `company_response`, `timely`, narratives | The customer's voice; which issues get relief; how banks respond | `01-voice-of-customer.md` |
| 2 | Job postings for "complaints analyst", "complaint management", "disputes analyst", "Reg E specialist" at US banks (LinkedIn, Indeed) | Real daily workflow, tools, SLAs, escalation rules | `02-job-posting-workflow.md` |
| 3 | CFPB Supervisory Highlights and enforcement actions / consent orders on complaint handling and Reg E disputes | What goes wrong and what regulators penalize | `03-regulator-findings.md` |
| 4 | CFPB Supervision and Examination Manual (compliance management, complaint response); OCC Comptroller's Handbook | What a "good" complaint management system must do | `04-exam-expectations.md` |
| 5 | Big-bank 10-K risk factors and annual reports mentioning complaints / CFPB | How leadership talks about complaint risk | `05-bank-disclosures.md` |
| 6 | Public talks, blogs and forums by compliance practitioners | Pain points in their own words | `06-practitioner-voice.md` |

## Simulated stakeholder sessions

Two recorded sessions with an LLM playing a skeptical Head of Complaints, grounded in sources 1-4.
Every transcript and every mention in the case study says SIMULATED.

- `sim-01-head-of-complaints.md` (Week 1, replaces discovery call 1)
- `sim-02-head-of-complaints.md` (Week 2, replaces discovery call 2; the Oct 24 mock review is a third)

## How to describe it

"Customer discovery was desk research on public regulator material, job postings and the complaint data itself,
plus two simulated stakeholder sessions. No real customer was interviewed."
