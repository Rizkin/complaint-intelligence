"""Load CFPB CCDB exports into DuckDB as a raw, all-VARCHAR landing table.

Each zip is extracted to a temp file (never the whole archive at once), loaded with
DuckDB's CSV reader, and independently row-counted with Python's csv module so the
load can be reconciled against the source.

Usage: uv run python pipelines/load_raw.py [--raw data/raw/cfpb] [--db data/cfpb.duckdb]
"""

import argparse
import csv
import glob
import os
import re
import shutil
import sys
import tempfile
import time
import zipfile

import duckdb

csv.field_size_limit(sys.maxsize)

COLUMNS = {
    "Date received": "date_received",
    "Product": "product",
    "Sub-product": "sub_product",
    "Issue": "issue",
    "Sub-issue": "sub_issue",
    "Consumer complaint narrative": "narrative",
    "Company public response": "company_public_response",
    "Company": "company",
    "State": "state",
    "ZIP code": "zip_code",
    "Tags": "tags",
    "Submitted via": "submitted_via",
    "Date sent to company": "date_sent_to_company",
    "Company response to consumer": "company_response",
    "Timely response?": "timely_response",
    "Complaint ID": "complaint_id",
}


def export_number(path):
    return int(re.search(r"CCDB_Export_(\d+)_", os.path.basename(path)).group(1))


def python_row_count(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        return header, sum(1 for _ in reader)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="data/raw/cfpb")
    ap.add_argument("--db", default="data/cfpb.duckdb")
    args = ap.parse_args()

    zips = sorted(glob.glob(os.path.join(args.raw, "CCDB_Export_*.zip")), key=export_number)
    if not zips:
        sys.exit(f"no exports found in {args.raw}")

    con = duckdb.connect(args.db)
    select_cols = ", ".join(f'"{src}" AS {dst}' for src, dst in COLUMNS.items())
    con.execute(f"""
        CREATE OR REPLACE TABLE raw_complaints AS
        SELECT {", ".join(f"NULL::VARCHAR AS {d}" for d in COLUMNS.values())},
               NULL::INTEGER AS export_no, NULL::VARCHAR AS source_file
        WHERE false
    """)
    con.execute("""
        CREATE OR REPLACE TABLE load_audit (
            export_no INTEGER, source_file VARCHAR, header_ok BOOLEAN,
            source_rows BIGINT, loaded_rows BIGINT, seconds DOUBLE
        )
    """)

    tmpdir = tempfile.mkdtemp(prefix="cfpb_")
    try:
        for zpath in zips:
            n = export_number(zpath)
            t0 = time.time()
            with zipfile.ZipFile(zpath) as z:
                member = z.namelist()[0]
                csv_path = z.extract(member, tmpdir)
            header, src_rows = python_row_count(csv_path)
            header_ok = header == list(COLUMNS)
            before = con.execute("SELECT count(*) FROM raw_complaints").fetchone()[0]
            con.execute(
                f"""
                INSERT INTO raw_complaints
                SELECT {select_cols}, ? AS export_no, ? AS source_file
                FROM read_csv(?, header = true, all_varchar = true, quote = '"', escape = '"',
                              strict_mode = true, max_line_size = 10000000)
                """,
                [n, member, csv_path],
            )
            loaded = con.execute("SELECT count(*) FROM raw_complaints").fetchone()[0] - before
            secs = time.time() - t0
            con.execute(
                "INSERT INTO load_audit VALUES (?, ?, ?, ?, ?, ?)",
                [n, member, header_ok, src_rows, loaded, secs],
            )
            flag = "OK " if loaded == src_rows and header_ok else "MISMATCH"
            print(f"{flag} export {n:>2}: source={src_rows:>9,} loaded={loaded:>9,} {secs:5.1f}s", flush=True)
            os.remove(csv_path)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    total = con.execute("SELECT count(*) FROM raw_complaints").fetchone()[0]
    bad = con.execute("SELECT count(*) FROM load_audit WHERE source_rows <> loaded_rows OR NOT header_ok").fetchone()[0]
    print(f"\nraw_complaints: {total:,} rows; exports with mismatches: {bad}")
    con.close()


if __name__ == "__main__":
    main()
