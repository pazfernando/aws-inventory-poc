# Spec Delta

## Purpose

Define the serialization semantics of a non-version-bearing record so the shared
record model and CSV contract represent resources that have no version without
breaking the existing column set.

## MODIFIED Requirements

### Requirement: Lifecycle output fields

The record and CSV contract SHALL add the lifecycle fields `lifecycle_status`,
`eol_date`, `days_to_eol`, `lifecycle_source`, `lifecycle_evidence_id`, and
`evaluated_at`, appended after the baseline columns without removing any existing
column. The `lifecycle_status` column SHALL be able to hold `NOT_APPLICABLE` for
non-version-bearing records, serialized distinctly from both `UNKNOWN` and
`SUPPORTED`.

#### Scenario: Lifecycle columns appended

- **WHEN** records are written to CSV after lifecycle evaluation
- **THEN** the lifecycle columns appear after the baseline columns
- **AND** no baseline column is removed or reordered

#### Scenario: UNKNOWN serialized distinctly

- **WHEN** a record has lifecycle status `UNKNOWN`
- **THEN** its `lifecycle_status` cell reads `UNKNOWN`
- **AND** `eol_date`, `days_to_eol`, `lifecycle_source`, and
  `lifecycle_evidence_id` are empty while remaining distinguishable from a
  `SUPPORTED` row

#### Scenario: NOT_APPLICABLE serialized for no-version records

- **WHEN** a non-version-bearing record is written to CSV
- **THEN** its `version`, `software_type`, and `software_name` cells are empty
- **AND** its `lifecycle_status` cell reads `NOT_APPLICABLE`
- **AND** `eol_date`, `days_to_eol`, `lifecycle_source`, and
  `lifecycle_evidence_id` are empty
