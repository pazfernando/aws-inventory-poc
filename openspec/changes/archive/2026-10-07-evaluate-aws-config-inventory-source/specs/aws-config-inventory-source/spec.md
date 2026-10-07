# Spec Delta

## Purpose

An optional AWS Config-backed inventory source that detects Config availability,
normalizes Config data into the shared record model, and is measured against the
direct-API baseline to produce an explicit source-strategy decision.

## ADDED Requirements

### Requirement: Config availability detection
The system SHALL determine whether AWS Config is enabled and usable in the target
account/region before querying it, and SHALL report an explicit status when it is
not usable.

#### Scenario: Config unavailable is reported, baseline still works
- **WHEN** AWS Config is not enabled in the target account/region
- **THEN** the Config source status is reported as unavailable
- **AND** direct-API inventory still completes successfully

### Requirement: Config inventory normalization
The system SHALL query Config configuration items or Advanced Queries for baseline
resource types and normalize results into `ResourceVersionRecord` with
`inventory_source=AWS_CONFIG`.

#### Scenario: Config record normalized with provenance
- **WHEN** Config returns a configuration item for a baseline resource type
- **THEN** a normalized record is produced with `inventory_source=AWS_CONFIG`

### Requirement: Provenance preserved across sources
When the same resource is described by both Config and direct APIs, the system
SHALL preserve both provenances and SHALL NOT silently overwrite a value from one
source with a conflicting value from the other.

#### Scenario: Conflicting values are not silently overwritten
- **WHEN** Config and a direct-API collector report different versions for the
  same resource
- **THEN** both sources' provenance is preserved and the conflict is surfaced
  rather than one value silently replacing the other

### Requirement: Config remains optional until accepted
The baseline CLI SHALL NOT require AWS Config to run until this change produces an
explicit architectural decision adopting it.

#### Scenario: Baseline runs without Config configured
- **WHEN** a scan runs with no Config source requested
- **THEN** the scan completes using direct APIs only

### Requirement: Source comparison and decision
The change SHALL compare Config against direct APIs across coverage, version
completeness, freshness, latency, API complexity, required IAM, operational
dependencies, and expected cost, and SHALL conclude with exactly one decision:
`DIRECT_API_PRIMARY`, `HYBRID`, or `CONFIG_PRIMARY`.

#### Scenario: Explicit decision recorded
- **WHEN** the comparison is complete
- **THEN** a report records each comparison dimension
- **AND** exactly one of `DIRECT_API_PRIMARY`, `HYBRID`, or `CONFIG_PRIMARY` is
  selected with rationale
