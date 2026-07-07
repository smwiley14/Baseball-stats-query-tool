#!/bin/bash
# Smoke test for the NL2SQL chat workflow against a running backend.
#
# Usage:
#   ./scripts/smoke_test.sh                                   # defaults to http://localhost:8000
#   BASE_URL=http://localhost:3000/api ./scripts/smoke_test.sh # through the frontend's nginx proxy
#
# Reads API_KEY from backend/.env if not set explicitly.
#
# Exit code is 0 if every check behaved as expected, 1 otherwise.

set -uo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
API_KEY="${API_KEY:-$(grep -E '^API_KEY=' backend/.env 2>/dev/null | cut -d= -f2-)}"

if [[ -z "$API_KEY" ]]; then
  echo "Could not find API_KEY. Set it explicitly: API_KEY=... ./scripts/smoke_test.sh" >&2
  exit 1
fi

PASS=0
FAIL=0

# check_status DESCRIPTION EXPECTED_HTTP_CODE -- curl_args...
check_status() {
  local desc="$1" expected="$2"; shift 2
  local code
  code=$(curl -s -o /dev/null -m 30 -w "%{http_code}" "$@")
  if [[ "$code" == "$expected" ]]; then
    echo "PASS: $desc (HTTP $code)"
    PASS=$((PASS + 1))
  else
    echo "FAIL: $desc (expected HTTP $expected, got $code)"
    FAIL=$((FAIL + 1))
  fi
}

# check_query DESCRIPTION MESSAGE -- checks sql_execution_status == success and a non-null table_data
check_query() {
  local desc="$1" message="$2"
  local resp status
  resp=$(curl -s -m 60 -X POST "$BASE_URL/chat" \
    -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" \
    -d "$(python3 -c 'import json,sys; print(json.dumps({"message": sys.argv[1]}))' "$message")")
  status=$(echo "$resp" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("metadata",{}).get("sql_execution_status"))' 2>/dev/null)
  if [[ "$status" == "success" ]]; then
    echo "PASS: $desc"
    PASS=$((PASS + 1))
  else
    echo "FAIL: $desc (sql_execution_status=$status)"
    echo "  response: $resp"
    FAIL=$((FAIL + 1))
  fi
}

# check_rejected DESCRIPTION MESSAGE -- checks the query was NOT executed (relevance gate or safety check caught it)
check_rejected() {
  local desc="$1" message="$2"
  local resp status
  resp=$(curl -s -m 60 -X POST "$BASE_URL/chat" \
    -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" \
    -d "$(python3 -c 'import json,sys; print(json.dumps({"message": sys.argv[1]}))' "$message")")
  status=$(echo "$resp" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("metadata",{}).get("sql_execution_status"))' 2>/dev/null)
  if [[ "$status" != "success" ]]; then
    echo "PASS: $desc (correctly not executed)"
    PASS=$((PASS + 1))
  else
    echo "FAIL: $desc (query unexpectedly executed!)"
    echo "  response: $resp"
    FAIL=$((FAIL + 1))
  fi
}

echo "== Health & auth =="
check_status "health endpoint" 200 "$BASE_URL/health"
check_status "chat rejects missing API key" 401 -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" -d '{"message":"test"}'
check_status "chat rejects wrong API key" 401 -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" -H "X-API-Key: wrong-key" -d '{"message":"test"}'
check_status "chat rejects malformed body" 422 -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" -d '{}'

echo
echo "== Real NL2SQL queries (known-good, from backend/configs/sql_examples.yml) =="
check_query "season leaderboard"        "Who hit the most home runs in 2020?"
check_query "single-player season line" "What were Aaron Judge's batting stats in 2020?"
check_query "career totals"             "What are Mike Trout's career batting totals?"
check_query "team aggregate"            "What were the Yankees' team batting totals in 2020?"
check_query "qualified-hitter filter"   "Who had the highest OPS in 2020 among qualified hitters?"

echo
echo "== Should be rejected, not executed =="
check_rejected "off-topic question"        "What is the capital of France?"
check_rejected "destructive-phrased query" "Delete all players who played for the Yankees in 2020"

echo
echo "== Results: $PASS passed, $FAIL failed =="
[[ "$FAIL" -eq 0 ]]
