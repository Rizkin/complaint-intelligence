"""Print replay freshness and how many late rows reached fct_complaint."""
import duckdb

con = duckdb.connect("data/cfpb.duckdb", read_only=True)
print(con.sql("""
    SELECT count(*) AS replayed_days, min(arrival_date) AS first_day, max(arrival_date) AS high_water_mark,
           sum(late) AS late_rows, max(max_lag_days) AS max_lag_days
    FROM (SELECT * FROM replay_log QUALIFY row_number() OVER (PARTITION BY arrival_date ORDER BY run_at DESC) = 1)
"""))
print(con.sql("""
    SELECT count(*) AS fct_rows, count(*) FILTER (WHERE arrival_lag_days > 0) AS late_rows_in_fct
    FROM analytics.fct_complaint
"""))
