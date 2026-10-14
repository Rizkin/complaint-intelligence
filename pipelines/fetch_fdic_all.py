"""Fetch all active FDIC institutions (plus a few closed charters we know matter) as match candidates.

Writes data/raw/fdic/all_institutions_<date>.json and table main.fdic_all_institutions in DuckDB.
Usage: uv run python pipelines/fetch_fdic_all.py
"""

import json
import os
from datetime import date

import duckdb
import requests

API = "https://api.fdic.gov/banks/institutions"
FIELDS = "CERT,NAME,ACTIVE,ASSET,STALP,CITY,NAMEHCR,RSSDHCR,REGAGNT,BKCLASS,ENDEFYMD"
KEEP_INACTIVE = [5649]  # Discover Bank, merged 2025-05-18 (docs/01-data-quality.md #12)


def page(filters, offset):
    r = requests.get(API, params={"filters": filters, "fields": FIELDS, "limit": 10000, "offset": offset,
                                  "sort_by": "CERT", "sort_order": "ASC"}, timeout=60)
    r.raise_for_status()
    j = r.json()
    return [x["data"] for x in j["data"]], j["meta"]["total"]


def main():
    rows, offset = [], 0
    while True:
        batch, total = page("ACTIVE:1", offset)
        rows += batch
        offset += len(batch)
        if not batch or offset >= total:
            break
    for cert in KEEP_INACTIVE:
        b, _ = page(f"CERT:{cert}", 0)
        rows += b
    os.makedirs("data/raw/fdic", exist_ok=True)
    path = f"data/raw/fdic/all_institutions_{date.today().isoformat()}.json"
    json.dump(rows, open(path, "w"))
    con = duckdb.connect("data/cfpb.duckdb")
    con.execute("CREATE OR REPLACE TABLE fdic_all_institutions AS SELECT * FROM read_json_auto(?)", [path])
    n, act = con.execute("SELECT count(*), count(*) FILTER (WHERE ACTIVE = 1) FROM fdic_all_institutions").fetchone()
    print(f"{n} institutions ({act} active) -> {path}")
    con.close()


if __name__ == "__main__":
    main()
