# Design

## Context

We established a "separate, composable step" pattern with
`refactor-lifecycle-assessment-reuse`: discovery produces records; assessment
services annotate them. Usage metrics follow the same shape — a standalone
`assess_usage(records, *, session, window_days=30, ...)` service over read-only
CloudWatch, independent of the scan flow, composable into a run.

The peer collector proved the signal is available via CloudWatch (invocations,
throughput, connections, message counts). The honest constraint: not every
inventoried resource has a meaningful usage metric, so the model must express
`NO_METRIC` distinctly rather than mislabel such resources `IDLE`.

## Goals / Non-Goals

**Goals**
- One reusable usage service, invocable alone and composable in a run.
- Per-resource-type metric registry; easy to extend.
- Clear four-state signal: IN_USE / IDLE / NO_DATA / NO_METRIC.
- Retain the activity value (e.g. invocation/connection count) — answers "was it
  ever used in the window".

**Non-Goals**
- No cost, rightsizing, or decommission actions.
- No change to the scan engine (stays discovery-only).
- No per-resource metric beyond a sensible default each (extensible later).

## Decisions

### Decision: Service facade `usage/assessment.py`
`assess_usage(records, *, session, window_days=30, today=None) ->
list[ResourceVersionRecord]`:
- For each record, look up its metric spec by `resource_type` in a registry.
- No spec → annotate `usage_status=NO_METRIC` (no CloudWatch call).
- Spec present → query CloudWatch `GetMetricData` for the window; classify:
  - datapoints with sum > 0 → `IN_USE`, `usage_value` = aggregated activity
  - datapoints all zero → `IDLE`, `usage_value` = 0
  - no datapoints returned → `NO_DATA`
  - query error/denied → explicit no-result (`NO_DATA` with empty value + source
    note), never fabricated.
- Mirrors the lifecycle service signature and non-fatal posture.

### Decision: Metric registry keyed by resource_type
A small table mapping `resource_type` → (namespace, metric_name, dimension
builder, statistic). Initial entries:

| resource_type | namespace | metric | stat | dimension |
|---|---|---|---|---|
| AWS::Lambda::Function | AWS/Lambda | Invocations | Sum | FunctionName |
| AWS::DynamoDB::Table | AWS/DynamoDB | ConsumedRead+WriteCapacityUnits | Sum | TableName |
| AWS::RDS::DBInstance | AWS/RDS | DatabaseConnections | Sum | DBInstanceIdentifier |
| AWS::RDS::DBCluster | AWS/RDS | DatabaseConnections | Sum | DBClusterIdentifier |
| AWS::SQS::Queue | AWS/SQS | NumberOfMessagesSent | Sum | QueueName |
| AWS::SNS::Topic | AWS/SNS | NumberOfMessagesPublished | Sum | TopicName |

Everything else (VPC, EFS*, CloudFormation, Route53, and all version-bearing
compute like EKS/MSK/etc. not listed) → `NO_METRIC` for now; extend the registry
in later changes. *EFS does have metrics; left out of the initial set to keep
scope tight — add when prioritized.

- **Alternative rejected:** one CloudWatch call per metric per resource without
  batching. `GetMetricData` supports many queries per call; batch to stay within
  limits and reduce latency.

### Decision: Dimension values come from the record
Use `resource_id` as the dimension value (we set it to the name/id CloudWatch
expects: FunctionName, TableName, QueueName, TopicName, DB identifiers). Route53's
id would not map to a usage dimension anyway (NO_METRIC).

### Decision: Composition, not coupling
`run_scan*` stays discovery-only. CLI/Lambda compose:
`records = run_scan(...); records = assess_records(...); records =
assess_usage(records, session=..., window_days=...)` then write CSV. Usage is
**opt-in** (off by default) so normal scans stay cheap and cheap on CloudWatch.

### Decision: New CSV columns appended
Add `usage_status, usage_metric, usage_value, usage_window_days, usage_source,
usage_assessed_at` after the coverage column. Empty when unassessed (distinct from
an assessed result).

## Risks / Trade-offs

- **CloudWatch cost/limits** at org scale (many resources × GetMetricData).
  Mitigation: batch queries, opt-in, bounded window. Partial failures isolated.
- **Metric nuances** (e.g. DynamoDB on-demand vs provisioned emit different
  metrics; serverless Lambda aliases). Mitigation: start with the most universal
  metric per type; `NO_DATA` is a valid, honest outcome.
- **`usage_value` units differ per metric** (count vs capacity units). The record
  carries `usage_metric` so the value is interpretable; we do not normalize units.

## Open Questions

- Classification threshold for `IN_USE`: strictly `> 0`, or a configurable minimum
  (e.g. ignore a single stray invocation)? Proposed: `> 0` now, configurable
  threshold later. Confirm during apply.
- Aggregation statistic per metric (Sum vs Average vs Max) — proposed defaults in
  the registry above; revisit per metric if misleading.
