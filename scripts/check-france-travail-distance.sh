#!/usr/bin/env bash
set -euo pipefail

MOTS_CLES="${1:-Linux}"
COMMUNE="${2:-75101}"
DISTANCE="${3:-10}"

: "${MIRANDOLE_FRANCE_TRAVAIL_CLIENT_ID:?MIRANDOLE_FRANCE_TRAVAIL_CLIENT_ID is required}"
: "${MIRANDOLE_FRANCE_TRAVAIL_CLIENT_SECRET:?MIRANDOLE_FRANCE_TRAVAIL_CLIENT_SECRET is required}"

TOKEN_RESPONSE="$(
  curl -sS -X POST \
    "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=/partenaire" \
    -H "Accept: application/json" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    --data-urlencode "grant_type=client_credentials" \
    --data-urlencode "client_id=${MIRANDOLE_FRANCE_TRAVAIL_CLIENT_ID}" \
    --data-urlencode "client_secret=${MIRANDOLE_FRANCE_TRAVAIL_CLIENT_SECRET}" \
    --data-urlencode "scope=api_offresdemploiv2 o2dsoffre"
)"

ACCESS_TOKEN="$(
  python3 -c 'import json, sys; print(json.load(sys.stdin)["access_token"])' \
    <<< "$TOKEN_RESPONSE"
)"

echo "Request: motsCles=${MOTS_CLES} commune=${COMMUNE} distance=${DISTANCE}" >&2

curl -sS -G \
  "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  --data-urlencode "motsCles=${MOTS_CLES}" \
  --data-urlencode "commune=${COMMUNE}" \
  --data-urlencode "distance=${DISTANCE}" \
  | python3 -c '
import json
import sys

payload = json.load(sys.stdin)
for offer in payload.get("resultats", []):
    location = offer.get("lieuTravail", {})
    print(json.dumps(location, ensure_ascii=False, sort_keys=True))
'
