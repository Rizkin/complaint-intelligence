"""Replay the CFPB archive as a daily feed, one arrival day at a time, in date order.

The archive is frozen, so "arrival" is simulated: most complaints arrive on their `date_received`, and a
deterministic ~2% (chosen by hashing `complaint_id`) arrive 1-7 days late. Late rows exercise the part of
the pipeline that must not key incremental loads on event date.

Every load is idempotent: rows are upserted on `complaint_id` and only rewritten when their content hash
changes, so replaying a day twice changes nothing. Each day is logged in `replay_log` for freshness and
reconciliation.

Usage:
  uv run python pipelines/replay.py --days 30            # continue from the high-water mark
  uv run python pipelines/replay.py --until 2026-06-30   # replay up to a date
  uv run python pipelines/replay.py --reset --days 30    # start over from --start
  uv run python pipelines/replay.py --rerun 2024-01-05   # re-apply one arrival day (idempotency check)
"""

import argparse
import time
from datetime import date, timedelta

import duckdb

SCOPE_PRODUCTS = ("Checking or savings account", "Credit card")
LATE_EVERY = 50      # 1 in 50 complaints arrives late
MAX_LATE_DAYS = 7

COLUMNS = [
    "complaint_id", "date_received", "product", "sub_product", "issue", "sub_issue", "narrative",
    "company_public_response", "company", "state", "zip_code", "tags", "submitted_via",
    "date_sent_to_company", "company_response", "timely_response",
]


def setup(con, start):
    products = ", ".join(f"'{p}'" for p in SCOPE_PRODUCTS)
    # Arrival schedule for the in-scope archive. Deterministic, so every replay sees the same late rows.
    con.execute(f"""
        CREATE TABLE IF NOT EXISTS replay_source AS
        SELECT {", ".join(COLUMNS)}, export_no,
               CASE WHEN hash(complaint_id) % {LATE_EVERY} = 0
                    THEN 1 + (hash(complaint_id || 'lag') % {MAX_LATE_DAYS})::INTEGER ELSE 0 END AS arrival_lag_days,
               try_cast(date_received AS DATE) + arrival_lag_days AS arrival_date,
               md5(concat_ws('|', {", ".join(f"coalesce({c}, '')" for c in COLUMNS)})) AS row_hash
        FROM raw_complaints
        WHERE product IN ({products}) AND date_received >= '{start.isoformat()}'
    """)
    con.execute(f"""
        CREATE TABLE IF NOT EXISTS feed_complaints (
            {", ".join(f"{c} VARCHAR" + (" PRIMARY KEY" if c == "complaint_id" else "") for c in COLUMNS)},
            export_no INTEGER, arrival_lag_days INTEGER, arrival_date DATE, row_hash VARCHAR,
            first_loaded_at TIMESTAMP, last_loaded_at TIMESTAMP, load_count INTEGER
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS replay_log (
            arrival_date DATE, run_at TIMESTAMP, arrived BIGINT, on_time BIGINT, late BIGINT,
            inserted BIGINT, updated BIGINT, unchanged BIGINT, max_lag_days INTEGER, seconds DOUBLE
        )
    """)


def high_water_mark(con):
    return con.execute("SELECT max(arrival_date) FROM replay_log").fetchone()[0]


def load_day(con, day):
    t0 = time.time()
    con.execute("CREATE OR REPLACE TEMP TABLE batch AS SELECT * FROM replay_source WHERE arrival_date = ?", [day])
    arrived, late, max_lag = con.execute(
        "SELECT count(*), count(*) FILTER (WHERE arrival_lag_days > 0), coalesce(max(arrival_lag_days), 0) FROM batch"
    ).fetchone()
    inserted, updated = con.execute("""
        SELECT count(*) FILTER (WHERE f.complaint_id IS NULL),
               count(*) FILTER (WHERE f.complaint_id IS NOT NULL AND f.row_hash <> b.row_hash)
        FROM batch b LEFT JOIN feed_complaints f USING (complaint_id)
    """).fetchone()
    set_cols = ", ".join(f"{c} = excluded.{c}" for c in COLUMNS[1:] + ["export_no", "arrival_lag_days", "arrival_date", "row_hash"])
    con.execute(f"""
        INSERT INTO feed_complaints
        SELECT {", ".join(COLUMNS)}, export_no, arrival_lag_days, arrival_date, row_hash,
               now(), now(), 1
        FROM batch
        ON CONFLICT (complaint_id) DO UPDATE SET {set_cols},
            last_loaded_at = now(), load_count = feed_complaints.load_count + 1
        WHERE feed_complaints.row_hash <> excluded.row_hash
    """)
    secs = time.time() - t0
    unchanged = arrived - inserted - updated
    con.execute(
        "INSERT INTO replay_log VALUES (?, now(), ?, ?, ?, ?, ?, ?, ?, ?)",
        [day, arrived, arrived - late, late, inserted, updated, unchanged, max_lag, secs],
    )
    return arrived, late, inserted, updated, unchanged


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/cfpb.duckdb")
    ap.add_argument("--start", type=date.fromisoformat, default=date(2024, 1, 1))
    ap.add_argument("--days", type=int)
    ap.add_argument("--until", type=date.fromisoformat)
    ap.add_argument("--rerun", type=date.fromisoformat, help="re-apply one arrival day")
    ap.add_argument("--reset", action="store_true")
    args = ap.parse_args()

    con = duckdb.connect(args.db)
    if args.reset:
        for t in ("replay_source", "feed_complaints", "replay_log"):
            con.execute(f"DROP TABLE IF EXISTS {t}")
    setup(con, args.start)

    if args.rerun:
        days = [args.rerun]
    else:
        last_source_day = con.execute("SELECT max(arrival_date) FROM replay_source").fetchone()[0]
        hwm = high_water_mark(con)
        first = hwm + timedelta(days=1) if hwm else args.start
        last = args.until or (first + timedelta(days=args.days - 1) if args.days else last_source_day)
        last = min(last, last_source_day)
        days = [first + timedelta(days=i) for i in range((last - first).days + 1)]

    totals = [0, 0, 0, 0, 0]
    for day in days:
        con.execute("BEGIN")
        stats = load_day(con, day)
        con.execute("COMMIT")
        totals = [a + b for a, b in zip(totals, stats)]
        if len(days) <= 31 or day.day == 1:
            print(f"{day} arrived={stats[0]:>5} late={stats[1]:>3} ins={stats[2]:>5} upd={stats[3]:>3} same={stats[4]:>5}", flush=True)

    feed, source_due = con.execute("""
        SELECT (SELECT count(*) FROM feed_complaints),
               (SELECT count(*) FROM replay_source WHERE arrival_date <= (SELECT max(arrival_date) FROM replay_log))
    """).fetchone()
    print(f"\n{len(days)} day(s): arrived={totals[0]:,} late={totals[1]:,} inserted={totals[2]:,} "
          f"updated={totals[3]:,} unchanged={totals[4]:,}")
    print(f"feed_complaints={feed:,} vs source rows due by high-water mark={source_due:,} -> "
          f"{'RECONCILED' if feed == source_due else 'MISMATCH'}")
    con.close()


if __name__ == "__main__":
    main()
