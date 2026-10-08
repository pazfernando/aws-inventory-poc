# Tasks

## 1. Record model + CSV

- [ ] 1.1 Add usage fields to `ResourceVersionRecord`: `usage_status`,
  `usage_metric`, `usage_value`, `usage_window_days`, `usage_source`,
  `usage_assessed_at` (empty/None defaults; unassessed is distinct from assessed).
- [ ] 1.2 Append `USAGE_COLUMNS` after `COVERAGE_COLUMNS` in `output/csv_writer.py`;
  never reorder/remove existing columns.
- [ ] 1.3 Test: usage columns appended; unassessed record has empty usage cells;
  `NO_METRIC` distinct from `IDLE` (value 0) and `NO_DATA`.

## 2. Usage status + registry

- [ ] 2.1 Define usage status set `IN_USE`, `IDLE`, `NO_DATA`, `NO_METRIC`.
- [ ] 2.2 Add a metric registry keyed by `resource_type` (namespace, metric,
  statistic, dimension builder) for Lambda, DynamoDB, RDS instance/cluster, SQS,
  SNS; everything else → no entry (NO_METRIC).

## 3. Usage assessment service

- [ ] 3.1 Add `usage/assessment.py` with
  `assess_usage(records, *, session, window_days=30, today=None) ->
  list[ResourceVersionRecord]`: registry lookup; NO_METRIC without a CloudWatch
  call; else batched `GetMetricData` over the window; classify IN_USE/IDLE/NO_DATA;
  record activity value, metric, window, source, assessed_at.
- [ ] 3.2 Partial-failure isolation: a failed/denied query yields an explicit
  no-result for that record; others still assessed; never fabricate a value.
- [ ] 3.3 Read-only: only CloudWatch read APIs.
- [ ] 3.4 Export from `usage/__init__.py` (stable public surface), flow-independent
  (usable on records from any source, no scan required).

## 4. Tests

- [ ] 4.1 Unit tests with mocked/stubbed CloudWatch: IN_USE (invocations > 0),
  IDLE (metric, zero activity), NO_DATA (no datapoints), NO_METRIC (unmapped type
  — no CloudWatch call made).
- [ ] 4.2 Window: default 30 days; caller override reflected in `usage_window_days`.
- [ ] 4.3 Partial-failure test: one query fails, others still assessed.
- [ ] 4.4 Composition test: records from a scan → `assess_usage` populates usage
  fields; service also runs on records not from a scan.

## 5. Composition (opt-in)

- [ ] 5.1 Allow CLI/Lambda to run usage assessment as an optional step
  (off by default) after discovery (and optional lifecycle assessment), before
  CSV write; keep each a distinct composable step.
- [ ] 5.2 Test: when enabled, the output CSV carries populated usage columns; when
  not enabled, usage columns are empty.

## 6. Docs + diagram

- [ ] 6.1 README: add `cloudwatch:GetMetricData` read-only IAM action and document
  the opt-in usage step (scan → assess lifecycle → assess usage → CSV).
- [ ] 6.2 Update the execution-sequence diagram: add usage assessment as a
  composable (opt-in) step; regenerate `.mmd` + `.svg` via the skill.
- [ ] 6.3 Update `AGENTS.md` status/structure (new `usage/` package, usage
  columns, four-state usage signal).

## 7. Validation

- [ ] 7.1 `openspec validate add-resource-usage-metrics --strict` passes.
- [ ] 7.2 `python -m pytest -s` passes.
- [ ] 7.3 Optional live check against account 179733518853 (us-east-1,us-east-2):
  usage signal for Lambda/DynamoDB/RDS/SNS/SQS; confirm NO_METRIC for VPC/Route53/
  CloudFormation.
