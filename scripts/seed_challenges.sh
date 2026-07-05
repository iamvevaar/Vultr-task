#!/usr/bin/env bash
#
# Seed a batch of challenges via the admin API.
#
# No real credentials are stored here — supply your own via env vars.
# ADMIN_CODE must match the server's ADMIN_SIGNUP_CODE (from your .env).
#
# The script logs in as the admin if it exists, otherwise registers it using
# ADMIN_CODE. Run ONCE — re-running creates duplicate challenges.
#
# Local dev:
#   ADMIN_CODE=<your ADMIN_SIGNUP_CODE> bash scripts/seed_challenges.sh
#
# Production (point BASE at your deployment):
#   ADMIN_CODE=<code> ADMIN_EMAIL=<admin email> ADMIN_PASS=<admin password> \
#   BASE=https://<your-domain>/api bash scripts/seed_challenges.sh

set -euo pipefail

BASE="${BASE:-http://localhost:8000/api}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@example.com}"
ADMIN_PASS="${ADMIN_PASS:-changeme123}"
ADMIN_CODE="${ADMIN_CODE:-change-me}"   # ← override with your real ADMIN_SIGNUP_CODE

echo "→ Getting an admin token from $BASE ..."
# Try to log in; if that fails, register a fresh admin with the code.
TOKEN=$(curl -s -X POST "$BASE/auth/login" -H 'Content-Type: application/json' \
  -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASS\"}" \
  | python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null || true)

if [ -z "$TOKEN" ]; then
  TOKEN=$(curl -s -X POST "$BASE/auth/register" -H 'Content-Type: application/json' \
    -d "{\"email\":\"$ADMIN_EMAIL\",\"username\":\"admin\",\"password\":\"$ADMIN_PASS\",\"admin_code\":\"$ADMIN_CODE\"}" \
    | python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))")
fi

[ -n "$TOKEN" ] || { echo "✗ Could not obtain an admin token (check ADMIN_CODE / credentials)."; exit 1; }
echo "  ok"

START="2020-01-01T00:00:00Z"
END="2030-12-31T23:59:59Z"

create() {
  curl -s -X POST "$BASE/admin/challenges" \
    -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d "$1" \
    | python3 -c "import sys,json;d=json.load(sys.stdin);print('  ✓ created:', d.get('name', d))"
}

echo "→ Creating challenges ..."
create "{\"name\":\"Chatterbox\",\"description\":\"Post 5 comments\",\"type\":\"count\",\"rule_config\":{\"target\":5},\"event_type\":\"comment_posted\",\"start_at\":\"$START\",\"end_at\":\"$END\",\"reward\":{\"type\":\"points\",\"amount\":100},\"status\":\"active\"}"
create "{\"name\":\"Conversation Starter\",\"description\":\"Create 3 threads\",\"type\":\"count\",\"rule_config\":{\"target\":3},\"event_type\":\"post_created\",\"start_at\":\"$START\",\"end_at\":\"$END\",\"reward\":{\"type\":\"points\",\"amount\":50},\"status\":\"active\"}"
create "{\"name\":\"Problem Solver\",\"description\":\"Get an answer marked as the solution\",\"type\":\"count\",\"rule_config\":{\"target\":1},\"event_type\":\"solution_marked\",\"start_at\":\"$START\",\"end_at\":\"$END\",\"reward\":{\"type\":\"badge\",\"code\":\"problem_solver\",\"label\":\"Problem Solver\"},\"status\":\"active\"}"
create "{\"name\":\"Curious Mind\",\"description\":\"Read 10 posts\",\"type\":\"count\",\"rule_config\":{\"target\":10},\"event_type\":\"post_viewed\",\"start_at\":\"$START\",\"end_at\":\"$END\",\"reward\":{\"type\":\"points\",\"amount\":20},\"status\":\"active\"}"
create "{\"name\":\"On Fire\",\"description\":\"Comment 3 days in a row\",\"type\":\"streak\",\"rule_config\":{\"days\":3},\"event_type\":\"comment_posted\",\"start_at\":\"$START\",\"end_at\":\"$END\",\"reward\":{\"type\":\"badge\",\"code\":\"on_fire\",\"label\":\"On Fire\"},\"status\":\"active\"}"
create "{\"name\":\"Weekly Contributor\",\"description\":\"Post 5 comments this week\",\"type\":\"count\",\"rule_config\":{\"target\":5},\"event_type\":\"comment_posted\",\"start_at\":\"$START\",\"end_at\":\"$END\",\"reward\":{\"type\":\"points\",\"amount\":75},\"cadence\":\"weekly\",\"status\":\"active\"}"

echo "Done. Open the Challenges page to see them."
