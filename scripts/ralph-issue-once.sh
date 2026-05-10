#!/usr/bin/env bash
set -euo pipefail

REPO="mirandole/mirandole-001"

if [ $# -lt 1 ]; then
  echo "Usage: $0 <issue-number>"
  exit 1
fi

ISSUE="$1"
SANDBOX="mirandole-001"
BRANCH="agent/issue-${ISSUE}-$(date +%Y%m%d-%H%M%S)"
PROGRESS=".agent-progress/issue-${ISSUE}.md"
PROMPT_FILE="/tmp/ralph-issue-${ISSUE}.prompt.md"

mkdir -p .agent-progress
touch "$PROGRESS"

TITLE="$(gh issue view "$ISSUE" --repo "$REPO" --json title --jq '.title')"

cat > "$PROMPT_FILE" <<EOF
You are implementing GitHub issue #$ISSUE in repo $REPO.

MANDATORY CONTEXT:
- Read AGENTS.md first.
- Read CONTEXT.md.
- Read docs/agents/issue-tracker.md.
- Read docs/agents/triage-labels.md.
- Read docs/agents/domain.md.
- Use the project domain vocabulary from CONTEXT.md.
- Use GitHub CLI for issue operations.

FETCH THE ISSUE:
Run:
gh issue view $ISSUE --repo $REPO --comments --json number,title,body,labels,comments

PRE-CHECKS:
- Continue only if the issue has label ready-for-agent.
- Stop if the issue has label ready-for-human, needs-info, needs-triage, or wontfix.
- Read the "Blocked by" section.
- If any blocker is still open, do not code. Add a GitHub issue comment saying:
  RALPH_STATUS: BLOCKED
  Then explain the open blockers.

TASK:
Implement only issue #$ISSUE: "$TITLE"

WORKFLOW:
1. Make a short plan.
2. Implement the smallest complete vertical slice satisfying the acceptance criteria.
3. Do not refactor unrelated code.
4. Add or update tests required by the issue.
5. Run all relevant checks you discover: tests, lint, typecheck, formatting.
6. If checks fail, fix them before committing.
7. Update $PROGRESS with:
   - issue number and title
   - summary
   - important decisions
   - files changed
   - commands run
   - remaining blockers if any
8. Commit the change with:
   Implement issue #$ISSUE: $TITLE
9. Push the branch.
10. Open a draft PR linked to issue #$ISSUE.
11. Add a comment on issue #$ISSUE containing:
   RALPH_STATUS: PR_OPEN
   PR link
   summary
   checks run

STRICT RULES:
- Work on one issue only.
- Do not merge the PR.
- Do not close the issue unless explicitly instructed by the human.
- Do not commit secrets.
- Do not store real API keys in source code.
EOF

echo "Running issue #$ISSUE on branch $BRANCH"

sbx run codex \
  --name "$SANDBOX" \
  --branch "$BRANCH" \
  -- exec \
  --sandbox workspace-write \
  "$(cat "$PROMPT_FILE")"
