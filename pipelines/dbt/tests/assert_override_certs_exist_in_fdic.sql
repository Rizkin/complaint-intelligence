-- Every certificate a human override points to must exist in the FDIC candidate file (typos and stale certs fail here).
select o.cfpb_company, o.fdic_cert
from {{ ref('entity_overrides') }} o
left join {{ ref('stg_fdic_all_institutions') }} f using (fdic_cert)
where o.fdic_cert is not null and f.fdic_cert is null
