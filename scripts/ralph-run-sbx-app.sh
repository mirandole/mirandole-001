#!/usr/bin/env bash

# Stop on errors, missing variables, and failed pipeline commands.
set -euo pipefail

# Useful one-shot overrides:
# RALPH_SBX_APP_HOST_PORT=8001 scripts/ralph-run-sbx-app.sh
# RALPH_SBX_APP_PUBLIC_URL=http://localhost:8001/ scripts/ralph-run-sbx-app.sh
# RALPH_SBX_APP_WORKTREE=dev2 scripts/ralph-run-sbx-app.sh
# scripts/ralph-run-sbx-app.sh /path/to/worktree

SANDBOX="${RALPH_SBX_NAME:-mirandole-001}"

if [ "$#" -gt 1 ]; then
  echo "Usage: $0 [worktree-path-or-branch]"
  exit 2
fi

# The ${VAR:-default} form means: use $VAR if it exists, otherwise use default.
HOST="${RALPH_SBX_APP_HOST:-0.0.0.0}"
HOST_PORT="${RALPH_SBX_APP_HOST_PORT:-8000}"
PUBLIC_URL="${RALPH_SBX_APP_PUBLIC_URL:-http://127.0.0.1:${HOST_PORT}/}"
WORKTREE_SELECTOR="${RALPH_SBX_APP_WORKTREE:-${1:-}}"

# Resolve the repository root from this script location, so the script can be
# run from any current directory.
ROOT="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.." >/dev/null
  pwd
)"

resolve_worktree() {
  local selector="$1"

  if [ -z "$selector" ]; then
    printf '%s\n' "$ROOT"
    return 0
  fi

  if [ -d "$selector" ]; then
    (
      cd "$selector" >/dev/null
      pwd
    )
    return 0
  fi

  if [ -d "${ROOT}/${selector}" ]; then
    (
      cd "${ROOT}/${selector}" >/dev/null
      pwd
    )
    return 0
  fi

  git -C "$ROOT" worktree list --porcelain | awk -v selector="$selector" '
    /^worktree / {
      worktree = substr($0, 10)
      worktree_name = worktree
      sub("^.*/", "", worktree_name)
      branch = ""
      if (selector == worktree || selector == worktree_name) {
        print worktree
        found = 1
        exit
      }
      next
    }
    /^branch / {
      branch = substr($0, 8)
      short_branch = branch
      sub("^refs/heads/", "", short_branch)
      if (selector == branch || selector == short_branch) {
        print worktree
        found = 1
        exit
      }
      next
    }
    /^$/ {
      worktree = ""
      worktree_name = ""
      branch = ""
    }
    END {
      exit found ? 0 : 1
    }
  '
}

APP_WORKTREE="$(resolve_worktree "$WORKTREE_SELECTOR")" || {
  echo "Could not find worktree: $WORKTREE_SELECTOR"
  echo
  echo "Available worktrees:"
  git -C "$ROOT" worktree list
  exit 1
}

echo "Sandbox app"
echo "Sandbox: $SANDBOX"
echo "Worktree: $APP_WORKTREE"
echo
echo "Starting app. Login password: sandbox-password"
echo "Bind: ${HOST}:${HOST_PORT}"
echo "Open: ${PUBLIC_URL}"
echo "Press Ctrl-C to stop."
echo

ENV_FILE="${APP_WORKTREE}/.env.ralph.local"
SBX_ENV_FILE_ARGS=()

# Optional local secrets and source credentials live outside committed code.
# set -a exports every variable assigned by the sourced file.
if [ -f "$ENV_FILE" ]; then
  echo "Using .env.ralph.local for optional source credentials."
  set -a
  # shellcheck disable=SC1091
  . "$ENV_FILE"
  set +a
  SBX_ENV_FILE_ARGS=(--env-file "$ENV_FILE")
  echo
fi

# The app writes to a local SQLite database and the script tails this log file.
LOG_FILE="${APP_WORKTREE}/var/sbx-app.log"
mkdir -p "${APP_WORKTREE}/var"

# Export the environment expected by mirandole.config.Settings.from_env().
# Existing values are preserved, so callers can override them before the command.
export MIRANDOLE_PASSWORD="${MIRANDOLE_PASSWORD:-sandbox-password}"
export MIRANDOLE_SESSION_SECRET="${MIRANDOLE_SESSION_SECRET:-sandbox-session-secret-sandbox-session-secret}"
export MIRANDOLE_DATABASE_PATH="${MIRANDOLE_DATABASE_PATH:-${APP_WORKTREE}/var/sbx-app.sqlite3}"
export MIRANDOLE_COOKIE_SECURE="${MIRANDOLE_COOKIE_SECURE:-false}"
export PROD="${PROD:-false}"
export MIRANDOLE_LOG_LEVEL="${MIRANDOLE_LOG_LEVEL:-INFO}"
export UV_LINK_MODE="${UV_LINK_MODE:-copy}"

# Start the app inside the Docker sandbox with sbx exec.
# The trailing & runs the host-side sbx exec process in the background so this
# script can wait for readiness and then stream logs.
sbx exec \
  -w "$APP_WORKTREE" \
  "${SBX_ENV_FILE_ARGS[@]}" \
  -e "MIRANDOLE_PASSWORD=$MIRANDOLE_PASSWORD" \
  -e "MIRANDOLE_SESSION_SECRET=$MIRANDOLE_SESSION_SECRET" \
  -e "MIRANDOLE_DATABASE_PATH=$MIRANDOLE_DATABASE_PATH" \
  -e "MIRANDOLE_COOKIE_SECURE=$MIRANDOLE_COOKIE_SECURE" \
  -e "PROD=$PROD" \
  -e "MIRANDOLE_LOG_LEVEL=$MIRANDOLE_LOG_LEVEL" \
  -e "UV_LINK_MODE=$UV_LINK_MODE" \
  "$SANDBOX" \
  bash -lc "uv sync --extra dev && exec uv run uvicorn --factory mirandole.app:create_app --host '$HOST' --port '$HOST_PORT'" \
  >"$LOG_FILE" 2>&1 &
APP_PID="$!"

# Ensure Ctrl-C, TERM, or normal script exit stops the background app process.
cleanup() {
  trap - EXIT INT TERM
  echo
  echo "Stopping sandbox app."
  kill "$APP_PID" 2>/dev/null || true
  sbx exec "$SANDBOX" pkill -f "uvicorn --factory mirandole.app:create_app" \
    >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

# Publish the sandbox port to the host after sbx has started the container.
# sbx may need a few seconds before Docker reports the container endpoint.
echo "Publishing sandbox port ${HOST_PORT}:${HOST_PORT}..."
PORT_PUBLISHED="false"
PUBLISH_OUTPUT=""
for _ in $(seq 1 30); do
  if PUBLISH_OUTPUT="$(sbx ports "$SANDBOX" --publish "${HOST_PORT}:${HOST_PORT}" 2>&1)"; then
    PORT_PUBLISHED="true"
    break
  fi
  if [[ "$PUBLISH_OUTPUT" == *"already published"* ]]; then
    PORT_PUBLISHED="true"
    break
  fi
  sleep 1
done

if [ "$PORT_PUBLISHED" != "true" ]; then
  echo "Could not publish sandbox port ${HOST_PORT}:${HOST_PORT}."
  if [ -n "$PUBLISH_OUTPUT" ]; then
    echo "$PUBLISH_OUTPUT"
  fi
  echo "Recent app log:"
  tail -n 80 "$LOG_FILE" || true
  exit 1
fi

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
