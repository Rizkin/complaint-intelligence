-- The entity join must neither drop nor duplicate complaints: one row per complaint, none 'unmapped'.
select 'row count differs' as problem, (select count(*) from {{ ref('stg_complaints') }}) as expected, (select count(*) from {{ ref('int_complaint_entity') }}) as actual
where (select count(*) from {{ ref('stg_complaints') }}) <> (select count(*) from {{ ref('int_complaint_entity') }})
union all
select 'unmapped role', 0, count(*) from {{ ref('int_complaint_entity') }} where entity_role = 'unmapped' having count(*) > 0
