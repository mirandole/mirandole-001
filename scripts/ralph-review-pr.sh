#!/usr/bin/env bash
set -euo pipefail

REPO="mirandole/mirandole-001"

PR="${1:-}"

if [ -z "$PR" ]; then
  PR="$(
    gh pr list \
      --repo "$REPO" \
      --state open \
      --json number,headRefName \
      --jq '[.[] | select(.headRefName | startswith("agent/issue-"))][0].number // empty'
  )"
fi

if [ -z "$PR" ]; then
  echo "No open agent PR found."
  exit 1
fi

HEAD="$(
  gh pr view "$PR" \
    --repo "$REPO" \
    --json headRefName \
    --jq '.headRefName'
)"

ISSUE="$(
  echo "$HEAD" | sed -n 's#agent/issue-\([0-9][0-9]*\)-.*#\1#p'
)"

if [ -z "$ISSUE" ]; then
  echo "Could not infer issue number from branch: $HEAD"
  exit 1
fi

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
echo "Issue:   #$ISSUE"
echo "Branch:  $HEAD"
echo "Worktree: $WT"
echo

echo "=== PR summary ==="
gh pr view "$PR" --repo "$REPO" --comments || true
echo

echo "=== PR diff stat ==="
git -C "$WT" diff --stat main...HEAD
echo

echo "=== Running checks ==="
cd "$WT"

export UV_LINK_MODE=copy

uv sync --extra dev
uv run pytest
uv run ruff check .

echo
echo "Review checks passed for PR #$PR / issue #$ISSUE."
echo
echo "Next manual review commands:"
echo "  gh pr diff $PR"
echo "  gh pr view $PR --web"
echo
echo "If OK, merge with:"
echo "  ./scripts/ralph-merge-pr.sh $PR"
