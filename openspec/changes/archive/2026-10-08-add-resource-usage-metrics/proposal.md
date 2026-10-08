# Proposal

## Why

We inventory resources but cannot yet tell whether they are actually used. The
peer collector's logs showed activity signals (Lambda invocations, DynamoDB
throughput, RDS connections, SNS/SQS message volume) that answer the key
decommission question: *is this resource in use or idle?* We want that signal as a
reusable, composable feature — invocable on its own and chainable into a run
(scan → lifecycle assessment → usage assessment → CSV) — following the same
"separate, composable step" pattern as lifecycle assessment.

## What Changes

- Introduce a **usage assessment service**: a standalone, flow-independent step
  that takes normalized records and annotates each with a usage signal derived
  from read-only CloudWatch metrics over a configurable window (default 30 days).
- Each assessed record gains: a **usage status** (`IN_USE`, `IDLE`, `NO_DATA`,
  `NO_METRIC`), the **activity value** that justifies it (e.g. invocation/connection
  count in the window — useful to see whether a resource was ever used), the
  **metric/source** used, the **window in days**, and an **assessed-at** timestamp.
- Per-resource metric mapping (read-only CloudWatch `GetMetricData`):
  - Lambda → `Invocations` (sum)
  - DynamoDB → consumed read+write throughput (sum)
  - RDS instance/cluster → `DatabaseConnections` (sum/max)
  - SQS → `NumberOfMessagesSent`/`NumberOfMessagesReceived` (sum)
  - SNS → `NumberOfMessagesPublished` (sum)
  - Resources with no meaningful usage metric (VPC, EFS where not applicable,
    CloudFormation, Route53) → `NO_METRIC` (never a false `IDLE`).
- **Composable and independent**: the service does not require a scan; it runs on
  records from any source. A run composes it as a distinct step after discovery
  (and optionally after lifecycle assessment).
- CSV contract: append new usage columns after existing columns; never reorder or
  remove. Resources without a metric are explicit (`NO_METRIC`), distinct from
  `IDLE` (has a metric, no activity) and `NO_DATA` (metric exists but no datapoints).
- **Out of scope (later):** cost data, rightsizing recommendations, automated
  decommission actions. This is read-only signal only.

## Capabilities

### New Capabilities
- `resource-usage-metrics`: read-only, flow-independent assessment that derives a
  per-resource usage signal (in-use / idle / no-data / no-metric) plus the
  supporting activity value from CloudWatch over a configurable window.

### Modified Capabilities
- `normalized-record-model`: add usage output fields (`usage_status`,
  `usage_metric`, `usage_value`, `usage_window_days`, `usage_source`,
  `usage_assessed_at`) appended to the CSV contract without removing or reordering
  existing columns; `NO_METRIC` stays distinct from `IDLE` and `NO_DATA`.

## Impact

- **New code:** `usage/` package — a service facade
  `assess_usage(records, *, session, window_days=30, today=None)` plus a
  per-resource-type metric registry; CloudWatch `GetMetricData` client usage.
- **Modified code:** `models.py` (usage fields), `output/csv_writer.py` (append
  usage columns). Scan engine untouched (discovery-only, per the assessment
  pattern).
- **IAM:** `cloudwatch:GetMetricData` (read-only) — documented in README.
- **Composition:** CLI/Lambda may add usage assessment as an optional step; it is
  off unless requested, keeping default scans cheap.
- **No breaking change** to existing columns.
- **Depends on** the discovery/assessment separation established by
  `refactor-lifecycle-assessment-reuse` (usage follows the same composable shape).
