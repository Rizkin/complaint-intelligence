-- Resolve each complaint's CFPB company name to an FDIC certificate, as of the date it was received.
-- The seed is date-aware because charters merge (Discover Bank -> Capital One on 2025-05-18) while
-- CFPB keeps the old name (docs/01-data-quality.md #12).

with complaints as (
    select complaint_id, company, date_received from {{ ref('stg_complaints') }}
),

entity_map as (
    select * from {{ ref('entity_map_seed') }}
),

exclusions as (
    select * from {{ ref('company_exclusions') }}
)

select
    c.complaint_id,
    m.fdic_cert,
    case
        when m.role = 'customer' then 'customer'
        when m.role in ('peer', 'peer_rollup') then 'peer'
        when m.role = 'history' then 'peer_history'
        when x.entity_type is not null then x.entity_type
        else 'unmapped'
    end as entity_role
from complaints c
left join entity_map m
    on c.company = m.cfpb_company
   and c.date_received between m.valid_from and m.valid_to
left join exclusions x
    on c.company = x.cfpb_company
