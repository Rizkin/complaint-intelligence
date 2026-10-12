"""Customer vs peers: in-scope complaints per $1B of assets, relief rate and narrative share (Jan 2024 to Jun 2026)."""

import duckdb

con = duckdb.connect("data/cfpb.duckdb")
con.execute("""
    CREATE OR REPLACE TABLE entity_map_seed AS
    SELECT * FROM read_csv('pipelines/seeds/entity_map_seed.csv', header = true,
        columns = {'cfpb_company': 'VARCHAR', 'fdic_cert': 'INTEGER', 'valid_from': 'DATE',
                   'valid_to': 'DATE', 'role': 'VARCHAR', 'note': 'VARCHAR'})
""")
print(con.sql("""
WITH c AS (
    SELECT r.complaint_id, r.product, r.company_response, r.narrative, m.fdic_cert,
           CASE WHEN m.role = 'customer' THEN 'customer' ELSE 'peer' END AS role
    FROM raw_complaints r
    JOIN entity_map_seed m
      ON r.company = m.cfpb_company
     AND try_cast(r.date_received AS DATE) BETWEEN m.valid_from AND m.valid_to
    WHERE r.date_received BETWEEN '2024-01-01' AND '2026-06-30'
      AND r.product IN ('Checking or savings account', 'Credit card')
      AND m.role <> 'history'
),
assets AS (
    SELECT CERT, avg(ASSET) / 1e6 AS avg_assets_bn FROM fdic_financials
    WHERE REPDTE BETWEEN '20231231' AND '20260630' GROUP BY 1
)
SELECT i.NAME AS bank, any_value(c.role) AS role, count(*) AS complaints,
       round(any_value(a.avg_assets_bn), 0) AS avg_assets_bn,
       round(count(*) / any_value(a.avg_assets_bn), 1) AS per_1bn_assets,
       round(100 * avg((c.company_response LIKE 'Closed with %relief')::INT), 1) AS pct_relief,
       round(100 * avg((nullif(trim(c.narrative), '') IS NOT NULL)::INT), 1) AS pct_narrative
FROM c JOIN assets a ON a.CERT = c.fdic_cert JOIN fdic_institutions i ON i.CERT = c.fdic_cert
GROUP BY i.NAME ORDER BY per_1bn_assets DESC
""").show(max_width=200))
