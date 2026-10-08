# Proposal

## Why

The tool today only discovers *version-bearing* resources (Lambda, RDS, EKS, …)
because its purpose is lifecycle/EOL evaluation. But a side-by-side run against
account `179733518853` showed a peer inventory collector reporting many resources
this tool ignores entirely — EC2, VPC, DynamoDB, SNS, SQS, EFS, CloudFormation,
Route53. For a complete account inventory (and as the foundation for a later
usage/utilization capability), the tool must also enumerate these resources even
though they carry no software version to evaluate for end-of-life.

## What Changes

- Add discovery of eight **non-version-bearing** resource groups via read-only
  direct AWS APIs: EC2 instances, VPCs, DynamoDB tables, SNS topics, SQS queues,
  EFS file systems, CloudFormation stacks and stacksets, and Route53 hosted
  zones.
- Reuse the existing `ResourceVersionRecord`: these records carry an empty
  `version`/`software_*` and are marked with a new lifecycle status
  **`NOT_APPLICABLE`** (distinct from `UNKNOWN`), signalling "this resource has no
  version to evaluate" rather than "we lack evidence".
- The lifecycle evaluator SHALL skip non-version-bearing records (no provider is
  consulted; status stays `NOT_APPLICABLE`), preserving the "no invented
  versions" and "UNKNOWN distinct from SUPPORTED" principles.
- New collectors register into the shared engine the same way as existing ones,
  so multi-region and multi-account (org) scans cover them automatically.
- CSV contract unchanged structurally: same columns; non-version-bearing rows
  simply have empty version/lifecycle-evidence cells and
  `lifecycle_status=NOT_APPLICABLE`.
- **Out of scope (future spec):** usage/utilization metrics (invocations,
  throughput, idle detection). This change only establishes *presence/inventory*.

## Capabilities

### New Capabilities
- `general-resource-inventory`: read-only discovery of non-version-bearing AWS
  resources (EC2, VPC, DynamoDB, SNS, SQS, EFS, CloudFormation
  stacks/stacksets, Route53), normalized into the shared record model as
  presence records with no version.

### Modified Capabilities
- `lifecycle-evaluation`: add `NOT_APPLICABLE` to the lifecycle status set and
  require the evaluator to assign it (without consulting providers) to records
  that carry no version, keeping it distinct from `UNKNOWN`.
- `normalized-record-model`: define the semantics of a non-version-bearing
  record (empty `version`/`software_*`, `lifecycle_status=NOT_APPLICABLE`) and
  confirm the CSV serialization of that case.

## Impact

- **New code:** collectors under `src/aws_lifecycle_inventory/inventory/direct_api/`
  (one per resource group) registered in `default_collectors()`.
- **Modified code:** `lifecycle/models.py` (add `NOT_APPLICABLE`),
  `lifecycle/evaluator.py` (skip no-version records), possibly `models.py`
  docstring/semantics.
- **IAM:** additional read-only actions (ec2, dynamodb, sns, sqs, elasticfilesystem,
  cloudformation, route53) — documented in README.
- **Diagram:** the execution-sequence diagram gains the new discovery scope; the
  pre-commit nudge already covers `inventory/`.
- **No breaking change** to the CSV column set; `NOT_APPLICABLE` is a new value in
  an existing column.
