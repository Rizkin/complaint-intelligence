-- Company-level, date-aware mapping of a CFPB company name to an FDIC bank (or to none).
--   1. human-reviewed overrides (dated rows: a merged charter ends and its successor starts)
--   2. the matcher's algorithm output for every company that has no override
-- Match means the company IS or OWNS the bank (docs/entity-matching-review.md); partner banks are not matches.

with overrides as (
    select cfpb_company, fdic_cert, valid_from, valid_to, 'override' as source, relation
    from {{ ref('entity_overrides') }}
),

algorithm as (
    select
        cfpb_company,
        fdic_cert,
        date '2011-12-01' as valid_from,
        date '9999-12-31' as valid_to,
        'algorithm'       as source,
        match_type        as relation
    from {{ ref('stg_entity_match_core') }}
    where cfpb_company not in (select cfpb_company from overrides)
)

select * from overrides
union all
select * from algorithm
