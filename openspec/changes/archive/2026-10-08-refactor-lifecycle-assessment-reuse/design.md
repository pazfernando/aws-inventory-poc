# Design

## Context

Lifecycle evaluation is already a standalone layer: `evaluator.evaluate_all(
records, providers)` is pure (records + providers → annotated records) and
`providers.default_lifecycle_providers(session)` builds the ordered
`[AWS Health, EndOfLife]` list non-fatally. What is missing is a single, named
**service facade** that ties these together with a stable signature, plus an
explicit contract that discovery and assessment are separate composable steps.

The only prior caller was a removed one-off runner. `add-lambda-batch-execution`
currently specifies fusing evaluation into `run_scan()`; this change supersedes
that in favor of composition.

## Goals / Non-Goals

**Goals**
- One reusable assessment entry point usable by CLI, Lambda, and re-assessment of
  prior records.
- Keep `run_scan*` discovery-only.
- Reconcile the lambda-batch plan to compose, not fuse.

**Non-Goals**
- No change to evaluation semantics (status set, precedence, UNKNOWN/NOT_APPLICABLE,
  evidence/provenance).
- No new providers.
- No CLI subcommand for re-assessing a CSV in this change (the service makes it
  possible; a subcommand can be a later change).

## Decisions

### Decision: Thin service facade `lifecycle/assessment.py`
Add `assess_records(records, *, session=None, providers=None, today=None,
health_region="us-east-1") -> list[ResourceVersionRecord]`:
- If `providers` is None, build them via `default_lifecycle_providers(session,
  health_region)`.
- Delegate to `evaluate_all(records, providers, today=today)`.
- `session=None` is valid: AWS Health is skipped (non-fatal), EndOfLife still runs.

Rationale: smallest possible surface that satisfies "reusable, owns provider
construction, flow-independent, caller-overridable". It adds no new semantics —
just a stable seam.

- **Alternative rejected:** a class `LifecycleAssessor`. A function is enough; a
  class adds ceremony without state worth holding across calls.

### Decision: Scan stays discovery-only
Do not add lifecycle to `run_scan*`. Instead, callers compose:
`records = run_scan(...); assessed = assess_records(records, session=...)`.
This is the crux of "independent of the flow".

### Decision: Supersede lambda-batch's scan-time evaluation
Update `add-lambda-batch-execution` so its lifecycle wiring composes
`assess_records()` after `run_scan()` (CLI and Lambda both), rather than
`run_scan()` evaluating internally. Its `lifecycle-evaluation` delta requirement
"Engine evaluates every scanned record" is replaced by "Entry points compose the
assessment service after scanning".
- Done in this change by editing that in-flight change's artifacts (it is not yet
  implemented or archived), so the two changes stay coherent.

### Decision: CLI wiring is optional here
The CLI may start calling `assess_records()` after its scan so `inventory.csv`
carries lifecycle fields. This is a natural, low-risk composition and is included
as a task, but the core deliverable is the service + the discovery/assessment
separation contract.

## Risks / Trade-offs

- **Double-coordination with lambda-batch.** Editing another in-flight change's
  artifacts risks drift. Mitigation: do it in the same change and re-validate both
  with `openspec validate --strict`.
- **Perceived regression**: someone expecting `run_scan` to populate lifecycle
  will now get defaults. Mitigation: the contract is explicit in the spec and the
  CLI composition keeps the end-to-end CSV populated.

## Open Questions

- Should `assess_records` accept an already-built provider list AND a session
  simultaneously? Proposed: if `providers` is given, ignore `session` (explicit
  wins). Confirm during apply.
