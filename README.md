# Complaint Intelligence

Self-directed project on public data (CFPB complaints, FDIC BankFind, eCFR Title 12). Not client work.
The customer, Bank of America, is simulated; see [docs/00-brief.md](docs/00-brief.md).

A triage and regulation-mapping system for a bank complaints and compliance team:
Palantir Foundry (pipelines, Ontology, Workshop, AIP Logic) plus an open-source agent and eval layer on Google Cloud Run.

## Layout

- `pipelines/` DuckDB loaders, daily replay and the dbt project (`pipelines/dbt`) that mirrors the Foundry pipelines
- `agent/` RAG and agent service
- `evals/` golden sets, LLM judge, `REPORT.md`
- `infra/` Terraform for Cloud Run
- `docs/` brief, data quality, Foundry notes, discovery notes, day log

Raw data lives outside the repo: `data/raw` is a gitignored symlink to the downloaded exports.

## Data pipeline

```bash
uv sync
uv run python pipelines/load_raw.py            # 17 CFPB exports -> raw_complaints, reconciled per export
uv run python pipelines/fetch_fdic.py          # FDIC institutions + quarterly financials for the seed certs
uv run python pipelines/replay.py --reset --days 1
pipelines/run_daily.sh 29                      # replay one day, then incremental dbt build; repeat
uv run python pipelines/replay_status.py       # freshness, late rows
uv run python pipelines/check_incremental.py   # incremental fct_complaint == full rebuild
```

The replay feeds `feed_complaints` one arrival day at a time. About 2% of complaints are made to arrive
1 to 7 days late (deterministic, by hash of `complaint_id`). Loads upsert on `complaint_id` with a row hash,
so rerunning a day changes nothing. `fct_complaint` is incremental on the load watermark, not on
`date_received`, which is what lets late rows through.

dbt models: `stg_complaints`, `stg_fdic_institutions`, `stg_fdic_financials`, `int_complaint_entity`
(date-aware CFPB name to FDIC cert), `fct_complaint`, `dim_institution`. Tests cover keys, accepted values,
relationships, feed reconciliation, preserved `XXXX` redactions, date order and the entity-map ranges.
