# Proposal

## Why

Organizations run many accounts. The tool must scan multiple AWS accounts using
cross-account read-only access (and/or an accepted centralized source) while
isolating accounts and preserving account provenance.

## What Changes

- Add an account-access capability using configurable STS AssumeRole into target
  accounts with read-only permissions.
- Extend scan-orchestration to iterate accounts, isolating each account's failures
  and recording account provenance on every record.
- Continue when one account is inaccessible rather than aborting.
- Evaluate, per the Change 03 decision, Config Aggregator (if `HYBRID`/
  `CONFIG_PRIMARY`) versus cross-account direct-API fan-out as the org-wide
  inventory source.
- Evaluate organization-level AWS Health visibility versus per-account access.

## Capabilities

### New Capabilities
- `account-access`: Cross-account read-only access via STS AssumeRole with
  per-account isolation and provenance.

### Modified Capabilities
- `scan-orchestration`: extend execution to iterate multiple accounts and include
  account in the execution summary and provenance.

## Impact

- New account-access module; `orchestration.py` iterates accounts × regions.
- IAM: a read-only role assumable in each target account; `sts:AssumeRole` in the
  running principal.
- Aggregation strategy depends on Change 03's recorded decision.
