#!/usr/bin/env bash
set -euo pipefail

WHAT="${1:-Python}"
WHERE="${2:-Paris}"
COUNTRY="${3:-fr}"
PAGE="${4:-1}"
DISTANCE="${5:-}"
RESULTS_PER_PAGE="${MIRANDOLE_ADZUNA_RESULTS_PER_PAGE:-5}"

: "${MIRANDOLE_ADZUNA_APP_ID:?MIRANDOLE_ADZUNA_APP_ID is required}"
: "${MIRANDOLE_ADZUNA_APP_KEY:?MIRANDOLE_ADZUNA_APP_KEY is required}"

QUERY_PARAMS=(
  --data-urlencode "app_id=${MIRANDOLE_ADZUNA_APP_ID}"
  --data-urlencode "app_key=${MIRANDOLE_ADZUNA_APP_KEY}"
  --data-urlencode "what=${WHAT}"
  --data-urlencode "where=${WHERE}"
  --data-urlencode "results_per_page=${RESULTS_PER_PAGE}"
  --data-urlencode "content-type=application/json"
)

if [[ -n "${DISTANCE}" ]]; then
  QUERY_PARAMS+=(--data-urlencode "distance=${DISTANCE}")
fi

echo "Request: country=${COUNTRY} page=${PAGE} what=${WHAT} where=${WHERE} distance=${DISTANCE:-none} results_per_page=${RESULTS_PER_PAGE}" >&2

curl -sS -G \
  "https://api.adzuna.com/v1/api/jobs/${COUNTRY}/search/${PAGE}" \
  -H "Accept: application/json" \
  "${QUERY_PARAMS[@]}" \
  | python3 -c '
import json
import sys

payload = json.load(sys.stdin)
results = payload.get("results", [])
count = payload.get("count", 0)

print(f"count={count} returned={len(results)}")

for index, offer in enumerate(results, start=1):
    company = offer.get("company") or {}
    location = offer.get("location") or {}
    title = offer.get("title") or "Title missing"
    source_id = offer.get("id") or "missing"
    company_name = company.get("display_name") or "missing"
    location_name = location.get("display_name") or "missing"
    created = offer.get("created") or "missing"
    contract = offer.get("contract_type") or offer.get("contract_time") or "missing"
    redirect_url = offer.get("redirect_url") or "missing"

    print()
    print(f"{index}. {title}")
    print(f"   id: {source_id}")
    print(f"   company: {company_name}")
    print(f"   location: {location_name}")
    print(f"   created: {created}")
    print(f"   contract: {contract}")
    print(f"   url: {redirect_url}")
'
