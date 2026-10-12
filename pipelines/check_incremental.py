"""Prove the incremental fct_complaint equals a full rebuild from the same feed.

Snapshots the incrementally built table, runs `dbt build --full-refresh -s fct_complaint`,
then diffs both ways (ignoring last_loaded_at, which is load metadata).

Usage: uv run python pipelines/check_incremental.py
"""

import subprocess
import sys

import duckdb

DB = "data/cfpb.duckdb"
DBT = ["uv", "run", "dbt", "--quiet", "build", "--project-dir", "pipelines/dbt", "--profiles-dir", "pipelines/dbt"]

con = duckdb.connect(DB)
con.execute("CREATE OR REPLACE TABLE main.fct_complaint_incremental_snapshot AS SELECT * FROM analytics.fct_complaint")
con.close()

subprocess.run(DBT + ["--full-refresh", "-s", "fct_complaint"], check=True)

con = duckdb.connect(DB)
cols = "* EXCLUDE (last_loaded_at)"
only_inc, only_full, rows = con.execute(f"""
    SELECT
      (SELECT count(*) FROM (SELECT {cols} FROM main.fct_complaint_incremental_snapshot
                             EXCEPT SELECT {cols} FROM analytics.fct_complaint)),
      (SELECT count(*) FROM (SELECT {cols} FROM analytics.fct_complaint
                             EXCEPT SELECT {cols} FROM main.fct_complaint_incremental_snapshot)),
      (SELECT count(*) FROM analytics.fct_complaint)
""").fetchone()
con.execute("DROP TABLE main.fct_complaint_incremental_snapshot")
con.close()

print(f"full rebuild rows={rows:,}; only in incremental={only_inc}; only in full rebuild={only_full}")
sys.exit(0 if only_inc == only_full == 0 else 1)
