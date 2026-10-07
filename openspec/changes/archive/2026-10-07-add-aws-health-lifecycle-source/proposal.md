# Proposal

## Why

The curated provider (Change 04) is useful but not authoritative. AWS Health
Planned Lifecycle Events are an AWS-provided, account-specific source of
lifecycle dates and affected resources. Integrating Health yields the first truly
useful product milestone: discovered resources enriched with AWS lifecycle
evidence.

## What Changes

- Add an AWS Health lifecycle provider that queries Planned Lifecycle Events when
  permissions and account capabilities allow.
- Match Health affected entities/resources to normalized inventory records when a
  reliable ARN/identifier match exists.
- Preserve Health evidence: event ARN/identity, event type, event date, affected
  entity, affected-resource status, `lifecycle_source=AWS_HEALTH`.
- Keep Health non-fatal: if Health is unavailable the inventory still completes,
  other providers still run, and status may remain `UNKNOWN`.
- Never infer support: absence of a Health event MUST NOT mean the resource is
  supported.

## Capabilities

### New Capabilities
- `aws-health-lifecycle-source`: AWS Health Planned Lifecycle Events as a
  first-class, non-fatal lifecycle evidence provider with ARN-based matching.

### Modified Capabilities

(none — plugs into the Change 04 `LifecycleProvider` abstraction)

## Impact

- New `src/aws_lifecycle_inventory/lifecycle/providers/aws_health.py`.
- Read-only IAM: `health:DescribeEvents`, `health:DescribeEventDetails`,
  `health:DescribeAffectedEntities` (Business/Enterprise Support required for the
  Health API; unavailability is handled gracefully).
- CSV lifecycle fields now populated from Health where matched.
