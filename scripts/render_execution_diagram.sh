#!/usr/bin/env bash
# Render + validate the execution sequence diagram.
#
# Single source of truth: docs/diagrams/execution-sequence.mmd
# Generated artifact:      docs/diagrams/execution-sequence.svg
#
# Uses mermaid-cli via npx (no permanent dependency). A non-zero exit means the
# mermaid source has a syntax error — fix the .mmd, do not touch the .svg by hand.
#
# Usage: scripts/render_execution_diagram.sh

set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
SRC="$ROOT/docs/diagrams/execution-sequence.mmd"
OUT="$ROOT/docs/diagrams/execution-sequence.svg"
CFG="$ROOT/docs/diagrams/.mermaid-config.json"

if [ ! -f "$SRC" ]; then
  echo "error: mermaid source not found: $SRC" >&2
  exit 2
fi

echo "Rendering $SRC -> $OUT (SVG)…"
npx -y @mermaid-js/mermaid-cli -i "$SRC" -o "$OUT" -c "$CFG" -b white

echo "OK: validated syntax and wrote $OUT"
