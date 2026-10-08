# Spec Delta

## Purpose

A read-only, flow-independent assessment that derives a per-resource usage signal
(in-use / idle / no-data / no-metric) and the supporting activity value from
CloudWatch over a configurable window, so callers can tell whether a resource is
actually used. It is composable: a discrete step usable on records from any source.

## ADDED Requirements

### Requirement: Reusable, flow-independent usage assessment

The system SHALL expose usage assessment as a standalone service that accepts a
list of normalized records from any source and returns them annotated with a usage
signal. It SHALL NOT require a scan and SHALL be invocable as a discrete,
composable step.

#### Scenario: Assess records without a scan

- **WHEN** a caller passes normalized records (from a scan, a loaded CSV, or any
  source) to the usage assessment service
- **THEN** the service returns the records annotated with usage fields
- **AND** it performs no resource discovery

#### Scenario: Composed as a distinct step

- **WHEN** a run needs usage results
- **THEN** it composes discovery and usage assessment as separate steps
- **AND** usage assessment is reusable independently of discovery and of lifecycle
  assessment

### Requirement: Usage status classification

The service SHALL classify each resource into exactly one usage status:
`IN_USE`, `IDLE`, `NO_DATA`, `NO_METRIC`. `IN_USE` means activity above zero in the
window; `IDLE` means a usage metric exists but shows no activity; `NO_DATA` means
the metric exists but returned no datapoints; `NO_METRIC` means the resource type
has no meaningful usage metric. `NO_METRIC` SHALL remain distinct from `IDLE` and
`NO_DATA`, and the service SHALL NOT report a resource without a usage metric as
`IDLE`.

#### Scenario: Active resource is IN_USE

- **WHEN** a Lambda function had invocations greater than zero within the window
- **THEN** its usage status is `IN_USE`
- **AND** the supporting activity value is recorded

#### Scenario: Metric present but no activity is IDLE

- **WHEN** a resource has a usage metric but zero activity across the window
- **THEN** its usage status is `IDLE`

#### Scenario: Resource type without a usage metric is NO_METRIC

- **WHEN** a resource type has no meaningful usage metric (for example a VPC or a
  Route53 hosted zone)
- **THEN** its usage status is `NO_METRIC`
- **AND** it is not reported as `IDLE` or `NO_DATA`

### Requirement: CloudWatch-sourced over a configurable window

Usage SHALL be derived from read-only CloudWatch metrics over a configurable
observation window that defaults to 30 days. The assessed record SHALL carry the
activity value, the metric used, the window length in days, and the source.

#### Scenario: Default 30-day window

- **WHEN** no window is specified
- **THEN** the service evaluates activity over the last 30 days

#### Scenario: Caller overrides the window

- **WHEN** a caller specifies a window of N days
- **THEN** activity is evaluated over the last N days
- **AND** the recorded window length reflects N

### Requirement: Partial failures isolated

A CloudWatch query failure for one resource or metric SHALL NOT abort the
assessment of other resources; the affected record SHALL carry an explicit
no-result signal rather than a fabricated value.

#### Scenario: One metric query fails

- **WHEN** the CloudWatch query for one resource fails or is denied
- **THEN** that resource is annotated with an explicit no-result usage signal
- **AND** the remaining resources are still assessed

### Requirement: Read-only

Usage assessment SHALL only issue read-only CloudWatch API calls and SHALL NOT
modify any scanned resource.

#### Scenario: No mutation

- **WHEN** usage assessment runs
- **THEN** only read-only metric queries are issued
