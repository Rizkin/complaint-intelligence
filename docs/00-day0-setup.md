# Day 0 setup (2026-10-12)

## Status

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Palantir Developer Tier signup + plan limits | PENDING | Approval pending. Fill the limits table below once in. |
| 2 | Developer Console / OSDK / Ontology MCP availability | PENDING | Blocked on 1. If unavailable, page 5 fallback: export curated tables, agent fully open-source. |
| 3 | CFPB 2024-2026 exports | DONE | Exports 5-21, 846 MB zipped, ~6.2 GB CSV, all zips pass integrity check. |
| 4 | FDIC institutions test call | DONE | `api.fdic.gov/banks/institutions`, no key. |
| 5 | GCP project, us-central1, $10 budget, 1-instance cap | TODO | Billing account must be set up by hand. |
| 6 | $15 OpenRouter credit | DONE | Prepaid, hard stop. |
| 7 | Ollama + small instruct model | DONE | `qwen3.5:2b` (2.7 GB), ~25 tok/s on RTX 3050 4 GB, JSON mode works. |
| 8 | Docker Desktop on WSL2, repos in WSL2 fs | DONE | Docker 29.8.2 + Compose v5.5.1 in Ubuntu WSL2. Containers reach host Ollama via `--add-host=host.docker.internal:host-gateway`. |
| 9 | Kaggle token + GitHub repo | PARTIAL | Repo created. Kaggle token still to add. |
| 10 | 15 discovery contacts | TODO | `docs/discovery/contacts.md` (keep out of git if it has personal details). |

## Data on disk

Raw data lives at `D:\foundary\data\raw` (`/mnt/d/foundary/data/raw`), symlinked as `data/raw`.

- `cfpb/CCDB_Export_{5..21}_*.zip` from the CFPB Narratives Archive (complaints received Dec 2011 to Aug 14, 2026; archive is frozen).
  Export 5 covers Sep 2023 to Mar 2024, so filter to `date_received >= 2024-01-01`.
- `ecfr/title12_part{1005,1030,1026}.xml` = Reg E, Reg DD, Reg Z, issue date 2026-10-05.

## Gotchas found

- eCFR `/api/versioner/v1/full/...` returns HTTP 406 without compression. Use `curl --compressed` or send `Accept-Encoding: gzip`.
- Each CFPB export is one CSV inside a zip; DuckDB cannot read zips directly, so unzip first (or stream with Python).
- Kaggle CLI now reads the token from `~/.kaggle/access_token` (older `kaggle.json` also works).

## Palantir Developer Tier limits

Copy from Control Panel -> Your Plan.

| Limit | Value |
|-------|-------|
| Storage | |
| Compute / builds | |
| Ontology objects | |
| AIP / LLM usage | |
| Users / seats | |
| Developer Console | |
| OSDK | |
| Ontology MCP | |
