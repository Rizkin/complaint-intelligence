-- One row per complaint in the replay feed: typed, trimmed, with flags used downstream.

with source as (
    select * from {{ source('landing', 'feed_complaints') }}
)

select
    cast(complaint_id as bigint)                         as complaint_id,
    cast(date_received as date)                          as date_received,
    cast(date_sent_to_company as date)                   as date_sent_to_company,
    arrival_date,
    arrival_lag_days,
    last_loaded_at,
    export_no,

    nullif(trim(product), '')                            as product,
    nullif(trim(sub_product), '')                        as sub_product,
    nullif(trim(issue), '')                              as issue,
    nullif(trim(sub_issue), '')                          as sub_issue,
    nullif(trim(narrative), '')                          as narrative,
    nullif(trim(narrative), '') is not null              as has_narrative,

    trim(company)                                        as company,
    nullif(trim(state), '')                              as state,
    nullif(trim(zip_code), '')                           as zip_code,
    coalesce(nullif(trim(tags), ''), 'none')             as tags,
    coalesce(tags, '') like '%Older American%'           as is_older_american,
    coalesce(tags, '') like '%Servicemember%'            as is_servicemember,
    nullif(trim(submitted_via), '')                      as submitted_via,

    nullif(trim(company_response), '')                   as company_response,
    nullif(trim(company_public_response), '')            as company_public_response,
    trim(timely_response) = 'Yes'                        as is_timely,
    company_response = 'In progress'                     as is_in_progress,
    company_response in ('Closed with monetary relief',
                         'Closed with non-monetary relief') as got_relief,
    company_response = 'Closed with monetary relief'     as got_monetary_relief,

    -- The narratives archive ends on 2026-08-14; later rows carry no narratives (docs/01-data-quality.md #1).
    cast(date_received as date) > date '2026-08-14'      as is_post_cutoff

from source
