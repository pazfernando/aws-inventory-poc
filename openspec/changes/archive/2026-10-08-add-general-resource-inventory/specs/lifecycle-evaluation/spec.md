# Spec Delta

## Purpose

Extend the lifecycle status set so resources that have no version to evaluate are
marked explicitly as not applicable, kept distinct from both `SUPPORTED` and
`UNKNOWN`.

## MODIFIED Requirements

### Requirement: Lifecycle status set

The system SHALL classify each resource into exactly one lifecycle status from:
`SUPPORTED`, `EOL_365`, `EOL_180`, `EOL_90`, `EOL_30`, `EOL`, `UNSUPPORTED`,
`UNKNOWN`, `NOT_APPLICABLE`. `NOT_APPLICABLE` SHALL mean the resource carries no
version to evaluate (not an absence of evidence), and SHALL remain distinct from
`UNKNOWN` and `SUPPORTED`.

#### Scenario: Approaching-EOL window classified

- **WHEN** a resource version has a known EOL date 120 days in the future
- **THEN** its lifecycle status is `EOL_180`

#### Scenario: Past EOL classified

- **WHEN** a resource version has a known EOL date in the past
- **THEN** its lifecycle status is `EOL` (or `UNSUPPORTED` per provider evidence)

#### Scenario: Non-version-bearing resource classified NOT_APPLICABLE

- **WHEN** a record has an empty `version` because the resource type has no
  version to evaluate
- **THEN** its lifecycle status is `NOT_APPLICABLE`
- **AND** it is distinguishable from both `UNKNOWN` and `SUPPORTED`

### Requirement: UNKNOWN is distinct from SUPPORTED

Absence of lifecycle evidence SHALL yield `UNKNOWN`, and `UNKNOWN` SHALL remain
distinguishable from `SUPPORTED`; absence of evidence SHALL NOT be read as
supported. A record classified `NOT_APPLICABLE` is not an absence-of-evidence case
and SHALL NOT be reported as `UNKNOWN`.

#### Scenario: No matching evidence yields UNKNOWN

- **WHEN** a version-bearing resource has a version but no provider returns
  evidence
- **THEN** its lifecycle status is `UNKNOWN`
- **AND** it is not reported as `SUPPORTED`

#### Scenario: No-version resource is not UNKNOWN

- **WHEN** a record carries no version to evaluate
- **THEN** the evaluator assigns `NOT_APPLICABLE` without consulting providers
- **AND** the record is not reported as `UNKNOWN`
