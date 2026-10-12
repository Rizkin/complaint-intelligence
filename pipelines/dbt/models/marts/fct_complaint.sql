{{
    config(
        materialized='incremental',
        unique_key='complaint_id',
        incremental_strategy='delete+insert',
    )
}}

-- One row per complaint. Incremental on the load watermark (last_loaded_at), not on date_received,
-- so late-arriving rows and rows whose content changed are both picked up on the next run.

select
    c.complaint_id,
    c.date_received,
    c.date_sent_to_company,
    c.arrival_date,
    c.arrival_lag_days,
    c.last_loaded_at,

    c.product,
    c.sub_product,
    c.issue,
    c.sub_issue,
    c.narrative,
    c.has_narrative,

    c.company,
    e.fdic_cert,
    e.entity_role,
    c.state,
    c.zip_code,
    c.tags,
    c.is_older_american,
    c.is_servicemember,
    c.submitted_via,

    c.company_response,
    c.company_public_response,
    c.is_timely,
    c.is_in_progress,
    c.got_relief,
    c.got_monetary_relief,
    c.is_post_cutoff

from {{ ref('stg_complaints') }} c
join {{ ref('int_complaint_entity') }} e using (complaint_id)

{% if is_incremental() %}
where c.last_loaded_at > (select coalesce(max(last_loaded_at), timestamp '1900-01-01') from {{ this }})
{% endif %}
