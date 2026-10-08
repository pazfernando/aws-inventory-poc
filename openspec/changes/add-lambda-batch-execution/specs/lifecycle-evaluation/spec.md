# Spec Delta

## Purpose

Integrate the existing provider-based lifecycle evaluation into the shared scan
engine so every scan output carries evaluated lifecycle fields; discovery stays
lifecycle-agnostic and entrypoints share one evaluation path.

## MODIFIED Requirements

### Requirement: Provider abstraction
Lifecycle evaluation SHALL be provided through a `LifecycleProvider` abstraction
where `match(record)` returns `LifecycleEvidence` or `None`, and evaluation SHALL
be pluggable across multiple providers. The shared scan engine SHALL integrate
evaluation at scan time — every record produced by a scan SHALL carry evaluated
lifecycle fields per provider precedence — and collectors SHALL NOT own
deprecation policy.

#### Scenario: Provider returns no match
- **WHEN** a provider's `match(record)` returns `None`
- **THEN** evaluation continues with other providers and defaults to `UNKNOWN` if
  none match

#### Scenario: Engine evaluates every scanned record
- **WHEN** `run_scan()` aggregates collected records
- **THEN** each record is evaluated through the ordered providers before output
- **AND** records with no matching evidence keep status UNKNOWN, distinguishable
  from SUPPORTED
