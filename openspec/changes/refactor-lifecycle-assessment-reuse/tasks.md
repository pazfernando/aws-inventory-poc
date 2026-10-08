# Tasks

## 1. Assessment service

- [ ] 1.1 Add `lifecycle/assessment.py` with
  `assess_records(records, *, session=None, providers=None, today=None,
  health_region="us-east-1") -> list[ResourceVersionRecord]`: build default
  providers when none given, else use the supplied list; delegate to
  `evaluate_all`. `session=None` skips AWS Health non-fatally.
- [ ] 1.2 Export it from `lifecycle/__init__.py` (stable public surface).
- [ ] 1.3 Unit tests: records-in/records-out annotation; default-provider path;
  caller-supplied providers path; `session=None` completes (EndOfLife only);
  non-version-bearing records stay NOT_APPLICABLE; UNKNOWN stays distinct from
  SUPPORTED.

## 2. Scan stays discovery-only (contract)

- [ ] 2.1 Confirm/assert `run_scan`, `run_scan_multi_region`, `run_org_scan`
  contain no lifecycle evaluation; add a regression test asserting scan output
  has default (unevaluated) lifecycle fields.
- [ ] 2.2 Add a composition test: `run_scan(...)` then `assess_records(...)`
  yields populated lifecycle fields, proving the two steps compose.

## 3. Reconcile add-lambda-batch-execution

- [ ] 3.1 Update that change's `proposal.md`: lifecycle is applied by composing
  the assessment service after `run_scan()` (CLI and Lambda), not fused into
  `run_scan()`.
- [ ] 3.2 Update its `specs/lifecycle-evaluation/spec.md` delta: replace
  "engine evaluates every scanned record" with "entry points compose the
  assessment service after scanning".
- [ ] 3.3 Update its `tasks.md` (task 1.x) to call `assess_records()` as a step.
- [ ] 3.4 `openspec validate add-lambda-batch-execution --strict` passes.

## 4. CLI composition (optional but included)

- [ ] 4.1 CLI `run()` composes `assess_records(result.records, session=...)`
  before `write_csv`, so `inventory.csv` carries lifecycle fields; keep it a
  distinct step (scan → assess → write).
- [ ] 4.2 Test: CLI output CSV has populated lifecycle columns.

## 5. Docs + diagram

- [ ] 5.1 Update the execution-sequence diagram wording: lifecycle is a
  "composable assessment step" (regenerate `.mmd` + `.svg` via the skill).
- [ ] 5.2 Update `AGENTS.md` status to describe the assessment service and the
  discovery/assessment separation.
- [ ] 5.3 README: note the assessment step (scan → assess → CSV).

## 6. Validation

- [ ] 6.1 `openspec validate refactor-lifecycle-assessment-reuse --strict` passes.
- [ ] 6.2 `python -m pytest -s` passes.
