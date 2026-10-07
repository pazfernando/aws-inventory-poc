# normalized-record-model Specification

## Purpose
Defines the single normalized record model and its CSV serialization contract
shared by every inventory source and lifecycle provider across the tool.

## Requirements

### Requirement: Normalized record schema
The system SHALL define one normalized `ResourceVersionRecord` carrying at least:
`account_id`, `region`, `resource_type`, `resource_id`, `resource_arn`,
`software_type`, `software_name`, `version`, `inventory_source`, `collected_at`.

#### Scenario: Record exposes baseline fields
- **WHEN** a collector emits a record for a discovered resource
- **THEN** the record exposes all baseline fields
- **AND** `collected_at` is an ISO-8601 UTC timestamp
- **AND** `inventory_source` identifies the source that produced it

### Requirement: Provenance is preserved
Every record SHALL record its `inventory_source`, and the model SHALL NOT silently
overwrite a field value from one source with a conflicting value from another.

#### Scenario: Source recorded on every record
- **WHEN** a record is produced by the direct-API baseline
- **THEN** its `inventory_source` is set to `DIRECT_API`

### Requirement: Stable CSV serialization
The system SHALL serialize records to CSV with a fixed, ordered baseline column
set, and SHALL NOT silently remove an existing column as the schema evolves.

#### Scenario: Deterministic column order
- **WHEN** records are written to CSV
- **THEN** the header row lists the baseline columns in a fixed order
- **AND** every data row aligns its values to that column order

#### Scenario: Empty values are represented explicitly
- **WHEN** a record has an empty `version`
- **THEN** the corresponding CSV cell is empty rather than omitted or defaulted

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
