-- One row per FDIC certificate in the customer + peer set, with its latest reported size.

with roles as (
    select
        fdic_cert,
        -- A cert can appear more than once in the seed (Capital One is both a peer and the Discover rollup).
        case min(case role when 'customer' then 1 when 'peer' then 2 when 'peer_rollup' then 2 else 3 end)
            when 1 then 'customer' when 2 then 'peer' else 'peer_history'
        end as role,
        string_agg(distinct cfpb_company, ' | ' order by cfpb_company) as cfpb_company_names
    from {{ ref('entity_map_seed') }}
    group by fdic_cert
),

latest_financials as (
    select *
    from {{ ref('stg_fdic_financials') }}
    qualify row_number() over (partition by fdic_cert order by report_date desc) = 1
)

select
    i.fdic_cert,
    i.institution_name,
    i.holding_company,
    r.role,
    r.cfpb_company_names,
    i.is_active,
    i.state,
    i.city,
    i.bank_class,
    i.regulator,
    i.established_date,
    i.end_date,
    f.report_date as latest_report_date,
    f.assets_bn   as latest_assets_bn,
    f.deposits_bn as latest_deposits_bn
from {{ ref('stg_fdic_institutions') }} i
join roles r using (fdic_cert)
left join latest_financials f using (fdic_cert)
