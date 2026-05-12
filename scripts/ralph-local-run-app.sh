#!/usr/bin/env bash

# Stop on errors, missing variables, and failed pipeline commands.
set -euo pipefail

# Useful one-shot overrides:
# RALPH_SBX_APP_HOST_PORT=8001 scripts/ralph-run-sbx-app.sh
# RALPH_SBX_APP_PUBLIC_URL=http://localhost:8001/ scripts/ralph-run-sbx-app.sh

# The ${VAR:-default} form means: use $VAR if it exists, otherwise use default.
HOST="${RALPH_SBX_APP_HOST:-0.0.0.0}"
HOST_PORT="${RALPH_SBX_APP_HOST_PORT:-8000}"
PUBLIC_URL="${RALPH_SBX_APP_PUBLIC_URL:-http://127.0.0.1:${HOST_PORT}/}"

# Resolve the repository root from this script location, so the script can be
# run from any current directory.
ROOT="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.." >/dev/null
  pwd
)"

echo "Sandbox app"
echo "Worktree: $ROOT"
echo
echo "Starting app. Login password: sandbox-password"
echo "Bind: ${HOST}:${HOST_PORT}"
echo "Open: ${PUBLIC_URL}"
echo "Press Ctrl-C to stop."
echo

# Optional local secrets and source credentials live outside committed code.
# set -a exports every variable assigned by the sourced file.
if [ -f "${ROOT}/.env.ralph.local" ]; then
  echo "Using .env.ralph.local for optional source credentials."
  set -a
  # shellcheck disable=SC1091
  . "${ROOT}/.env.ralph.local"
  set +a
  echo
fi

# The app writes to a local SQLite database and the script tails this log file.
LOG_FILE="${ROOT}/var/sbx-app.log"
mkdir -p "${ROOT}/var"

# Export the environment expected by mirandole.config.Settings.from_env().
# Existing values are preserved, so callers can override them before the command.
export MIRANDOLE_PASSWORD="${MIRANDOLE_PASSWORD:-sandbox-password}"
export MIRANDOLE_SESSION_SECRET="${MIRANDOLE_SESSION_SECRET:-sandbox-session-secret-sandbox-session-secret}"
export MIRANDOLE_DATABASE_PATH="${MIRANDOLE_DATABASE_PATH:-${ROOT}/var/sbx-app.sqlite3}"
export MIRANDOLE_COOKIE_SECURE="${MIRANDOLE_COOKIE_SECURE:-false}"
export PROD="${PROD:-false}"
export MIRANDOLE_LOG_LEVEL="${MIRANDOLE_LOG_LEVEL:-INFO}"
export UV_LINK_MODE="${UV_LINK_MODE:-copy}"

# Start the app in a subshell. Its stdout and stderr go to the log file.
# The trailing & runs it in the background so this script can wait and tail logs.
(
  cd "$ROOT"
  uv sync --extra dev
  exec uv run uvicorn --factory mirandole.app:create_app --host "$HOST" --port "$HOST_PORT"
) >"$LOG_FILE" 2>&1 &
APP_PID="$!"

# Ensure Ctrl-C, TERM, or normal script exit stops the background app process.
cleanup() {
  trap - EXIT INT TERM
  echo
  echo "Stopping sandbox app."
  kill "$APP_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Poll the local app endpoint until it responds, or give up after 60 seconds.
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
  exit 1
fi

echo "App is available at ${PUBLIC_URL}"
echo

# Keep the foreground process alive and stream app logs to the terminal.
tail -f "$LOG_FILE"
