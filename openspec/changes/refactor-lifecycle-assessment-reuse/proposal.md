# Proposal

## Why

Lifecycle evaluation is already decoupled at the function level
(`evaluate_all(records, providers)` knows nothing about scans, accounts, or
regions), but there is **no product entry point that offers it as a reusable,
standalone step**. The only caller was a one-off runner (now removed). Meanwhile
`add-lambda-batch-execution` plans to fuse evaluation *into* `run_scan()`, making
every scan evaluate automatically — the opposite of a reusable, flow-independent
assessment. We want lifecycle assessment to be a first-class, composable service
that any flow (CLI, Lambda, future jobs, re-assessing a prior inventory) can
apply to an arbitrary set of records, without coupling it to discovery.

## What Changes

- Introduce a **lifecycle assessment service**: a small, stable facade over the
  existing evaluator + default provider factory that takes records (from any
  source) and returns records annotated with lifecycle fields. It owns provider
  construction (precedence AWS Health → EndOfLife) and non-fatal provider setup.
- Establish that **discovery and assessment are separate, composable steps**:
  `run_scan()` / `run_scan_multi_region()` / `run_org_scan()` produce records and
  SHALL NOT evaluate lifecycle themselves. A caller composes scan → assessment.
- **Reconcile `add-lambda-batch-execution`**: its current spec requires the engine
  to evaluate "every scanned record" at scan time. This change supersedes that:
  the Lambda (and CLI) SHALL compose the assessment service after scanning, not
  have `run_scan()` evaluate internally. The lambda-batch spec/tasks are updated
  to call the assessment service as a distinct step.
- The assessment service MUST be usable on records that did not come from a scan
  (e.g. loaded from a prior CSV), so lifecycle can be re-evaluated without
  re-discovering.
- No change to evaluation **semantics**: status set, precedence, UNKNOWN vs
  SUPPORTED vs NOT_APPLICABLE, evidence/provenance all unchanged.

## Capabilities

### Modified Capabilities
- `lifecycle-evaluation`: add requirements that lifecycle assessment is exposed as
  a reusable, flow-independent service with a stable input/output contract
  (records in → annotated records out), owning provider construction, usable on
  records from any source, and never coupled to discovery.
- `scan-orchestration`: add a requirement that the scan engine produces records
  without evaluating lifecycle; assessment is a separate composable step.

## Impact

- **New code:** `lifecycle/assessment.py` (service facade, e.g.
  `assess_records(records, session=None, ...)`) over `evaluator.evaluate_all` +
  `providers.default_lifecycle_providers`.
- **Modified code:** none of the evaluator internals; entrypoints (CLI, future
  Lambda) call the service as a step. `orchestration` stays discovery-only.
- **Supersedes:** `add-lambda-batch-execution` task 1.1 / its
  `lifecycle-evaluation` delta (evaluation at scan time). That change is updated
  to compose the assessment service instead. Must land before lambda-batch is
  implemented.
- **No behavior change** to lifecycle conclusions or CSV columns.
- **Docs/diagram:** execution-sequence diagram already shows lifecycle as a
  separate `(not wired)` step; update wording to "composable assessment step".
