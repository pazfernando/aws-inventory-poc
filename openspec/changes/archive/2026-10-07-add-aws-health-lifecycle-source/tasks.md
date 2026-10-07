# Tasks

## 1. Health provider

- [x] 1.1 Implement `aws_health.py` that prefetches Planned Lifecycle Events and builds an ARN index, exposing `match(record)`; verify a test (mocked Health responses) asserts an event is matched to a record by ARN and evidence is attached
- [x] 1.2 Implement evidence preservation (event identity, type, date, affected entity, affected-resource status, `lifecycle_source=AWS_HEALTH`); verify a test asserts all evidence fields are recorded

## 2. Precedence and no-false-inference

- [x] 2.1 Integrate the provider into the evaluator with Health-authoritative precedence while preserving curated provenance; verify a test asserts Health supplies the conclusion and curated provenance is not discarded
- [x] 2.2 Verify a test asserts a record with no matching Health event is never set to `SUPPORTED` on that basis

## 3. Non-fatal behavior

- [x] 3.1 Implement best-effort availability detection so access-denied/unsupported degrades to "unavailable"; verify a test shows the scan completes, other providers still run, and unmatched records remain `UNKNOWN` when Health is unavailable
- [x] 3.2 Add an end-to-end fixture running the scan with Health available and unavailable and verify inventory succeeds in both cases

## Workflow follow-up

- Run `openspec validate add-aws-health-lifecycle-source --strict` before archive.
- This is the first useful product milestone; archive after verification.
