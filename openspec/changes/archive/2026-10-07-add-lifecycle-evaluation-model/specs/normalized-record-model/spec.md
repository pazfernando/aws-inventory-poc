# Spec Delta

## ADDED Requirements

### Requirement: Lifecycle output fields
The record and CSV contract SHALL add the lifecycle fields `lifecycle_status`,
`eol_date`, `days_to_eol`, `lifecycle_source`, `lifecycle_evidence_id`, and
`evaluated_at`, appended after the baseline columns without removing any existing
column.

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
