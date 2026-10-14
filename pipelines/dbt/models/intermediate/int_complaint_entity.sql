-- Resolve each complaint's CFPB company to an FDIC certificate and a role, as of the date it was received.
-- Priority:
--   1. entity_map_seed: the curated customer and peer set (date-aware: Discover Bank -> Capital One on 2025-05-18)
--   2. company_exclusions: credit bureaus, credit unions, fintechs, processors (never a bank match)
--   3. int_company_entity: matcher + human overrides, date-aware -> 'other_bank' when a bank is matched
--   4. otherwise 'non_bank'

with complaints as (
    select complaint_id, company, date_received from {{ ref('stg_complaints') }}
),

entity_map as (
    select * from {{ ref('entity_map_seed') }}
),

exclusions as (
    select * from {{ ref('company_exclusions') }}
),

company_entity as (
    select * from {{ ref('int_company_entity') }}
)

select
    c.complaint_id,
    coalesce(m.fdic_cert, case when x.entity_type is null then ce.fdic_cert end) as fdic_cert,
    case
        when m.role = 'customer' then 'customer'
        when m.role in ('peer', 'peer_rollup') then 'peer'
        when m.role = 'history' then 'peer_history'
        when x.entity_type is not null then x.entity_type
        when ce.fdic_cert is not null then 'other_bank'
        else 'non_bank'
    end as entity_role
from complaints c
left join entity_map m
    on c.company = m.cfpb_company
   and c.date_received between m.valid_from and m.valid_to
left join exclusions x
    on c.company = x.cfpb_company
left join company_entity ce
    on c.company = ce.cfpb_company
   and c.date_received between ce.valid_from and ce.valid_to
