# Spec Delta

## ADDED Requirements

### Requirement: Multi-account orchestration
The scan engine SHALL iterate multiple accounts, running the per-account
multi-region scan for each, and SHALL include account in the execution summary.

#### Scenario: Two accounts scanned with per-account summary
- **WHEN** a scan is requested across two accounts
- **THEN** both accounts are scanned across their configured regions
- **AND** the execution summary reports status per account, region, source, and
  collector

### Requirement: Organization-wide source strategy honored
The orchestration SHALL apply the source strategy chosen in the AWS Config
evaluation: cross-account direct-API fan-out under `DIRECT_API_PRIMARY`, and
consideration of a Config Aggregator under `HYBRID` or `CONFIG_PRIMARY`.

#### Scenario: Strategy drives org-wide inventory source
- **WHEN** the recorded Config decision is `DIRECT_API_PRIMARY`
- **THEN** org-wide inventory is gathered via cross-account direct-API fan-out
- **AND** provenance is preserved per account without silent overwrite
