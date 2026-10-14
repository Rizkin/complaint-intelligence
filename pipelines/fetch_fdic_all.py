"""Fetch FDIC institutions as match candidates: all ACTIVE ones plus charters that ENDED since 2023-12-31 (mergers/renames).

Why the ended ones: CFPB keeps filing under an old name after a merger (Discover Bank 2025, Synovus 2026, Comerica 2026...), so an active-only
candidate list cannot match them (entity-matching v1 missed these).

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
ENDED_SINCE = "2023-12-31"
EXTRA_CERTS = [5649]  # Discover Bank, merged 2025-05-18 (already inside ENDED_SINCE; kept as a guard)


def page(filters, offset):
    r = requests.get(API, params={"filters": filters, "fields": FIELDS, "limit": 10000, "offset": offset,
                                  "sort_by": "CERT", "sort_order": "ASC"}, timeout=60)
    r.raise_for_status()
    j = r.json()
    return [x["data"] for x in j["data"]], j["meta"]["total"]


def fetch_all(filters):
    rows, offset = [], 0
    while True:
        batch, total = page(filters, offset)
        rows += batch
        offset += len(batch)
        if not batch or offset >= total:
            return rows


def main():
    rows = fetch_all("ACTIVE:1")
    n_active = len(rows)
    rows += fetch_all(f"ACTIVE:0 AND ENDEFYMD:[{ENDED_SINCE} TO 9999-12-31]")
    have = {r["CERT"] for r in rows}
    for cert in EXTRA_CERTS:
        if cert not in have:
            rows += page(f"CERT:{cert}", 0)[0]
    os.makedirs("data/raw/fdic", exist_ok=True)
    path = f"data/raw/fdic/all_institutions_{date.today().isoformat()}.json"
    json.dump(rows, open(path, "w"))
    con = duckdb.connect("data/cfpb.duckdb")
    con.execute("CREATE OR REPLACE TABLE fdic_all_institutions AS SELECT * FROM read_json_auto(?)", [path])
    n, act = con.execute("SELECT count(*), count(*) FILTER (WHERE ACTIVE = 1) FROM fdic_all_institutions").fetchone()
    print(f"{n} institutions ({act} active, {n - act} ended since {ENDED_SINCE}) -> {path}")
    con.close()


if __name__ == "__main__":
    main()
