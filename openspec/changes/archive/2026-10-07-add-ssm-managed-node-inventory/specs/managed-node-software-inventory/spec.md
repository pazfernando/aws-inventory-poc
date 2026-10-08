# Spec Delta

## Purpose

Adds guest OS and installed-software inventory for SSM-managed nodes, normalized
into the shared record model, with unmanaged instances surfaced as explicit
coverage gaps.

## ADDED Requirements

### Requirement: Ingest SSM Inventory metadata
The system SHALL ingest SSM Inventory metadata and normalize selected OS,
software, and version data into `ResourceVersionRecord`.

#### Scenario: Managed instance software normalized
- **WHEN** an SSM-managed instance reports OS and installed-package inventory
- **THEN** normalized records are produced for the selected OS/software with their
  versions

### Requirement: Explicit coverage gaps for unmanaged instances
The system SHALL identify instances not managed by SSM explicitly as coverage
gaps, and SHALL NOT infer guest software when SSM metadata is unavailable.

#### Scenario: Unmanaged instance reported as coverage gap
- **WHEN** an EC2 instance is not managed by SSM
- **THEN** it is reported as a coverage gap
- **AND** no guest software or version is inferred for it

#### Scenario: Managed vs unmanaged remain distinguishable
- **WHEN** a scan includes one SSM-managed and one unmanaged instance
- **THEN** the managed instance yields software records
- **AND** the unmanaged instance remains visible as a coverage gap
