# Proposal

## Why

Inventory is proven, but it does not yet answer "is this version supported,
approaching EOL, or unsupported?" Lifecycle semantics must be introduced
independently of discovery so collectors never own deprecation policy.

## What Changes

- Introduce a lifecycle evaluation model with states: `SUPPORTED`, `EOL_365`,
  `EOL_180`, `EOL_90`, `EOL_30`, `EOL`, `UNSUPPORTED`, `UNKNOWN`.
- Add a `LifecycleProvider` abstraction (`match(record) -> LifecycleEvidence | None`)
  so lifecycle evidence comes from pluggable providers, not collectors.
- Add a first curated provider as the initial evidence source.
- Every non-`UNKNOWN` conclusion MUST carry evidence; absence of evidence yields
  `UNKNOWN`, which MUST remain distinguishable from `SUPPORTED`.
- Extend the record and CSV with lifecycle fields: `lifecycle_status`,
  `eol_date`, `days_to_eol`, `lifecycle_source`, `lifecycle_evidence_id`,
  `evaluated_at`.

## Capabilities

### New Capabilities
- `lifecycle-evaluation`: Provider-based evaluation of a resource's version into a
  lifecycle status with preserved evidence, independent of inventory.

### Modified Capabilities
- `normalized-record-model`: add lifecycle output fields to the record/CSV
  contract without retiring existing columns.

## Impact

- New `src/aws_lifecycle_inventory/lifecycle/` (`evaluator.py`, `providers/`).
- CSV gains lifecycle columns appended after baseline columns.
- No new AWS IAM (curated provider is local data); AWS-sourced lifecycle is
  Change 05.
