# Spec Delta

## Purpose

Keep the scan engine responsible for discovery only, so lifecycle assessment stays
a separate, reusable step rather than being fused into scanning.

## ADDED Requirements

### Requirement: Scan is discovery-only

The scan engine (`run_scan`, `run_scan_multi_region`, `run_org_scan`) SHALL produce
normalized records without evaluating lifecycle. Lifecycle fields SHALL be left at
their defaults by the scan; populating them is the responsibility of the separate
assessment step a caller composes afterward.

#### Scenario: Scan does not evaluate lifecycle

- **WHEN** a scan runs and produces records
- **THEN** the records carry discovery fields and provenance
- **AND** lifecycle fields remain at their defaults until a separate assessment
  step is applied

#### Scenario: Caller composes scan then assessment

- **WHEN** a flow needs populated lifecycle fields
- **THEN** it runs the scan, then passes the records to the assessment service
- **AND** the scan engine itself contains no lifecycle evaluation logic
