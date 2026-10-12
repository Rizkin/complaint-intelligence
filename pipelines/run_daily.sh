#!/usr/bin/env bash
# Simulate the daily feed: replay one arrival day, then run dbt incrementally. Repeat N times.
# Usage: pipelines/run_daily.sh [days=1]
set -euo pipefail
cd "$(dirname "$0")/.."
DAYS="${1:-1}"
DBT=(uv run dbt --quiet build --project-dir pipelines/dbt --profiles-dir pipelines/dbt)

for ((i = 1; i <= DAYS; i++)); do
    out="$(uv run python pipelines/replay.py --days 1)"
    echo "${out%%$'\n'*}"
    "${DBT[@]}" || { echo "dbt build failed on day $i" >&2; exit 1; }
done
echo "daily run: $DAYS day(s) OK"
