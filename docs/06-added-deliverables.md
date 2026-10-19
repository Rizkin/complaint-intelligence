# 06 Added deliverables: engagement artefacts and production controls

Added 2026-10-19. Status: **PLANNED, not started** (the project is paused; see `STATUS.yaml` `paused`). Tasks `GAP-01` to `GAP-06` in `STATUS.yaml`.

## Why

The three-week plan is strong on data, evals and deployment. A review of the plan against a list of what Forward Deployed roles are screened on found six thin spots. Each is a thing a customer or reviewer would ask for and the plan does not yet produce:

| Gap | What a customer or reviewer asks |
|---|---|
| Engagement paperwork | "What exactly are you delivering, for how much, who signs off, and how do we hand it over?" |
| Tenant scoping and kill switch | "Can the agent leak another business unit's data, and can we turn its writes off?" |
| Text-to-SQL accuracy | "How often is the metrics-query tool right, and what stops it running an expensive or destructive query?" |
| Approach selection | "Why an LLM at all, and when would a small classifier be better?" |
| Own MCP surface | "Can other agents use your tools safely, with permissions per tool?" |
| Data handling and incident drill | "What personal data is involved, and have you rehearsed a failure?" |

## Ground rules (inherited from the plan)

- The customer is **SIMULATED** (decision D1). Every customer-facing artefact below is labelled SIMULATED.
- No personal outreach (decision D4). Nothing here needs it.
- Numbers come from repo files (`STATUS.yaml`, `evals/results/`, `docs/`). No invented numbers.
- Every legal or regulatory statement cites a primary text, or is marked **NOT VERIFIED**.
- Cut order if time runs short (existing): FinanceBench side build, Kaggle side build, polish. These tasks take the FinanceBench slot first. Evals and deploy are never cut.

## The six deliverables

### GAP-01 Engagement pack (about 4 h) - `docs/engagement/`
Files: `sow-simulated.md`, `pricing-options.md`, `stakeholders-raci.md`, `DECISIONS.md`, `handover-acceptance.md`.
- SoW: scope, out of scope, deliverables, milestones, assumptions, change control. Acceptance criteria are the **measurable gates already in the plan** (for example citation precision and judge agreement thresholds), not vague promises.
- Pricing: three options (time-and-materials with a cap, fixed price, outcome-based), worked with this project's own cost data (cloud spend, LLM cost per answer from `evals/results/` run metadata), with the risk of each and a recommendation.
- Stakeholders and RACI: the simulated Head of Complaints, compliance, model risk, IT security, analysts; who is responsible, accountable, consulted and informed per deliverable.
- `DECISIONS.md`: compiled from `STATUS.yaml` decisions (D1 to D8 and later), each with context, options, decision, consequence, date.
- Handover and acceptance: runbook, dashboards, secret rotation, teardown, acceptance test list, sign-off template, what is not included.
- **Pass if:** all five files exist; SoW acceptance criteria match `STATUS.yaml` gate numbers; every file says SIMULATED; at least one concrete repo number is cited per file.

### GAP-02 Tenant scoping, kill switch, audit log, per-request budgets (about 3 h) - `agent/`
- Bank scope comes from the authenticated context, never from model-supplied arguments. The customer bank is the tenant; the 10 peers are other tenants. (The CFPB data is public, so this is a **simulated** isolation policy, labelled as such.)
- Tests: (a) asking about a peer bank's complaints returns nothing or a refusal; (b) a prompt-injection attempt to change scope fails; (c) `WRITE_ENABLED=false` makes `propose-action` refuse and no Foundry action is called; (d) every tool call is logged with tool, arguments, scope, rows returned and cost; (e) per-request caps on tool calls, rows and tokens or cost are enforced.
- **Pass if:** all five tests pass in CI and a failing scope test blocks the build.

### GAP-03 Governed-metrics-query eval (about 3 h, 1.5 h of it inside the 40-question golden set)
- Each "what spiked" question in the golden set gets a reference SQL and result. Score **execution accuracy** (result set matches), and break failures down (wrong filter, wrong join, wrong date, wrong aggregate).
- Safety: read-only database role, row cap, statement timeout, cost cap; a test that destructive SQL is rejected.
- **Pass if:** a report with the accuracy and failure breakdown exists and the caps are enforced by tests.

### GAP-04 Approach comparison memo (about 4 h) - `docs/07-approach-comparison.md`
- Same held-out set as `docs/03` and `docs/04` (600 complaints, 2026-05). Compare: zero-shot local LLM (have), TF-IDF plus logistic regression (have), the decision-model run (have), **frozen embeddings plus logistic regression (add; SetFit only if time)**, and AIP Logic classification (add when available, otherwise mark NOT RUN).
- Columns: macro-F1 for product and issue, cost per 1,000 complaints, latency p50 and p95, hardware needed.
- Plus a half page: **when not to use an agent** for this system (classification is deterministic work; analyst questions justify an agent), and prompt vs retrieval vs fine-tuning for the regulation Q&A.
- **Pass if:** every number traces to a saved results file and each approach has a one-line recommendation with a condition.

### GAP-05 Own MCP server (about 3 h) - `agent/mcp_server.py`
- Wrap the four tools (governed metrics query, case search, regulation lookup, propose-action) in a FastMCP server with **per-tool permissions**; reuse the GAP-02 scoping; propose-action is unavailable when the write flag is off.
- **Pass if:** a test client lists only permitted tools and each tool works within scope.

### GAP-06 Data-handling note and incident drill (about 3 h) - `docs/security/`
- `data-handling.md`: inventory of personal data (CFPB narratives with XXXX redactions, FDIC and eCFR public data, Foundry, logs), flow diagram, retention, access; a mapping table to India's DPDP Act concepts and to the US context for a hypothetical deployment. Every legal statement cites the primary text or is marked NOT VERIFIED.
- `incident-drill-01.md`: stage one real failure (for example an LLM timeout storm that should trip the circuit breaker, an eval drop on a pull request, or prompt injection in complaint text), time detection and recovery, and write a blameless root-cause analysis with follow-ups. Optional: answer a 10-question security questionnaire from the threat model.
- **Pass if:** the drill was actually run (logs attached) and the RCA names a root cause and at least two follow-ups.

## Where they fit (to be re-planned at resume)

The calendar in the original plan has slipped (the project paused mid Week 1), so these slots are by day type, not by date:
- Agent day: GAP-02 and GAP-03 (the golden set already holds the questions).
- The FinanceBench slot (cut first): GAP-01 and GAP-04.
- Week 3 reliability and runbook day: GAP-05 and GAP-06. If time is tight, trim the Kaggle benchmark before these.

## Deliberately not added

Multi-agent frameworks, voice agents, managed agent platforms, Kubernetes, semantic caching and a React front end. They would dilute a three-week flagship.
