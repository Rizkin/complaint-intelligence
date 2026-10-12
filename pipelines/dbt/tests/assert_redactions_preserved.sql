-- CFPB redacts PII as XXXX. No transform may drop or alter it: the redaction count per complaint
-- must be identical in the feed and in fct_complaint.
select f.complaint_id,
       length(f.narrative) - length(replace(f.narrative, 'XXXX', '')) as feed_xxxx_chars,
       length(c.narrative) - length(replace(c.narrative, 'XXXX', '')) as fct_xxxx_chars
from {{ source('landing', 'feed_complaints') }} f
join {{ ref('fct_complaint') }} c on c.complaint_id = cast(f.complaint_id as bigint)
where f.narrative like '%XXXX%'
  and feed_xxxx_chars <> coalesce(fct_xxxx_chars, 0)
