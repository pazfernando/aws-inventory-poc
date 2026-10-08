# AWS Resource Lifecycle Inventory Tool

Read-only AWS tool that discovers version-bearing AWS resources, normalizes their
software/runtime/engine versions, evaluates lifecycle/deprecation status, and
produces a CSV report. It starts as a local CLI and is later deployable as an AWS
Lambda batch process reusing the same core engine.

> Team-wide conventions (Python, Terraform, testing, security, CI/CD) live in the
> central `~/.config/opencode/AGENTS.md`. This file only covers repo-specific
> context. Keep it current whenever structure, commands, or conventions change.

## Status

Changes 01-05 plus `add-endoflife-lifecycle-source` are implemented and verified;
Changes 01-04 are archived. The package under `src/aws_lifecycle_inventory/` has
the record model (with lifecycle fields), CSV writer, scan engine, CLI, 11
direct-API collectors, an optional AWS Config source + provenance reconciliation
under `inventory/config/`, and a lifecycle evaluation layer under `lifecycle/`:
status enum + evidence model, provider-based `evaluator.py` (ordering = precedence;
other matches preserved as provenance), an AWS Health provider
(`providers/aws_health.py`, AWS-authoritative, non-fatal, ARN-matched), and an
EndOfLife provider (`providers/endoflife.py`) backed by endoflife.date data (baked
`endoflife_seed.json`, on-disk runtime cache, age-based non-fatal auto-refresh via
`LIFECYCLE_REFRESH_MAX_AGE_DAYS`, default 30). Default lifecycle precedence is
**AWS Health → EndOfLife** (the curated seed provider was removed; EndOfLife
replaces it, each entry citing an official source link as evidence). The coverage
matrix and Config evaluation report are kept with the code
(`inventory/direct_api/COVERAGE_MATRIX.md`, `inventory/config/EVALUATION_REPORT.md`)
so their anti-drift tests survive change archival.

Changes 06 and 08 are implemented and archived: `scan-orchestration`
(`run_scan_multi_region()`, per-region isolation/provenance, structured
`execution_summary()`, CLI `--regions`) and `managed-node-software-inventory`
(`managed_nodes/ssm.py`, bounded OS + opt-in application subset, no-inference
rule, `SSM_UNMANAGED`/`SSM_NO_INVENTORY` coverage gaps, `coverage_status` field +
CSV column). Change 07 (`add-organization-account-scan`) is implemented and
in-flight: `account_access.py` assume-role session factory + `run_org_scan()`
(accounts × regions, per-account isolation, account-aware summary,
`ORG_SOURCE_STRATEGY = DIRECT_API_PRIMARY`); pending real multi-account
validation before archive. Change 03 decision: DIRECT_API_PRIMARY. AWS Config
stays optional; re-evaluate (Config Aggregator vs cross-account fan-out) was
resolved in favor of cross-account direct-API fan-out for org scans.

The lifecycle evaluator is a standalone layer; wiring it into the shared engine
is specified as part of `add-lambda-batch-execution` (tasks 1.1-1.2), not yet
implemented. Remaining: `add-lambda-batch-execution` (also carries the lifecycle
wiring) and optional `add-inspector-security-enrichment`.

Tests: `python -m pytest -s` (moto; no real AWS). Services moto cannot back (MWAA,
Config Advanced Queries, AWS Health) are tested via stub clients. See `README.md`
for CLI usage and IAM.

> Note: keep any file a test depends on inside `src/` or `tests/`, not inside a
> change folder — archiving moves change folders and would break the test.

## Architectural principles (non-negotiable)

- **Read-only.** The tool MUST NOT modify scanned workloads.
- **Inventory before lifecycle.** Prove discovery and version extraction before
  layering deprecation semantics.
- **Direct AWS APIs are the baseline** inventory source. AWS Config is a
  *candidate* centralized source that MUST be measured (Change 03) before adoption.
- **One normalized record model** is shared by CLI, CSV, Config, Health, SSM and
  Lambda.
- **UNKNOWN is a valid lifecycle status.** Absence of evidence is never SUPPORTED,
  and UNKNOWN MUST stay distinguishable from SUPPORTED.
- **No invented versions.** A collector MUST NOT infer a version the AWS API does
  not expose; unknown/unavailable versions stay explicit.
- **Provenance preserved.** Every record carries its `inventory_source`; every
  non-UNKNOWN lifecycle conclusion carries its `lifecycle_source`/evidence. Never
  silently overwrite conflicting values from different sources.
- **Partial failures never abort the scan.** Surface them as collector/coverage
  status.
- **Separate concerns.** Lifecycle/deprecation != vulnerability/CVE (Inspector).
  Inspector is optional (Change 10) and MUST NOT redefine lifecycle fields.
- **CLI and Lambda share one core engine.**

## Tech stack

- Python 3.12+, boto3
- pytest + moto (`@mock_aws`) for tests
- Pydantic for the normalized record model and configuration

## Target repository structure

```
aws-lifecycle-inventory/
├── pyproject.toml
├── src/aws_lifecycle_inventory/
│   ├── cli.py
│   ├── models.py            # normalized ResourceVersionRecord
│   ├── orchestration.py     # scan engine (shared by CLI + Lambda)
│   ├── inventory/
│   │   ├── direct_api/      # per-service collectors
│   │   └── config/          # AWS Config source (Change 03+)
│   ├── lifecycle/
│   │   ├── evaluator.py
│   │   └── providers/       # aws_health.py, endoflife.py
│   ├── managed_nodes/ssm.py # SSM Inventory (Change 08)
│   └── output/csv_writer.py
├── tests/{unit,fixtures}/
└── openspec/{specs,changes}/
```

## CSV contract evolution

- **Baseline (Change 01):** `account_id, region, resource_type, resource_id,
  resource_arn, software_type, software_name, version, inventory_source,
  collected_at`
- **After lifecycle (Change 04):** `lifecycle_status, eol_date, days_to_eol,
  lifecycle_source, lifecycle_evidence_id, evaluated_at`
- **Operational:** `collector_status, coverage_status, error_code, error_message`
- **Optional Inspector (Change 10):** `security_status, critical_cve_count,
  high_cve_count, inspector_finding_count, security_source`

UNKNOWN lifecycle MUST remain distinguishable from SUPPORTED. Never retire an
existing column silently.

## OpenSpec workflow

Work is sequenced as independent changes under `openspec/changes/`. Each is
proposed, implemented, verified, and archived before the next begins.

Recommended order (01-09 baseline, 10 optional):

1. `add-resource-version-inventory-cli`
2. `expand-basic-resource-collectors`
3. `evaluate-aws-config-inventory-source` (spike → DIRECT_API_PRIMARY | HYBRID | CONFIG_PRIMARY)
4. `add-lifecycle-evaluation-model`
5. `add-aws-health-lifecycle-source`  ← first useful product milestone
6. `add-multi-region-account-scan`
7. `add-organization-account-scan`
8. `add-ssm-managed-node-inventory`
9. `add-lambda-batch-execution`
10. `add-inspector-security-enrichment` (OPTIONAL — only if CVE management is required)

Common commands:

```bash
openspec list                     # in-flight changes
openspec list --specs             # capability inventory
openspec show <change-name>       # view a change
openspec validate <name> --strict # validate a change
openspec archive <name>           # after implementation + verification
```
