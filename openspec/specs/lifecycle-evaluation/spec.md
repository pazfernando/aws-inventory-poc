# lifecycle-evaluation Specification

## Purpose
Provider-based evaluation of a resource's version into a lifecycle status, with
preserved evidence, kept fully independent of resource discovery.

## Requirements

### Requirement: Lifecycle status set
The system SHALL classify each resource into exactly one lifecycle status from:
`SUPPORTED`, `EOL_365`, `EOL_180`, `EOL_90`, `EOL_30`, `EOL`, `UNSUPPORTED`,
`UNKNOWN`.

#### Scenario: Approaching-EOL window classified
- **WHEN** a resource version has a known EOL date 120 days in the future
- **THEN** its lifecycle status is `EOL_180`

#### Scenario: Past EOL classified
- **WHEN** a resource version has a known EOL date in the past
- **THEN** its lifecycle status is `EOL` (or `UNSUPPORTED` per provider evidence)

### Requirement: UNKNOWN is distinct from SUPPORTED
Absence of lifecycle evidence SHALL yield `UNKNOWN`, and `UNKNOWN` SHALL remain
distinguishable from `SUPPORTED`; absence of evidence SHALL NOT be read as
supported.

#### Scenario: No matching evidence yields UNKNOWN
- **WHEN** no provider returns evidence for a resource version
- **THEN** its lifecycle status is `UNKNOWN`
- **AND** it is not reported as `SUPPORTED`

### Requirement: Evidence required for non-UNKNOWN conclusions
Every non-`UNKNOWN` lifecycle conclusion SHALL carry evidence identifying its
source, and collectors/Config queries SHALL NOT own deprecation policy.

#### Scenario: Supported conclusion carries evidence
- **WHEN** a provider classifies a version as `SUPPORTED`
- **THEN** the conclusion records `lifecycle_source` and a `lifecycle_evidence_id`

### Requirement: Provider abstraction
Lifecycle evaluation SHALL be provided through a `LifecycleProvider` abstraction
where `match(record)` returns `LifecycleEvidence` or `None`, and evaluation SHALL
be pluggable across multiple providers.

#### Scenario: Provider returns no match
- **WHEN** a provider's `match(record)` returns `None`
- **THEN** evaluation continues with other providers and defaults to `UNKNOWN` if
  none match

### Requirement: Provider precedence order
When multiple lifecycle providers can match a record, evaluation SHALL consult
them in a fixed precedence order — AWS Health, then EndOfLife — and the first
match SHALL supply the conclusion while all other matches are preserved as
provenance.

#### Scenario: EndOfLife used when Health unavailable
- **WHEN** AWS Health returns no evidence for a record but EndOfLife does
- **THEN** the EndOfLife evidence supplies the lifecycle conclusion

#### Scenario: Health outranks EndOfLife
- **WHEN** both AWS Health and EndOfLife return evidence for the same record
- **THEN** AWS Health supplies the conclusion
- **AND** the EndOfLife match is preserved as provenance, not discarded

#### Scenario: No provider matches yields UNKNOWN
- **WHEN** neither AWS Health nor EndOfLife matches a record
- **THEN** the record's lifecycle status is UNKNOWN
