-- One row per FDIC certificate that any complaint resolves to: the curated customer and peers, plus every other matched bank.
-- Size: latest FDIC quarterly financials where we pulled them (customer and peers), otherwise the FDIC institution file's last reported assets.

with used_certs as (
    select distinct fdic_cert from {{ ref('int_complaint_entity') }} where fdic_cert is not null
),

seed_roles as (
    select
        fdic_cert,
        -- A cert can appear more than once in the seed (Capital One is both a peer and the Discover rollup).
        case min(case role when 'customer' then 1 when 'peer' then 2 when 'peer_rollup' then 2 else 3 end)
            when 1 then 'customer' when 2 then 'peer' else 'peer_history'
        end as role
    from {{ ref('entity_map_seed') }}
    group by fdic_cert
),

company_names as (
    select fdic_cert, string_agg(distinct cfpb_company, ' | ' order by cfpb_company) as cfpb_company_names
    from (
        select fdic_cert, cfpb_company from {{ ref('int_company_entity') }} where fdic_cert is not null
        union all
        select fdic_cert, cfpb_company from {{ ref('entity_map_seed') }}
    )
    group by fdic_cert
),

latest_financials as (
    select *
    from {{ ref('stg_fdic_financials') }}
    qualify row_number() over (partition by fdic_cert order by report_date desc) = 1
)

select
    a.fdic_cert,
    a.institution_name,
    a.holding_company,
    coalesce(r.role, 'other_bank')              as role,
    n.cfpb_company_names,
    a.is_active,
    a.state,
    a.city,
    a.bank_class,
    a.regulator,
    rich.established_date,
    a.end_date,
    f.report_date                               as latest_report_date,
    coalesce(f.assets_bn, a.assets_bn)          as latest_assets_bn,
    f.deposits_bn                               as latest_deposits_bn
from used_certs u
join {{ ref('stg_fdic_all_institutions') }} a using (fdic_cert)
left join seed_roles r using (fdic_cert)
left join company_names n using (fdic_cert)
left join {{ ref('stg_fdic_institutions') }} rich using (fdic_cert)
left join latest_financials f using (fdic_cert)
