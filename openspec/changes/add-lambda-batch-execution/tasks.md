# Tasks

## 1. Lifecycle assessment composition

- [ ] 1.1 Compose the reusable assessment service (`lifecycle.assess_records`) as a discrete step after `run_scan()` in the shared entry-point path (CLI and Lambda); verify a moto test asserts the composed output carries populated lifecycle columns and UNKNOWN stays distinct from SUPPORTED. Do NOT evaluate inside `run_scan()` (the engine stays discovery-only).
- [ ] 1.2 Keep AWS Health unavailability non-fatal in the assessment step; verify a stub-client test asserts evaluation falls back to EndOfLife/UNKNOWN per precedence and the run completes

## 2. Lambda handler

- [ ] 2.1 Implement a Lambda handler that parses a scan-scope event (accounts/regions) and calls the shared `run_scan()`; verify a test invokes the handler with a scope and asserts the engine is called with exactly that scope
- [ ] 2.2 Write the resulting CSV to S3 with a deterministic timestamped key via `s3:PutObject`; verify a moto S3 test asserts an object is written at the expected key pattern

## 3. Semantic equivalence and packaging

- [ ] 3.1 Reuse the CLI output writer and engine so semantics match; verify an equivalence test runs the same scope through the CLI and the handler and asserts identical normalized records, columns, and populated lifecycle fields in both
- [ ] 3.2 Package dependencies for Lambda (layer or slim bundle) and verify a cold-import smoke test of the handler module succeeds

## Workflow follow-up

- Run `openspec validate add-lambda-batch-execution --strict` before archive.
- Archive after comparing representative CLI and Lambda outputs for equivalent scope.
