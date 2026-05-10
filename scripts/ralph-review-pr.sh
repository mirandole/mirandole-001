#!/usr/bin/env bash
set -euo pipefail

REPO="mirandole/mirandole-001"

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
    read -r -p "Select PR to review [1-$PR_COUNT] (q to quit): " CHOICE

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
echo "Review checks passed for PR #$PR / issue #${ISSUE:-unknown}."
echo
echo "Next manual review commands:"
echo "  gh pr diff $PR"
echo "  gh pr view $PR --web"
echo
echo "If OK, merge with:"
echo "  ./scripts/ralph-merge-pr.sh $PR"
