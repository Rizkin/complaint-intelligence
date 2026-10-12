select
    cast(CERT as integer)                                as fdic_cert,
    trim(regexp_replace(NAME, '\s+', ' ', 'g'))          as institution_name,
    nullif(trim(NAMEHCR), '')                            as holding_company,
    ACTIVE = 1                                           as is_active,
    STALP                                                as state,
    CITY                                                 as city,
    BKCLASS                                              as bank_class,
    REGAGNT                                              as regulator,
    strptime(ESTYMD, '%m/%d/%Y')::date                   as established_date,
    nullif(strptime(ENDEFYMD, '%m/%d/%Y')::date, date '9999-12-31') as end_date,
    CHANGEC1                                             as last_change_code,
    WEBADDR                                              as website
from {{ source('landing', 'fdic_institutions') }}
