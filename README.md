# Complaint Intelligence

Self-directed project on public data (CFPB complaints, FDIC BankFind, eCFR Title 12). Not client work.

A triage and regulation-mapping system for a bank complaints and compliance team:
Palantir Foundry (pipelines, Ontology, Workshop, AIP Logic) plus an open-source agent and eval layer on Google Cloud Run.

## Layout

- `pipelines/` DuckDB + dbt mirror of the Foundry pipelines
- `agent/` RAG and agent service
- `evals/` golden sets, LLM judge, `REPORT.md`
- `infra/` Terraform for Cloud Run
- `docs/` brief, data quality, Foundry notes, discovery notes, day log

Raw data lives outside the repo: `data/raw` is a gitignored symlink to the downloaded exports.
