# Proposal

## Why

The proven scan engine should run unattended as a scheduled batch. Running it as
an AWS Lambda lets the same core engine execute on a schedule and deposit reports
centrally, without rewriting discovery or evaluation logic.

## What Changes

- Add a batch-execution capability: a Lambda handler that accepts a scan scope
  (accounts/regions) and invokes the same shared core engine as the CLI.
- Apply lifecycle evaluation by **composing the reusable assessment service**
  (`lifecycle.assess_records`) after `run_scan()` — the same discrete step the CLI
  uses — so CLI and Lambda CSVs carry populated lifecycle columns. The scan engine
  stays discovery-only (see `refactor-lifecycle-assessment-reuse`); evaluation is
  NOT fused into `run_scan()`.
- Write the output CSV to S3 using a deterministic, timestamped report key.
- Preserve identical normalized semantics between CLI and Lambda for equivalent
  scope and permissions.

## Capabilities

### New Capabilities
- `batch-execution`: Lambda-based execution of the shared scan engine with S3
  CSV output and CLI-equivalent semantics.

### Modified Capabilities

- `lifecycle-evaluation`: entry points (CLI and Lambda) compose the reusable
  assessment service after scanning; the scan engine itself does not evaluate
  lifecycle (evaluation semantics unchanged).

## Impact

- `orchestration.run_scan()` stays discovery-only; entry points compose
  `lifecycle.assess_records()` over collected records (AWS Health unavailability
  stays non-fatal).
- New Lambda handler module reusing `orchestration.run_scan()` and the shared
  assessment service.
- IAM: existing read-only scan permissions plus `s3:PutObject` to the report
  bucket/prefix.
- Packaging for Lambda (dependencies/layer) and a configurable S3 destination.
