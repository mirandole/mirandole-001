#!/usr/bin/env bash
set -euo pipefail

REPO="mirandole/mirandole-001"

PR="${1:-}"

if [ -z "$PR" ]; then
  echo "Usage: $0 <pr-number>"
  exit 1
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

echo "PR:      #$PR"
echo "Issue:   #${ISSUE:-unknown}"
echo "Branch:  $HEAD"
echo "Worktree: ${WT:-not found}"
echo

echo "Marking PR ready..."
gh pr ready "$PR" --repo "$REPO" || true

echo "Merging PR..."
gh pr merge "$PR" \
  --repo "$REPO" \
  --squash \
  --delete-branch

echo "Updating main..."
git checkout main
if [ -n "${ISSUE:-}" ] && [ -f ".agent-progress/issue-$ISSUE.md" ] && ! git ls-files --error-unmatch ".agent-progress/issue-$ISSUE.md" >/dev/null 2>&1; then
  BACKUP="/tmp/mirandole-agent-progress-before-pull-$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$BACKUP"
  cp -a ".agent-progress/issue-$ISSUE.md" "$BACKUP/" 2>/dev/null || true
  rm -f ".agent-progress/issue-$ISSUE.md"
  echo "Removed untracked .agent-progress/issue-$ISSUE.md before pull; backup: $BACKUP"
fi

git pull --ff-only

if [ -n "$ISSUE" ]; then
  STATE="$(
    gh issue view "$ISSUE" \
      --repo "$REPO" \
      --json state \
      --jq '.state'
  )"

  if [ "$STATE" = "OPEN" ]; then
    echo "Closing issue #$ISSUE..."
    gh issue close "$ISSUE" \
      --repo "$REPO" \
      --reason completed \
      --comment "RALPH_STATUS: DONE

Implemented by merged PR #$PR.

Validated locally before merge:
- UV_LINK_MODE=copy uv sync --extra dev
- uv run pytest
- uv run ruff check ."
  else
    echo "Issue #$ISSUE is already $STATE."
  fi
fi

if [ -n "$WT" ] && [ -d "$WT" ]; then
  echo "Removing worktree $WT..."
  git worktree remove --force "$WT"
fi

echo "Deleting local branch $HEAD if present..."
git branch -D "$HEAD" 2>/dev/null || true

echo
echo "Done."
echo
echo "Next issue:"
echo "  ./scripts/ralph-next-issue.sh"
