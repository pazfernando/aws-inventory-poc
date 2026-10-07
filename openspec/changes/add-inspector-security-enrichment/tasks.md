# Tasks

## 1. Optional enrichment pass

- [ ] 1.1 Implement a default-off, opt-in Inspector enrichment pass that runs after lifecycle evaluation and matches findings to records by ARN/identity; verify a test asserts no Inspector calls and no security fields when disabled
- [ ] 1.2 Aggregate findings into `security_status`, `critical_cve_count`, `high_cve_count`, `inspector_finding_count`, `security_source`; verify a test (mocked Inspector) asserts counts and status are populated and `security_source` identifies Inspector

## 2. Separation from lifecycle

- [ ] 2.1 Append security columns to the CSV without removing existing columns; verify a test asserts column order and that baseline/lifecycle columns are unchanged
- [ ] 2.2 Verify a test asserts enrichment never modifies `lifecycle_status`, `eol_date`, or `days_to_eol` (SUPPORTED-with-critical and EOL-with-no-findings cases)

## Workflow follow-up

- Run `openspec validate add-inspector-security-enrichment --strict` before archive.
- This change is OPTIONAL; only implement and archive if CVE management is required.
