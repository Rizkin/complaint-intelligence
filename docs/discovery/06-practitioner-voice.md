# 06 — Practitioner voice: pain points in their own words

Desk-research note 6 of 6 (`W1-DR-01`). Sources: public practitioner/consultancy material found via search,
Oct 2026. Customer SIMULATED. This is the weakest-evidence note and is labeled accordingly — direction, not
proof.

## Sources

- The Curve Group (UK consultancy) case study: 200,000+ written complaints arriving within two weeks
  overwhelmed existing manual-review teams (remediation-project capacity crunch).
- Complaints-management transformation material (industry SlideShare): root-cause analysis driven by real-time
  data sources is the recurring recommended lever.
- LinkedIn practitioner article (Aug 2023): feedback analysis to surface pain points and root causes.
- Academic/practitioner write-ups applying hybrid clustering to bank complaint data — motivated explicitly by
  inconsistent manual tagging.
- Australian Banking Code case study (Mar 2021): review of a bank's complaints-handling procedure found
  process/training gaps in how complaints were directed and processed.
- A trend analysis hosted on a jpmorgan.com property attributing complaint root causes to "technical glitches
  and human error" (provenance uncertain; treat as anecdote).

## The pain points, synthesized

1. **Volume spikes break manual review.** The Curve Group numbers are the extreme case; the everyday version
   is month-end and post-incident surges where every complaint still needs eyes.
2. **Tagging is inconsistent because humans do it.** Multiple sources independently motivate automated
   categorization/clustering as the fix for unreliable issue taxonomies.
3. **Root cause is the ambition; closure is the day job.** Practitioners describe wanting real-time root-cause
   signal but spending their hours on individual case resolution and response letters.
4. **Procedure gaps show up under load.** Training and routing are what fail when volume spikes (Banking Code
   case).

## What it means for Complaint Intelligence

- **Each pain maps to a shipped or planned feature:** spikes → replay-based spike detection vs trailing
  baseline; inconsistent tags → the H2 narrative classifier (and its audited-label eval); root cause →
  issue/sub-issue rollups + `Regulation Section` linkage in the Ontology; load → ranking that puts the
  relief-worthy cases in front of scarce reviewers first (H1).
- **The simulated stakeholder's skepticism writes itself** from these sources: "we already have a taxonomy,"
  "your classifier will be wrong on the messy ones," "root cause needs internal data you'll never see." Good —
  the eval report (citation precision, judge agreement, backtest lift vs random) is the answer to exactly this
  skepticism, with numbers.
- **Feature-priority implication:** ranking and regulation-mapping beat taxonomy-guessing in the demo
  narrative; the classifier is a means (better labels → better ranking), not the headline.

## Limits

SlideShare/LinkedIn-grade provenance; no direct forum scraping (Reddit/communities not pulled); the strongest
item (Curve Group) is UK retail banking, not US. Use as directional color for the simulated sessions, not as
cited evidence in the case study.
