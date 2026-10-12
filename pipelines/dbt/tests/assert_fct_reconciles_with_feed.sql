-- Every complaint in the replay feed lands in fct_complaint exactly once, and nothing else does.
select feed_rows, fct_rows
from (
    select
        (select count(*) from {{ source('landing', 'feed_complaints') }}) as feed_rows,
        (select count(*) from {{ ref('fct_complaint') }})                 as fct_rows
)
where feed_rows <> fct_rows
