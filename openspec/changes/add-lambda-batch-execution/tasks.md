# Tasks

## 1. Lambda handler

- [ ] 1.1 Implement a Lambda handler that parses a scan-scope event (accounts/regions) and calls the shared `run_scan()`; verify a test invokes the handler with a scope and asserts the engine is called with exactly that scope
- [ ] 1.2 Write the resulting CSV to S3 with a deterministic timestamped key via `s3:PutObject`; verify a moto S3 test asserts an object is written at the expected key pattern

## 2. Semantic equivalence and packaging

- [ ] 2.1 Reuse the CLI output writer and engine so semantics match; verify an equivalence test runs the same scope through the CLI and the handler and asserts identical normalized records and columns
- [ ] 2.2 Package dependencies for Lambda (layer or slim bundle) and verify a cold-import smoke test of the handler module succeeds

## Workflow follow-up

- Run `openspec validate add-lambda-batch-execution --strict` before archive.
- Archive after comparing representative CLI and Lambda outputs for equivalent scope.
