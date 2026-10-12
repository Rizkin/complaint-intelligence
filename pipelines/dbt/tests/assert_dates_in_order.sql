-- A complaint can't be sent to the company before it was received, or arrive before it was received.
select complaint_id, date_received, date_sent_to_company, arrival_date
from {{ ref('fct_complaint') }}
where date_sent_to_company < date_received
   or arrival_date < date_received
