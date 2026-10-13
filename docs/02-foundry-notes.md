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
| 2026-10-14 | Pipeline Builder: pipeline "New pipeline" with inputs complaint_customer + institution; transforms on complaints: `owner` = Null cast to String, `review_status` = "new" (Apply expression, Value tab); outputs `complaint_clean` (28 cols) and `institution_clean` (15 cols); compute profile Extra small | Deploy succeeded in ~2 min. Output datasets landed in the project folder. `complaint_clean` ~29.7k rows. |
| 2026-10-14 | Pipeline Builder UI gotchas | (1) Banner "one other open tab editing this branch" appears if the pipeline is open in two tabs; close the extra one before editing. (2) Expression picker "null" first option is the STRING "null"; pick the item typed Null. (3) Sandbox autosaves; Save/Deploy buttons top right. (4) Output dataset name field is the top field of the output panel; Enter confirms. |
| 2026-10-14 | Ontology Manager: created object type `Complaint` (backing `complaint_clean`, PK `complaint_id`, title `complaint_id`, 26 properties) and `Institution` (backing `institution_clean`, PK `fdic_cert`, title `institution_name`, 15 properties); many-to-one link type Complaint -> Institution via foreign key `fdic_cert` (`complaint.institution.get()`); saved to ontology | OK. Complaint indexed with 29,730 objects (= dataset rows). Object types used: 2 (+ 11 from the AIP Now starter ontology; limit 60). No auto-generated Create/Modify/Delete actions on purpose (narrow Escalate/Assign/Mark reviewed to be built Fri; broad Modify = threat-model risk). |
| 2026-10-14 | Ontology Manager UI gotchas | (1) New menu items: click the menu, wait ~1 s, then click; "Object type" is the first entry. (2) Changes stay staged until top-right **Save** -> review page -> **Save to ontology** -> **Save changes**. (3) Wizard pickers: Primary key / Title dropdowns toggle closed on a second click. (4) New Foundry object types default to status Experimental. |
| 2026-10-14 | Workshop: created module "Workshop module - 2026-10-14 02:36:43" in the project; added object type Complaint to the module; added an Object table widget in the right section bound to a new object set variable starting from all Complaint objects (current value 29,730 Complaints; table renders complaint ids). Table has only the Title column so far; Filter list widget not added; module not yet Saved and published (autosaved draft only) | Partial. Remaining: columns, Filter list for product + issue wired to the table's object set, filter to customer (entity_role = customer is already true for all rows in this dataset), Save and publish. |
| 2026-10-14 | Workshop in the embedded browser pane | Editor UI responds 10-30 s after each click; rapid clicks get queued and land on the wrong widgets (an unwanted Vega Chart was added and removed). "Edit module with AI FDE" opens a popup that the pane blocks (needs a user click). Do widget wiring one click at a time with long waits, or in a normal browser. Reload restores the autosaved draft. |

