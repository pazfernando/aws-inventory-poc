# Spec Delta

## Purpose

Entry points apply the reusable lifecycle assessment service as a discrete step
after scanning, so every CLI and Lambda output carries evaluated lifecycle fields;
discovery stays lifecycle-agnostic and both entrypoints share one assessment path.

## MODIFIED Requirements

### Requirement: Provider abstraction
Lifecycle evaluation SHALL be provided through a `LifecycleProvider` abstraction
where `match(record)` returns `LifecycleEvidence` or `None`, and evaluation SHALL
be pluggable across multiple providers. Entry points SHALL populate lifecycle
fields by composing the reusable assessment service
(`lifecycle.assess_records`) after scanning — the scan engine itself SHALL NOT
evaluate lifecycle — and collectors SHALL NOT own deprecation policy.

#### Scenario: Provider returns no match
- **WHEN** a provider's `match(record)` returns `None`
- **THEN** evaluation continues with other providers and defaults to `UNKNOWN` if
  none match

#### Scenario: Entry points compose assessment after scanning
- **WHEN** the CLI or the Lambda handler runs a scan
- **THEN** it passes the collected records to the assessment service as a separate
  step before output
- **AND** each record carries evaluated lifecycle fields per provider precedence
- **AND** records with no matching evidence keep status UNKNOWN, distinguishable
  from SUPPORTED
