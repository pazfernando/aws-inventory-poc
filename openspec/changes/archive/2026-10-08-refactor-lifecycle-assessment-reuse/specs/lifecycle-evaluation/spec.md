# Spec Delta

## Purpose

Expose lifecycle evaluation as a reusable, flow-independent assessment service so
any caller (CLI, Lambda, future jobs, re-assessing a prior inventory) can apply it
to an arbitrary set of records without coupling to discovery. Evaluation semantics
are unchanged.

## ADDED Requirements

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
