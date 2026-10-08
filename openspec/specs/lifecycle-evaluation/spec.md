# lifecycle-evaluation Specification

## Purpose
Provider-based evaluation of a resource's version into a lifecycle status, with
preserved evidence, kept fully independent of resource discovery.

## Requirements

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

### Requirement: Reusable assessment service

The system SHALL expose lifecycle assessment as a standalone service with a stable
contract: it accepts a list of normalized records from any source and returns the
records annotated with lifecycle fields. The service SHALL be independent of the
scan flow — it SHALL NOT require a scan, account context, or region context to run,
and callers SHALL be able to invoke it as a discrete step.

#### Scenario: Assess records from any source

- **WHEN** a caller passes a list of normalized records (from a scan, a loaded
  CSV, or any other source) to the assessment service
- **THEN** the service returns the same records annotated with lifecycle fields
  per the existing evaluation semantics
- **AND** it does so without performing or requiring any resource discovery

#### Scenario: Assessment is a discrete, composable step

- **WHEN** a flow needs both discovery and lifecycle results
- **THEN** it composes discovery and assessment as two separate steps
- **AND** the assessment step is reusable independently of the discovery step

### Requirement: Service owns provider construction

The assessment service SHALL own construction of the default ordered providers
(precedence AWS Health then EndOfLife) and SHALL keep provider setup non-fatal, so
callers do not assemble providers themselves. Callers MAY supply an explicit
provider list to override the default.

#### Scenario: Default providers assembled by the service

- **WHEN** a caller invokes the assessment service without specifying providers
- **THEN** the service builds the default ordered providers (AWS Health then
  EndOfLife)
- **AND** unavailable provider setup (e.g. no session, or AWS Health unreachable)
  is non-fatal and the assessment still completes

#### Scenario: Caller overrides providers

- **WHEN** a caller supplies an explicit provider list
- **THEN** the service uses exactly those providers in the given order
