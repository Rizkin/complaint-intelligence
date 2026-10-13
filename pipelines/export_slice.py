"""Export the curated Foundry upload slice from the dbt marts.

Files (data/export/, gitignored):
  complaint_customer.parquet/.csv  customer bank (Bank of America) complaints, full window  -> Complaint object type
  complaint_bank_scope.parquet     customer + 10 peers                                       -> peer benchmarks
  institution.csv                  dim_institution (11 banks + Discover history)             -> Institution object type
  complaint_sample_1k.csv          1,000-row smoke test for the first upload

Usage: uv run python pipelines/export_slice.py [--out data/export]
"""

import argparse
import os

import duckdb

ap = argparse.ArgumentParser()
ap.add_argument("--db", default="data/cfpb.duckdb")
ap.add_argument("--out", default="data/export")
args = ap.parse_args()
os.makedirs(args.out, exist_ok=True)

con = duckdb.connect(args.db, read_only=True)

# Foundry-friendly column set: snake_case, ISO dates, booleans, no load-metadata columns.
COLS = """
    cast(complaint_id as varchar) as complaint_id, date_received, date_sent_to_company, arrival_date,
    product, sub_product, issue, sub_issue, narrative, has_narrative,
    company, cast(fdic_cert as integer) as fdic_cert, entity_role, state, zip_code, tags,
    is_older_american, is_servicemember, submitted_via,
    company_response, company_public_response, is_timely, is_in_progress, got_relief, got_monetary_relief,
    is_post_cutoff
"""


def export(name, sql, fmts):
    for fmt in fmts:
        path = os.path.join(args.out, f"{name}.{fmt}")
        opts = "(FORMAT PARQUET, COMPRESSION ZSTD)" if fmt == "parquet" else "(FORMAT CSV, HEADER)"
        con.execute(f"COPY ({sql}) TO '{path}' {opts}")
        rows = con.execute(f"SELECT count(*) FROM ({sql})").fetchone()[0]
        print(f"{name}.{fmt:<8} rows={rows:>8,} size={os.path.getsize(path) / 2**20:8.1f} MB")


export("complaint_customer", f"SELECT {COLS} FROM analytics.fct_complaint WHERE entity_role = 'customer'", ["parquet", "csv"])
export("complaint_bank_scope", f"SELECT {COLS} FROM analytics.fct_complaint WHERE entity_role in ('customer','peer','peer_history')", ["parquet"])
export("institution", "SELECT * FROM analytics.dim_institution ORDER BY fdic_cert", ["csv"])
export("complaint_sample_1k", f"SELECT {COLS} FROM analytics.fct_complaint WHERE entity_role = 'customer' ORDER BY date_received, complaint_id LIMIT 1000", ["csv"])
