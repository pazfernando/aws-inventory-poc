# Spec Delta

## Purpose

Provides cross-account read-only access via STS AssumeRole, isolating each target
account and preserving account provenance across an organization-wide scan.

## ADDED Requirements

### Requirement: Cross-account assume-role access
The system SHALL access target accounts using configurable STS AssumeRole with
read-only permissions.

#### Scenario: Role assumed per target account
- **WHEN** a scan is configured with a list of target accounts and a role name
- **THEN** the system assumes the read-only role in each account before scanning it

### Requirement: Account isolation
A failure accessing or scanning one account SHALL NOT abort scanning of other
accounts.

#### Scenario: One inaccessible account does not stop the scan
- **WHEN** the role cannot be assumed in one target account
- **THEN** that account is reported as inaccessible and the remaining accounts are
  still scanned

### Requirement: Account provenance
Every record SHALL carry the account it was discovered in, and combining accounts
SHALL NOT lose or overwrite that provenance.

#### Scenario: Account id recorded on each record
- **WHEN** records from multiple accounts are combined
- **THEN** each record retains its originating `account_id`
