---
name: update-execution-diagram
description: Regenerate or verify the execution sequence diagram shown in README.md. The mermaid source is docs/diagrams/execution-sequence.mmd and the committed artifact is docs/diagrams/execution-sequence.svg. Use when the execution flow changes (triggers, orchestration, collectors, lifecycle wiring, CSV output) or when a pre-commit hook flags that flow source changed without regenerating the diagram. Also use when the user says "update the execution diagram" or "openspec diagram".
license: MIT
metadata:
  author: cloud-foundations
  version: "2.0"
---

Regenerate (or verify) the component-level **execution sequence diagram**
displayed in `README.md`. The diagram is a maintained documentation requirement
declared in `AGENTS.md`: a newcomer must be able to read it and understand how an
org multi-account scan is processed end to end, trigger to CSV.

This skill is **read-only against AWS** and only edits docs/diagram artifacts. It
never changes application code.

## Source of truth and artifacts

- **Mermaid source (edit this):** `docs/diagrams/execution-sequence.mmd`
- **Rendered artifact (generated, do NOT hand-edit):**
  `docs/diagrams/execution-sequence.svg`
- **Render config:** `docs/diagrams/.mermaid-config.json` (fonts/sizing)
- **README** embeds the SVG as a clickable image between the
  `BEGIN/END: execution-sequence-diagram` markers. Keep those markers intact — the
  pre-commit hook relies on them. Do NOT put inline ```mermaid``` back in the
  README; the README references the SVG only.

## Scope of the diagram

- **Primary path:** organization multi-account scan (the broadest path). Both
  triggers — CLI (current) and Lambda batch (planned) — converge on the shared
  core engine.
- **Level:** component-level (what runs and what it calls), **not** line-level.
- **Honesty markers:** anything implemented-but-not-wired into the org-scan path
  MUST be marked `(not wired)`. Never draw a specified-but-pending edge as if it
  were live.

## Steps

1. **Read the current source** `docs/diagrams/execution-sequence.mmd`.

2. **Re-derive the real flow from code.** Inspect, in order, and note key function
   names + whether each stage is wired into the org-scan path:
   - `src/aws_lifecycle_inventory/cli.py` — triggers/flags; does the CLI yet call
     `run_org_scan`? any Lambda handler?
   - `src/aws_lifecycle_inventory/orchestration.py` — `run_org_scan`,
     `run_scan_multi_region`, `run_scan`, `_collect_in_region`,
     `ORG_SOURCE_STRATEGY`, `OrgScanResult.execution_summary`.
   - `src/aws_lifecycle_inventory/account_access.py` — `resolve_account_session`,
     `assume_role_session` (STS AssumeRole).
   - `src/aws_lifecycle_inventory/inventory/direct_api/__init__.py` —
     `default_collectors()`: exact collectors/services that run.
   - `src/aws_lifecycle_inventory/inventory/config/` — is `collect_from_config`
     registered? If not → `(not wired)`.
   - `src/aws_lifecycle_inventory/managed_nodes/ssm.py` — is `SsmNodeCollector`
     in `default_collectors()`? If not → `(not wired)`.
   - `src/aws_lifecycle_inventory/lifecycle/` — is `evaluate_all`/`evaluate_record`
     called outside tests? If only tests → `(not wired)`, precedence AWS Health
     then EndOfLife.
   - `src/aws_lifecycle_inventory/output/csv_writer.py` — `write_csv`; who calls it.

   Fast wired-check:

   ```bash
   rg -n "run_org_scan|evaluate_all|evaluate_record|collect_from_config|SsmNodeCollector|write_csv" src/ --glob '!**/tests/**'
   ```

3. **Edit the `.mmd` source** so participants, loops, `alt`/`opt` blocks, and
   `(not wired)` markers match what you found. Keep conventions: `autonumber`;
   per-account `loop` with an `alt` for assume-role failure (isolation); per-region
   `loop`; collector backstop note; lifecycle in an `opt ... (not wired)` block
   with the "no match means UNKNOWN" note; closing note on `execution_summary()`.

   **CRITICAL — characters that break the mermaid sequence parser.** Do NOT use
   any of these inside message text or `Note` text (they caused real render
   failures):
   - `;` semicolon — mermaid treats it as a statement separator.
   - `[` `]` square brackets — parsed as syntax (even in message/alias text).
   - `->` inside a Note — parsed as an arrow.
   - `<br/>` inside `participant ... as` labels — unreliable.
   - non-ASCII `×`, `→`, `⇒` — use `x`, `then`, `means`.
   Prefer plain ASCII and parentheses. Wrap participant aliases in quotes.

4. **Render + validate** with the helper (uses mermaid-cli via npx; non-zero exit
   = syntax error in the `.mmd`):

   ```bash
   scripts/render_execution_diagram.sh
   ```

   This regenerates `docs/diagrams/execution-sequence.svg`. If it fails, fix the
   `.mmd` (most often a forbidden character from step 3) and re-run. Never edit
   the SVG by hand.

5. **Keep the README prose honest.** If the wired/not-wired reality changed (e.g.
   the CLI now wires lifecycle), update the paragraph and the `> Maintenance:`
   note around the image markers in `README.md`, and reflect it in `AGENTS.md`
   Status if needed. The README image reference itself usually does not change
   (same SVG path).

6. **Stage all three together** in the same commit: the `.mmd`, the regenerated
   `.svg`, and any `README.md`/`AGENTS.md` prose changes.

7. **Report** a short summary: which participants/edges/markers changed, which
   stages flipped wired ↔ not-wired, and confirm the SVG re-rendered cleanly.

## Invariants (must hold after every update)

- The org multi-account path is the primary subject.
- Both triggers (CLI, Lambda) converge on the shared engine.
- Read-only semantics visible (list/describe only).
- Partial-failure isolation visible (per-account `alt`, per-collector note).
- `UNKNOWN` lifecycle is never drawn as silently `SUPPORTED`.
- Not-yet-wired stages are explicitly marked `(not wired)`.
- The `BEGIN/END: execution-sequence-diagram` markers are preserved; README shows
  the SVG image (clickable), not inline mermaid.
- The `.svg` is regenerated from the `.mmd` by `render_execution_diagram.sh`,
  never hand-edited.
