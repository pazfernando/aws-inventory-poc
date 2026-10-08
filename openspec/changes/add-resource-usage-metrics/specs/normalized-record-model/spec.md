# Spec Delta

## Purpose

Add usage-assessment output fields to the shared record model and CSV contract,
appended after the existing columns, so usage results serialize alongside
discovery and lifecycle without breaking the column set.

## ADDED Requirements

### Requirement: Usage output fields

The record and CSV contract SHALL add usage fields `usage_status`,
`usage_metric`, `usage_value`, `usage_window_days`, `usage_source`, and
`usage_assessed_at`, appended after the existing columns without removing or
reordering any existing column. `usage_status` SHALL hold one of `IN_USE`,
`IDLE`, `NO_DATA`, `NO_METRIC`, with `NO_METRIC` serialized distinctly from
`IDLE` and `NO_DATA`.

#### Scenario: Usage columns appended

- **WHEN** records are written to CSV after usage assessment
- **THEN** the usage columns appear after the existing columns
- **AND** no existing column is removed or reordered

#### Scenario: Unassessed record has empty usage fields

- **WHEN** a record has not been through usage assessment
- **THEN** its usage fields are empty
- **AND** this is distinguishable from an assessed `IDLE` or `NO_METRIC` result

#### Scenario: NO_METRIC serialized distinctly

- **WHEN** a resource without a usage metric is written to CSV
- **THEN** its `usage_status` cell reads `NO_METRIC`
- **AND** `usage_value` is empty while remaining distinguishable from an `IDLE`
  row whose `usage_value` is zero
