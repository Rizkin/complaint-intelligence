-- A CFPB company must resolve to at most one override row on any date, otherwise int_complaint_entity would duplicate complaints.
select a.cfpb_company, a.valid_from as from_a, a.valid_to as to_a, b.valid_from as from_b, b.valid_to as to_b
from {{ ref('entity_overrides') }} a
join {{ ref('entity_overrides') }} b
  on a.cfpb_company = b.cfpb_company
 and (a.valid_from, coalesce(a.fdic_cert, -1)) < (b.valid_from, coalesce(b.fdic_cert, -1))
 and a.valid_from <= b.valid_to
 and b.valid_from <= a.valid_to
