# Project status: Complaint Intelligence (paused 2026-10-15)

Human-readable hand-off. The machine-readable source of truth is `STATUS.yaml` (per-task evidence). This page summarises it.

- **Project:** CFPB complaint triage and regulation mapping on Palantir Foundry (Developer Tier) plus an open-source agent/evals layer.
- **Plan window:** 2026-10-12 to 2026-10-31, $25 budget. Spent so far: about $0.3 of OpenRouter credit. GCP not yet set up.
- **State:** PAUSED by the owner on 2026-10-15, mid Week 1. Gate 1 (2026-10-17) is not yet reviewed.
- **Customer (SIMULATED):** Bank of America, N.A. (FDIC cert 3510). Peers: 10 banks (see `STATUS.yaml` decision D2). No real stakeholder was contacted; discovery was desk research plus simulated sessions, labelled as such.

## 1. What is done

### Data and pipeline
| Item | Result | Where |
|---|---|---|
| CFPB complaint exports 2023-09..2026-08 | 17 zips, 13,495,502 raw rows in DuckDB, 0 count mismatches vs source | `pipelines/load_raw.py`, `main.load_audit` |
| Data quality review | 14 issues documented | `docs/01-data-quality.md` |
| Regulation text | eCFR XML for Reg E, DD, Z on disk | `data/raw/ecfr` (gitignored) |
| FDIC records | institutions + quarterly financials for the customer, peers and matched banks | `pipelines/fetch_fdic.py`, `fetch_fdic_all.py` |
| Daily replay | 974 days, idempotent, about 2% late arrivals simulated; rerun gives 0 inserts/updates | `pipelines/replay.py` |
| dbt (staging, intermediate, marts) | 54/54 tests pass; incremental `fct_complaint` equals a full rebuild | `pipelines/dbt/` |
| Entity matching (CFPB company to FDIC bank) | see section 2; wired into dbt; `dim_institution` has 137 certs | `pipelines/entity_match.py`, `docs/entity-matching-review.md` |

In scope: 428,172 complaints (credit card, checking/savings, from 2024-01-01). The customer has 27,041 complaints in the analysis window, a 42.5% relief rate against a peer median of about 25%.

### Models and evals
| Item | Result | Where |
|---|---|---|
| Zero-shot classifier (qwen3.5:2b, local, $0) | product macro-F1 0.861, issue macro-F1 0.122 on 600 held-out complaints (2026-05) | `evals/classify.py`, `docs/03-classifier-baseline.md` |
| Supervised reference (TF-IDF + logistic regression) | product 0.955, issue 0.498 | same |
| Decision models (Ollama 0.40, tev1 4B, product-constrained issue) | issue macro-F1 0.341 | `docs/04-model-comparison.md` |
| Failure patterns | 3 documented (26.7% of issues invalid for the predicted product; attractor labels; card read as checking) | `docs/03-classifier-baseline.md` |
| Triage backtest v0 | top-50/day precision 0.500 vs 0.282 random = 1.78x lift (730 days, leakage controls in place) | `evals/triage_backtest.py`, `docs/05-triage-backtest.md` |
| Desk research | 6 notes | `docs/discovery/01..06` |
| Simulated stakeholder session 1 | done, labelled SIMULATED, cost $0.27 | `docs/discovery/sim-01-head-of-complaints.md` |

### Foundry (host perosa.usw-22.palantirfoundry.com, project complaint-intelligence)
| Item | Result |
|---|---|
| Upload and Pipeline Builder | 3 datasets uploaded, no tier limit hit; pipeline deployed; adds `owner` and `review_status`; outputs `complaint_clean` (about 29.7k rows) and `institution_clean` |
| Ontology | `Complaint` (about 29.7k objects) and `Institution` (12), many-to-one link on `fdic_cert`, saved |
| Workshop | module v0.4.0 published: complaint table with Product and Issue filters; filtering verified |
| Actions (done 2026-10-14) | Complaint edits and object edit history enabled. `escalate-complaint` (status "escalated"), `mark-complaint-reviewed` ("reviewed"), `assign-complaint` (required owner, status "assigned"). Status is a fixed value, never typed. Everyone in the Perosa org may run them. |

Notes and UI gotchas: `docs/02-foundry-notes.md`.

