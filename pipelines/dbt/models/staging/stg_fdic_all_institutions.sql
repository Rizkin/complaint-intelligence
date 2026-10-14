-- All active FDIC institutions plus charters ended since 2023-12-31 (pipelines/fetch_fdic_all.py). ASSET is in thousands of USD.

select
    cast(CERT as integer)                                             as fdic_cert,
    trim(regexp_replace(NAME, '\s+', ' ', 'g'))                       as institution_name,
    nullif(trim(NAMEHCR), '')                                         as holding_company,
    ACTIVE = 1                                                        as is_active,
    STALP                                                             as state,
    CITY                                                              as city,
    BKCLASS                                                           as bank_class,
    REGAGNT                                                           as regulator,
    nullif(strptime(ENDEFYMD, '%m/%d/%Y')::date, date '9999-12-31')   as end_date,
    ASSET / 1e6                                                       as assets_bn
from {{ source('landing', 'fdic_all_institutions') }}
