# Proposal

## Why

OPTIONAL — not part of the baseline. Only justified if the product explicitly
adds vulnerability/CVE management on top of lifecycle/deprecation. Amazon
Inspector can enrich discovered resources with CVE findings, but it MUST NOT
redefine lifecycle semantics.

## What Changes

- Add a security-vulnerability-enrichment capability that queries Amazon Inspector
  findings for discovered resources and adds security fields:
  `security_status`, `critical_cve_count`, `high_cve_count`,
  `inspector_finding_count`, `security_source`.
- Keep security strictly separate from lifecycle: Inspector SHALL NOT modify
  `lifecycle_status`, `eol_date`, or `days_to_eol`.
- Append security columns to the CSV without retiring existing columns.

## Capabilities

### New Capabilities
- `security-vulnerability-enrichment`: Optional Inspector-based CVE enrichment that
  adds security fields while leaving lifecycle fields untouched.

### Modified Capabilities

(none — security fields are additive and lifecycle fields are off-limits)

## Impact

- New optional enrichment module, disabled by default.
- Read-only IAM: `inspector2:ListFindings`,
  `inspector2:ListCoverage`/`BatchGetFindingDetails` as applicable.
- CSV gains security columns only when enrichment is enabled.
