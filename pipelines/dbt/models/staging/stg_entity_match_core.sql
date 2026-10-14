-- Algorithm-only company -> FDIC bank matches written by pipelines/entity_match.py (one row per CFPB company name).
-- Human-reviewed overrides are applied later, with dates, in int_company_entity.

select
    trim(company)                       as cfpb_company,
    cast(cert as integer)               as fdic_cert,
    match_type,
    score,
    reason
from {{ source('landing', 'entity_match_core') }}
