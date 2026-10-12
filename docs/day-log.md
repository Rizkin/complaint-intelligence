# Day log

## 2026-10-12 (Day 0)
- Shipped: CFPB exports 5-21 downloaded (846 MB zip), eCFR Reg E/DD/Z XML, FDIC test call OK, Ollama qwen3.5:2b tested (~25 tok/s)
- Numbers:
- Blockers: Palantir Developer Tier approval pending
- Tomorrow top 3:

## 2026-10-12 (Mon, Week 1 day 1, started early)
- Shipped: `pipelines/load_raw.py` (13,495,502 rows, 17/17 exports reconcile), `pipelines/profile_raw.py`,
  `docs/01-data-quality.md` (14 issues), FDIC fetch for 12 certs (`pipelines/fetch_fdic.py`),
  date-aware entity seed, first peer benchmark. Customer: Bank of America; 10 peers picked.
- Numbers: scope 428,203 complaints; 47.6% with narrative pre-cutoff; BofA 10.4 complaints per $1B assets, 42.5% relief vs peer median ~25%.
- Blockers: Palantir approval; GCP billing.
- Tomorrow top 3: `docs/00-brief.md`; dbt staging + fct_complaint + dim_institution with tests; replay script.
