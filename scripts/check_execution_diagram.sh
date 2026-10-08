#!/usr/bin/env bash
# Pre-commit guard: reminds the committer to regenerate the execution sequence
# diagram when flow-relevant source changes without updating the diagram.
#
# Source of truth: docs/diagrams/execution-sequence.mmd
# Rendered artifact: docs/diagrams/execution-sequence.svg (shown in README.md)
#
# Option (b) semantics: NON-BLOCKING nudge by default. It never rewrites the
# diagram and never guesses correctness — only a human/agent (via the
# `update-execution-diagram` skill) can do that. Set EXECUTION_DIAGRAM_STRICT=1
# to make it block the commit instead.
#
# Works both as a native git hook (.git/hooks/pre-commit) and under the
# pre-commit framework (repo: local hook).

set -euo pipefail

# Source files whose change may invalidate the execution sequence diagram.
FLOW_PATHS_REGEX='^src/aws_lifecycle_inventory/(cli\.py|orchestration\.py|account_access\.py|inventory/|lifecycle/|managed_nodes/|output/csv_writer\.py)'

# Any of these being staged counts as "the diagram was addressed".
DIAGRAM_PATHS_REGEX='^docs/diagrams/execution-sequence\.(mmd|svg)$'

# Staged files (added/copied/modified/renamed).
staged() { git diff --cached --name-only --diff-filter=ACMR; }

flow_changed="$(staged | grep -E "$FLOW_PATHS_REGEX" || true)"

# Nothing flow-relevant staged → nothing to check.
if [ -z "$flow_changed" ]; then
  exit 0
fi

diagram_changed="$(staged | grep -E "$DIAGRAM_PATHS_REGEX" || true)"

if [ -n "$diagram_changed" ]; then
  # Diagram source/artifact is part of this commit — assume it was reviewed. Pass.
  exit 0
fi

# Flow changed but the diagram was not touched: emit the reminder.
cat >&2 <<EOF

┌─ execution-diagram reminder ─────────────────────────────────────────────┐
│ You staged changes to the scan execution flow but did NOT update the
│ execution sequence diagram.
│
│ Changed flow files:
$(printf '│   - %s\n' $flow_changed)
│
│ The README shows a maintained diagram of the org multi-account scan,
│ rendered from docs/diagrams/execution-sequence.mmd. If this change alters
│ triggers, orchestration, collectors, lifecycle wiring, or CSV output,
│ regenerate it:
│
│   1) run the "update-execution-diagram" skill (edits the .mmd), or edit
│      docs/diagrams/execution-sequence.mmd directly, then
│   2) scripts/render_execution_diagram.sh   # re-renders the .svg
│   3) git add docs/diagrams/execution-sequence.mmd docs/diagrams/execution-sequence.svg
│
│ (If the flow is unchanged, you can ignore this and commit again.)
└──────────────────────────────────────────────────────────────────────────┘
EOF

if [ "${EXECUTION_DIAGRAM_STRICT:-0}" = "1" ]; then
  echo "EXECUTION_DIAGRAM_STRICT=1 → blocking commit." >&2
  exit 1
fi

# Non-blocking nudge.
exit 0
