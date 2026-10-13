# Foundry notes (AIP Developer Tier)

Stack hostname and enrollment IDs are kept out of the repo; the host is in the local `.env` as `FOUNDRY_HOST`.
Checked 2026-10-14 by reading the UI (no changes made).

## Plan limits (as stated by the tier)

| Limit | Value | Source |
|-------|-------|--------|
| vCPUs | 25 | Your Plan |
| GPUs | 2 | Your Plan |
| Object types | 60 | Your Plan |
| LLM rate limit | 60-120K tokens/min for latest-gen models; higher for others | Your Plan |
| Users | "Limited" (exact number not shown) | Your Plan |
| AIP tier | SMALL | Resource Management > AIP usage & limits |
| Storage / row caps | Not stated. Measured as GB-months in Resource Management | to be found by uploading |

## Available applications (64 total in the app switcher)

| App | Available | Notes |
|-----|-----------|-------|
| Pipeline Builder | yes | sidebar |
| Ontology Manager | yes | sidebar |
| AIP Logic | yes | sidebar |
| Workshop | yes | found via application search (not pinned in the sidebar) |
| Developer Console | yes | opens to "New application"; OSDK path available |
| Resource Management | yes | usage: Foundry compute (compute-seconds), Ontology volume (GB-months), Foundry storage (GB-months); all 0 at start |
| Code Workspaces, Jupyter, RStudio, VS Code | yes | listed under application search for "workshop" |
| Ontology MCP | not a separate app | search "mcp" returns nothing; MCP is configured from Developer Console, to be confirmed once an Ontology exists |

## Decisions for the plan

- OSDK route is open, so the page 5 fallback is **not** needed for the agent connection. Ontology MCP stays unverified.
- Everything is tracked in compute-seconds and GB-months. Re-check Resource Management after the first upload and again after the 48 MB peer file.

## Limits hit log

_No limit or error hit so far. Append each limit or error with date, action and message._

| Date | Action | Result |
|------|--------|--------|
| 2026-10-14 | Uploaded `institution.csv`, `complaint_sample_1k.csv`, `complaint_customer.parquet` (5.8 MB) to the project | OK, no limit message. Parquet kept its schema on import: 26 columns, dates as `date`, flags as `boolean`, `fdic_cert` as `integer`. Row count 29,730 = local export. |
