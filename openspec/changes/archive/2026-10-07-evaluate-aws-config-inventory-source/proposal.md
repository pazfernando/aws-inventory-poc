# Proposal

## Why

AWS Config may simplify multi-account/multi-region inventory aggregation, but it
adds recorder configuration, delivery, cost, freshness, and supported-resource
considerations. We MUST measure Config against the direct-API baseline before
making it a dependency — the project must not assume Config is better.

## What Changes

- Add an AWS Config inventory source that detects Config availability, queries
  configuration items / Advanced Queries for baseline resource types, and
  normalizes results into the same `ResourceVersionRecord` with
  `inventory_source=AWS_CONFIG`.
- Run as a spike: direct-API inventory MUST keep working even when Config is
  unavailable, and Config source status is reported as unavailable in that case.
- Compare Config vs direct APIs across coverage, version completeness, freshness,
  latency, API complexity, IAM, operational dependencies, and expected cost.
- Preserve provenance when the same resource appears from multiple sources; never
  silently overwrite conflicting values.
- Conclude with an explicit architectural decision:
  `DIRECT_API_PRIMARY` | `HYBRID` | `CONFIG_PRIMARY`.

## Capabilities

### New Capabilities
- `aws-config-inventory-source`: Optional AWS Config-backed inventory source with
  availability detection, normalization into the shared record model, and a
  documented comparison/decision against the direct-API baseline.

### Modified Capabilities

(none — the baseline CLI remains unchanged and MUST NOT require Config)

## Impact

- New `src/aws_lifecycle_inventory/inventory/config/` module.
- Read-only IAM: `config:DescribeConfigurationRecorderStatus`,
  `config:SelectResourceConfig`/`SelectAggregateResourceConfig`,
  `config:ListDiscoveredResources`, `config:BatchGetResourceConfig`.
- A comparison report + decision document artifact in the change folder.
- Downstream Changes 06/07 depend on this decision for aggregation strategy.
