"""Profile raw_complaints: date ranges, duplicates, nulls, scope, companies, quirks."""
import duckdb
con = duckdb.connect("data/cfpb.duckdb", read_only=True)
def q(title, sql):
    print(f"\n### {title}")
    print(con.sql(sql))

q("date range per export", """
SELECT export_no, min(date_received) mn, max(date_received) mx, count(*) n,
       count(*) FILTER (WHERE try_cast(date_received AS DATE) IS NULL) bad_dates
FROM raw_complaints GROUP BY 1 ORDER BY 1""")

q("duplicate complaint_id", """
WITH d AS (SELECT complaint_id, count(*) c, count(DISTINCT export_no) ex FROM raw_complaints GROUP BY 1 HAVING c > 1)
SELECT count(*) dup_ids, sum(c) dup_rows, sum(c - 1) extra_rows, count(*) FILTER (WHERE ex > 1) across_exports FROM d""")

q("are cross-export dupes identical rows?", """
WITH d AS (SELECT complaint_id FROM raw_complaints GROUP BY 1 HAVING count(*) > 1),
v AS (SELECT r.complaint_id, count(DISTINCT md5(concat_ws('|', COLUMNS(* EXCLUDE (export_no, source_file))))) versions
      FROM raw_complaints r JOIN d USING (complaint_id) GROUP BY 1)
SELECT versions, count(*) ids FROM v GROUP BY 1 ORDER BY 1""")

q("null / empty share per column (2024+)", """
SELECT * FROM (
 UNPIVOT (SELECT
   avg((nullif(trim(product),'') IS NULL)::INT) product, avg((nullif(trim(sub_product),'') IS NULL)::INT) sub_product,
   avg((nullif(trim(issue),'') IS NULL)::INT) issue, avg((nullif(trim(sub_issue),'') IS NULL)::INT) sub_issue,
   avg((nullif(trim(narrative),'') IS NULL)::INT) narrative, avg((nullif(trim(company_public_response),'') IS NULL)::INT) company_public_response,
   avg((nullif(trim(company),'') IS NULL)::INT) company, avg((nullif(trim(state),'') IS NULL)::INT) state,
   avg((nullif(trim(zip_code),'') IS NULL)::INT) zip_code, avg((nullif(trim(tags),'') IS NULL)::INT) tags,
   avg((nullif(trim(company_response),'') IS NULL)::INT) company_response, avg((nullif(trim(timely_response),'') IS NULL)::INT) timely_response
  FROM raw_complaints WHERE date_received >= '2024-01-01')
 ON COLUMNS(*) INTO NAME col VALUE null_share) ORDER BY null_share DESC""")

q("product mix 2024+", """
SELECT product, count(*) n, round(100.0*count(*)/sum(count(*)) OVER (),1) pct
FROM raw_complaints WHERE date_received >= '2024-01-01' GROUP BY 1 ORDER BY n DESC""")

q("scope rows: checking/savings + credit card, 2024+", """
SELECT product, count(DISTINCT complaint_id) complaints,
       round(100.0*avg((nullif(trim(narrative),'') IS NOT NULL)::INT),1) pct_with_narrative
FROM raw_complaints WHERE date_received >= '2024-01-01'
  AND product IN ('Checking or savings account','Credit card') GROUP BY 1""")

q("top 25 companies in scope", """
SELECT company, count(DISTINCT complaint_id) n,
  count(DISTINCT complaint_id) FILTER (WHERE product='Checking or savings account') checking,
  count(DISTINCT complaint_id) FILTER (WHERE product='Credit card') card,
  round(100.0*avg((company_response ILIKE 'Closed with monetary relief')::INT),1) pct_monetary
FROM raw_complaints WHERE date_received >= '2024-01-01'
  AND product IN ('Checking or savings account','Credit card')
GROUP BY 1 ORDER BY n DESC LIMIT 25""")

q("company_response values in scope", """
SELECT company_response, count(*) n FROM raw_complaints
WHERE date_received >= '2024-01-01' AND product IN ('Checking or savings account','Credit card')
GROUP BY 1 ORDER BY n DESC""")

q("monthly volume in scope", """
SELECT strftime(try_cast(date_received AS DATE), '%Y-%m') m, count(DISTINCT complaint_id) n
FROM raw_complaints WHERE date_received >= '2024-01-01' AND product IN ('Checking or savings account','Credit card')
GROUP BY 1 ORDER BY 1""")

q("other quirks in scope", """
SELECT
 count(*) FILTER (WHERE narrative LIKE '%XXXX%') redacted_narratives,
 count(*) FILTER (WHERE zip_code LIKE '%XX%') masked_zip,
 count(*) FILTER (WHERE try_cast(date_sent_to_company AS DATE) < try_cast(date_received AS DATE)) sent_before_received,
 count(*) FILTER (WHERE company_response = 'In progress') in_progress,
 count(*) FILTER (WHERE length(narrative) < 30 AND nullif(trim(narrative),'') IS NOT NULL) tiny_narratives,
 count(DISTINCT timely_response) timely_values,
 count(DISTINCT state) states
FROM raw_complaints WHERE date_received >= '2024-01-01' AND product IN ('Checking or savings account','Credit card')""")
S = "date_received >= '2024-01-01' AND product IN ('Checking or savings account','Credit card')"
print(con.sql(f"""
SELECT date_received >= '2026-08-15' after_aug14, count(*) n,
       round(100.0*avg((nullif(trim(narrative),'') IS NOT NULL)::INT),1) pct_narr,
       max(date_received) mx
FROM raw_complaints WHERE {S} GROUP BY 1"""))
print(con.sql(f"""
SELECT strftime(try_cast(date_received AS DATE), '%Y-%m') m,
       round(100.0*avg((nullif(trim(narrative),'') IS NOT NULL)::INT),1) pct_narr,
       round(100.0*avg((company_response='In progress')::INT),1) pct_in_progress
FROM raw_complaints WHERE {S} GROUP BY 1 ORDER BY 1"""))
print(con.sql(f"""
SELECT row_number() OVER (ORDER BY count(*) DESC) rk, company, count(*) n,
  count(*) FILTER (WHERE product='Checking or savings account') chk,
  count(*) FILTER (WHERE product='Credit card') card,
  round(100.0*avg((company_response IN ('Closed with monetary relief','Closed with non-monetary relief'))::INT),1) pct_relief,
  round(100.0*avg((nullif(trim(narrative),'') IS NOT NULL)::INT),1) pct_narr
FROM raw_complaints WHERE {S} GROUP BY company ORDER BY n DESC LIMIT 40""").show(max_rows=40, max_width=200))
print(con.sql(f"SELECT tags, count(*) n FROM raw_complaints WHERE {S} GROUP BY 1 ORDER BY 2 DESC"))
print(con.sql(f"SELECT submitted_via, count(*) n FROM raw_complaints WHERE {S} GROUP BY 1 ORDER BY 2 DESC"))
print(con.sql(f"SELECT count(DISTINCT company) companies, count(DISTINCT issue) issues, count(DISTINCT sub_issue) sub_issues, count(DISTINCT sub_product) sub_products FROM raw_complaints WHERE {S}"))
