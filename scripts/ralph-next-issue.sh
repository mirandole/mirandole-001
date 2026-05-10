#!/usr/bin/env bash
set -euo pipefail

REPO="mirandole/mirandole-001"

ISSUE="$(
  gh issue list \
    --repo "$REPO" \
    --state open \
    --label ready-for-agent \
    --json number,title,labels,comments \
    --jq '
      [
        .[]
        | select(([.labels[].name] | index("ready-for-human") | not))
        | select(([.labels[].name] | index("needs-info") | not))
        | select(([.labels[].name] | index("needs-triage") | not))
        | select(([.labels[].name] | index("wontfix") | not))
        | select(
            ([.comments[].body]
              | map(test("RALPH_STATUS: (IN_PROGRESS|PR_OPEN|BLOCKED)"))
              | any
            ) | not
          )
      ]
      | sort_by(.number)
      | .[0].number // empty
    '
)"

if [ -z "$ISSUE" ]; then
  echo "No eligible ready-for-agent issue found."
  exit 0
fi

echo "Selected issue #$ISSUE"

gh issue comment "$ISSUE" --repo "$REPO" --body "RALPH_STATUS: IN_PROGRESS

Agent started on VPS with Docker Sandboxes."

./scripts/ralph-issue-once.sh "$ISSUE"
