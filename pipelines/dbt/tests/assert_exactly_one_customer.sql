select count(*) as customers
from {{ ref('dim_institution') }}
where role = 'customer'
having count(*) <> 1
