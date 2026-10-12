-- A CFPB company name must map to at most one certificate on any given date,
-- otherwise the date-aware join in int_complaint_entity would duplicate complaints.
select a.cfpb_company, a.fdic_cert as cert_a, b.fdic_cert as cert_b
from {{ ref('entity_map_seed') }} a
join {{ ref('entity_map_seed') }} b
  on a.cfpb_company = b.cfpb_company
 and (a.fdic_cert, a.valid_from) < (b.fdic_cert, b.valid_from)
 and a.valid_from <= b.valid_to
 and b.valid_from <= a.valid_to
