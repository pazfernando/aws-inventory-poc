# aws-health-lifecycle-source Specification

## Purpose
Integrates AWS Health Planned Lifecycle Events as a non-fatal lifecycle evidence
provider that enriches already-discovered resources without owning discovery.

## Requirements

### Requirement: Query Planned Lifecycle Events
The provider SHALL query AWS Health for relevant Planned Lifecycle Events when
permissions and account capabilities allow.

#### Scenario: Events queried when permitted
- **WHEN** the account has Health API access and relevant Planned Lifecycle Events
- **THEN** the provider retrieves those events for matching

### Requirement: Match affected resources
Affected entities/resources SHALL be matched to normalized inventory records only
when a reliable ARN or identifier match exists.

#### Scenario: Event matched to inventory record by ARN
- **WHEN** a Planned Lifecycle Event's affected entity ARN equals a discovered
  record's `resource_arn`
- **THEN** that event's lifecycle evidence is attached to the record

#### Scenario: No reliable match leaves record unchanged
- **WHEN** a Health event cannot be reliably matched to any discovered record
- **THEN** no record is annotated from that event

### Requirement: Preserve Health evidence
Health-derived conclusions SHALL preserve the event ARN/identity, event type,
event date, affected entity/resource, affected-resource status, and
`lifecycle_source=AWS_HEALTH`.

#### Scenario: Evidence fields recorded
- **WHEN** a record is annotated from a Health event
- **THEN** its lifecycle evidence records the event identity, type, date, affected
  entity, affected-resource status, and `lifecycle_source=AWS_HEALTH`

### Requirement: Non-fatal dependency
If AWS Health is unavailable, inventory SHALL still complete, other lifecycle
providers SHALL continue, and status MAY remain `UNKNOWN`.

#### Scenario: Health unavailable, scan succeeds
- **WHEN** the Health API is not accessible for the account
- **THEN** the scan completes, other providers still evaluate, and unmatched
  records remain `UNKNOWN`

### Requirement: No false inference from absence
Absence of a Health event SHALL NOT be interpreted as the resource being
supported.

#### Scenario: No event does not imply supported
- **WHEN** a discovered resource has no matching Health event
- **THEN** its status is not set to `SUPPORTED` on that basis alone
