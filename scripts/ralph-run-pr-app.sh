#!/usr/bin/env bash
set -euo pipefail

REPO="mirandole/mirandole-001"
HOST_PORT="${RALPH_REVIEW_HOST_PORT:-8000}"

PR="${1:-}"

if [ -z "$PR" ]; then
  OPEN_PRS="$(
    gh pr list \
      --repo "$REPO" \
      --state open \
      --json number,title,headRefName \
      --jq '.[] | [.number, .title, .headRefName] | @tsv'
  )"

  if [ -z "$OPEN_PRS" ]; then
    echo "No open PR found."
    exit 1
  fi

  echo "Open PRs:"
  printf '%s\n' "$OPEN_PRS" \
    | awk -F '\t' '{printf "  %d) #%s %s [%s]\n", NR, $1, $2, $3}'
  echo

  if [ ! -t 0 ]; then
    echo "No interactive input available. Re-run with a PR number:"
    echo "  $0 <pr-number>"
    exit 1
  fi

  PR_COUNT="$(printf '%s\n' "$OPEN_PRS" | wc -l | tr -d ' ')"

  while true; do
    read -r -p "Select PR to run [1-$PR_COUNT] (q to quit): " CHOICE

    if [ "$CHOICE" = "q" ] || [ "$CHOICE" = "Q" ]; then
      exit 0
    fi

    if ! [[ "$CHOICE" =~ ^[0-9]+$ ]] || [ "$CHOICE" -lt 1 ] || [ "$CHOICE" -gt "$PR_COUNT" ]; then
      echo "Invalid selection."
      continue
    fi

    PR="$(printf '%s\n' "$OPEN_PRS" | awk -F '\t' -v choice="$CHOICE" 'NR == choice {print $1}')"
    break
  done
fi

HEAD="$(
  gh pr view "$PR" \
    --repo "$REPO" \
    --json headRefName \
    --jq '.headRefName'
)"

ISSUE="$(
  echo "$HEAD" | sed -n 's#.*issue-\([0-9][0-9]*\).*#\1#p'
)"

WT="$(
  git worktree list --porcelain \
    | awk -v branch="refs/heads/$HEAD" '
        /^worktree / {w=$2}
        /^branch / && $2 == branch {print w}
      '
)"

if [ -z "$WT" ]; then
  echo "Could not find local worktree for branch: $HEAD"
  echo "Current worktrees:"
  git worktree list
  exit 1
fi

echo "PR:      #$PR"
echo "Issue:   #${ISSUE:-unknown}"
echo "Branch:  $HEAD"
echo "Worktree: $WT"
echo

echo
echo "Starting app. Login password: review-password"
echo "Open: http://127.0.0.1:${HOST_PORT}/"
echo "Press Ctrl-C to stop."
echo

if [ -f ".env.ralph.local" ]; then
  echo "Using .env.ralph.local for optional source credentials."
  set -a
  # shellcheck disable=SC1091
  . ".env.ralph.local"
  set +a
  echo
fi

LOG_FILE="${WT}/var/review-pr-${PR}.log"
mkdir -p "$WT/var"

export MIRANDOLE_PASSWORD="review-password"
export MIRANDOLE_SESSION_SECRET="review-session-secret-review-session-secret"
export MIRANDOLE_DATABASE_PATH="${WT}/var/review-pr-${PR}.sqlite3"
export MIRANDOLE_COOKIE_SECURE="false"
export UV_LINK_MODE="copy"

(
  cd "$WT"
  uv sync --extra dev
  exec uv run uvicorn --factory mirandole.app:create_app --host 127.0.0.1 --port "$HOST_PORT"
) >"$LOG_FILE" 2>&1 &
APP_PID="$!"

echo "Waiting for app to respond..."
for _ in $(seq 1 60); do
  if curl -sS -o /dev/null "http://127.0.0.1:${HOST_PORT}/" 2>/dev/null; then
    break
  fi
  sleep 1
done

if ! curl -sS -o /dev/null "http://127.0.0.1:${HOST_PORT}/" 2>/dev/null; then
  echo "App did not respond on http://127.0.0.1:${HOST_PORT}/"
  echo "Recent app log:"
  tail -n 80 "$LOG_FILE" || true
  kill "$APP_PID" 2>/dev/null || true
  exit 1
fi

cleanup() {
  echo
  echo "Stopping review app."
  kill "$APP_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "App is available at http://127.0.0.1:${HOST_PORT}/"
echo
tail -f "$LOG_FILE"
