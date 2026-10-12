"""Fetch FDIC BankFind institution records and latest financials for the certs in the entity-map seed.

Writes raw JSON to data/raw/fdic/ and loads `fdic_institutions` and `fdic_financials` into DuckDB.

Usage: uv run python pipelines/fetch_fdic.py [--seed pipelines/seeds/entity_map_seed.csv]
"""

import argparse
import csv
import json
import os
from datetime import date

import duckdb
import requests

API = "https://api.fdic.gov/banks"
INST_FIELDS = "CERT,NAME,ACTIVE,ASSET,DEP,STALP,CITY,NAMEHCR,RSSDHCR,CHARTER_CLASS,REGAGNT,ESTYMD,ENDEFYMD,CHANGEC1,REPDTE,WEBADDR"
FIN_FIELDS = "CERT,REPDTE,ASSET,DEP,NETINC,LNLSNET"


def get(path, **params):
    r = requests.get(f"{API}/{path}", params=params, timeout=30)
    r.raise_for_status()
    return [row["data"] for row in r.json()["data"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", default="pipelines/seeds/entity_map_seed.csv")
    ap.add_argument("--out", default="data/raw/fdic")
    ap.add_argument("--db", default="data/cfpb.duckdb")
    ap.add_argument("--since", default="20231231", help="first quarter-end (YYYYMMDD) of financials to pull")
    args = ap.parse_args()

    with open(args.seed, newline="") as fh:
        certs = sorted({int(r["fdic_cert"]) for r in csv.DictReader(fh)})
    cert_filter = "CERT:(" + " OR ".join(map(str, certs)) + ")"

    institutions = get("institutions", filters=cert_filter, fields=INST_FIELDS, limit=100)
    financials = get(
        "financials", filters=f"{cert_filter} AND REPDTE:[{args.since} TO 99991231]", fields=FIN_FIELDS,
        sort_by="REPDTE", sort_order="DESC", limit=10000,
    )
    missing = set(certs) - {int(i["CERT"]) for i in institutions}
    if missing:
        raise SystemExit(f"FDIC returned no institution for certs {sorted(missing)}")

    os.makedirs(args.out, exist_ok=True)
    stamp = date.today().isoformat()
    paths = {}
    for name, rows in (("institutions", institutions), ("financials", financials)):
        paths[name] = os.path.join(args.out, f"{name}_{stamp}.json")
        with open(paths[name], "w") as fh:
            json.dump(rows, fh, indent=1)

    con = duckdb.connect(args.db)
    con.execute("CREATE OR REPLACE TABLE fdic_institutions AS SELECT * FROM read_json_auto(?)", [paths["institutions"]])
    con.execute("CREATE OR REPLACE TABLE fdic_financials AS SELECT * FROM read_json_auto(?)", [paths["financials"]])
    print(con.sql("""
        SELECT CERT, NAME, ACTIVE, round(ASSET / 1e6, 1) AS assets_bn, STALP, NAMEHCR
        FROM fdic_institutions ORDER BY ASSET DESC"""))
    print(con.sql("""
        SELECT count(*) AS rows, count(DISTINCT CERT) AS certs, min(REPDTE) AS oldest, max(REPDTE) AS latest
        FROM fdic_financials"""))
    con.close()


if __name__ == "__main__":
    main()
