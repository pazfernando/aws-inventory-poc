# Spec Delta

## Purpose

Runs the shared scan engine as an AWS Lambda batch process, writing CSV reports to
S3 while preserving the same normalized semantics as the CLI.

## ADDED Requirements

### Requirement: Shared core engine
The CLI and the Lambda handler SHALL invoke the same core scan engine; the Lambda
SHALL NOT reimplement discovery or evaluation logic.

#### Scenario: Handler delegates to the core engine
- **WHEN** the Lambda handler is invoked
- **THEN** it calls the same shared scan engine used by the CLI

### Requirement: Scan scope input
The Lambda handler SHALL accept a scan scope specifying accounts and regions.

#### Scenario: Scope honored
- **WHEN** the handler is invoked with a scope of specific accounts and regions
- **THEN** the scan covers exactly those accounts and regions

### Requirement: S3 CSV output with deterministic key
The handler SHALL write the output CSV to S3 using a deterministic, timestamped
report key.

#### Scenario: Report written to S3
- **WHEN** a Lambda scan completes
- **THEN** a CSV object is written to the configured S3 bucket/prefix
- **AND** its key includes a timestamp and is deterministic for the given scope/run

### Requirement: CLI/Lambda semantic equivalence
For equivalent scope and permissions, the Lambda output SHALL carry the same
normalized semantics as the CLI output.

#### Scenario: Equivalent outputs
- **WHEN** the CLI and Lambda run the same scope with the same permissions
- **THEN** their normalized records and columns are equivalent
