-- FDIC reports amounts in thousands of USD.

select
    cast(CERT as integer)                    as fdic_cert,
    strptime(REPDTE, '%Y%m%d')::date         as report_date,
    ASSET / 1e6                              as assets_bn,
    DEP / 1e6                                as deposits_bn,
    NETINC / 1e6                             as net_income_bn,
    LNLSNET / 1e6                            as net_loans_bn
from {{ source('landing', 'fdic_financials') }}