### Coordination
`STATUS.yaml`, `AGENTS.md`, `CLAUDE.md` define the protocol for the two agents (Claude Code and Zcode) that edit this repo. `docs/plan-changes.md` records the plan changes (no outreach).

## 2. Results against the plan's gates (honest read)

| Gate item | Target | Actual | Met? |
|---|---|---|---|
| Entity match precision | 0.95 | v1 0.787 (100 pairs); v2 0.900 (18/20 on a fresh 50) | No. Missed by one error; sample too small to tell. |
| Entity match recall | 0.90 | v1 0.822; v2 0.947 | Yes (v2) |
| Triage lift (H1) | 2x | 1.78x | No at v0 |
| Classifier | baseline reported | reported, TF-IDF beats the LLM | Measured, not "passed" |

Caveats to keep: v2.1 (state-conflict rule) and v2.2 (charter-suffix, large-bank rule) were added after seeing errors, so their scores are post-hoc and need a new sample. Labels are not yet audited for noise (see pending). The customer and all stakeholder sessions are simulated.

## 3. What is pending

### Owner (human)
1. **W1-THU-01:** hand-audit 200 complaints, `D:\foundary\data\audit\audit_200.xlsx`. Afterwards re-score the classifiers against the corrected labels and report both numbers.
2. **D0-05:** GCP sign-in and billing (`gcloud auth login`, `gcloud auth application-default login`, billing account). Needed by 2026-10-26 for Week 3 deploy. Then Claude creates project, budget alerts (50/90/100%), APIs, Artifact Registry.
3. **W1-SAT-01:** 5-minute walkthrough video.
4. **W1-SAT-03:** applications batch 1 (10, no referrals). Later batches in Weeks 2-3.

### Claude / engineering
| Task | Notes |
|---|---|
| **W1-FRI-01** | AIP Logic function: classify and summarize a complaint, write back through an action. Next step when work resumes. |
| Run the three Foundry actions once | Not yet executed; no test write has been made. |
| Workshop buttons for the actions | Not in the plan; optional. |
| **W1-WED-04** | Final pass on `docs/02-foundry-notes.md` ("every tier limit hit"). |
| **W1-SAT-02, W1-SAT-04** | Case study part 1; Gate 1 review (due 2026-10-17). |
| Entity precision gate | Needs a new fresh sample before claiming 0.95; known leftovers: Provident Financial Services (29), Nelnet (21), Synovus Bank after 2026-01-02. |
| Triage v1 | Add narrative TF-IDF, bank history, and clock proximity (days to Reg E/Z deadline), which the simulated persona named as the real pain. |

### Weeks 2-3 (not started)
- **Week 2:** regulation corpus chunking and a 60-item golden set; FastAPI RAG with citations; agent with 4 tools and a judged golden set; IRDAI Form L-30 side build; guardrails and `evals/REPORT.md`; FinanceBench baseline; second simulated session.
- **Week 3:** Dockerfile and Cloud Run via Terraform (blocked on D0-05); CI with an eval gate; resilience, load test, threat model, runbook; Kaggle benchmark; final demo; README polish.
- The plan's cut order if a gate fails: FinanceBench side build, Kaggle side build, polish. Never cut evals or deploy.

## 4. How to resume

1. `cd ~/complaint-intelligence && git pull --rebase`, then read `STATUS.yaml` (protocol in its header).
2. Rebuild the data if needed from the README commands. The DuckDB file (`data/cfpb.duckdb`, about 4.6 GB) and all datasets are local only and gitignored by decision D5.
3. Environment: WSL2 Ubuntu with `uv`. Windows Ollama is unreachable from WSL, so LLM steps run through `evals/docker_run.sh`. `.env` holds the OpenRouter key and is never committed.
4. Foundry sessions expire; sign in yourself when the page asks. Foundry UI edits stay staged until Save, then "Save to ontology", then "Save changes".
5. Suggested order: finish the audit, set up GCP billing, then W1-FRI-01, then the Gate 1 review.

## 5. Not in the repo (local only)
- Datasets and the DuckDB file; audit sheets (`D:\foundary\data\audit\`); the study folder `D:\foundary\study` (private); the plan PDF; `D:\foundary\.env` (many unrelated live keys; never commit; `D:\foundary` is not a git repo).
