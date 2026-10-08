# Proposal

## Why

The proven scan engine should run unattended as a scheduled batch. Running it as
an AWS Lambda lets the same core engine execute on a schedule and deposit reports
centrally, without rewriting discovery or evaluation logic.

## What Changes

- Add a batch-execution capability: a Lambda handler that accepts a scan scope
  (accounts/regions) and invokes the same shared core engine as the CLI.
- Wire lifecycle evaluation into the shared scan engine: after collection,
  `run_scan()` evaluates each record through the ordered providers (AWS Health
  then EndOfLife) so CLI and Lambda CSVs carry populated lifecycle columns.
- Write the output CSV to S3 using a deterministic, timestamped report key.
- Preserve identical normalized semantics between CLI and Lambda for equivalent
  scope and permissions.

## Capabilities

### New Capabilities
- `batch-execution`: Lambda-based execution of the shared scan engine with S3
  CSV output and CLI-equivalent semantics.

### Modified Capabilities

- `lifecycle-evaluation`: provider evaluation now runs at scan time inside the
  shared engine (evaluation semantics unchanged).

## Impact

- `orchestration.run_scan()` gains a lifecycle evaluation pass over collected
  records; AWS Health unavailability stays non-fatal.
- New Lambda handler module reusing `orchestration.run_scan()`.
- IAM: existing read-only scan permissions plus `s3:PutObject` to the report
  bucket/prefix.
- Packaging for Lambda (dependencies/layer) and a configurable S3 destination.
