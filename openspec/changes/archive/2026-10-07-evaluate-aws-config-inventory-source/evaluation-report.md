# AWS Config vs Direct APIs — Evaluation Report & Decision

Change: `evaluate-aws-config-inventory-source` (Change 03, architectural spike).

This report measures AWS Config as a centralized inventory/aggregation source
against the direct-API baseline (Changes 01-02) and records an explicit
source-strategy decision. Config stays optional until this decision adopts it.

## Method

- A Config source (`inventory/config/config_source.py`) detects availability via
  `DescribeConfigurationRecorderStatus` and probes baseline resource types with
  Advanced Queries (`SelectResourceConfig`), normalizing results into the shared
  `ResourceVersionRecord` with `inventory_source=AWS_CONFIG`.
- Provenance reconciliation (`inventory/config/provenance.py`) keeps every source's
  observation for a resource and surfaces version conflicts instead of overwriting.
- Automated coverage uses moto for availability detection and a stubbed Config
  client for Advanced-Query normalization (moto does not execute real Config
  queries). Dimensions that require a live multi-account Config deployment are
  marked **not measurable in this environment** with the expected real-world value
  stated, rather than fabricated.

## Comparison

| Dimension | Direct APIs (baseline) | AWS Config (candidate) | Measurement status |
|-----------|------------------------|------------------------|--------------------|
| Resource coverage | 11 managed-service families via per-service collectors | Depends on recorder's recording group; only recorded resource types are queryable | Partially measurable: availability + normalization proven; full per-type coverage **not measurable in this environment** (needs live recorder) |
| Version completeness | Reads each service's authoritative version field; empty when API exposes none | Reads the Config configuration item's fields; equivalent when Config records the same attribute, otherwise empty | Normalization proven for Lambda/RDS/ElastiCache/EKS via stub; parity per field **not measurable** without live data |
| Freshness | Live at scan time (describe/list calls) | Config item is as fresh as the last configuration change delivery; can lag live state | **Not measurable in this environment**; known to lag in real Config |
| Latency | One or more describe calls per service/region | One Advanced Query per resource type; can aggregate many resources per call | Qualitative: Config reduces call count at org scale; absolute latency **not measurable** here |
| API complexity | Many heterogeneous service APIs (per collector) | One uniform query API (`SelectResourceConfig` / aggregator) | Config is simpler to fan out; direct APIs need per-service code (already built) |
| Required IAM | Per-service read-only actions (documented in README + coverage matrix) | `config:DescribeConfigurationRecorderStatus`, `config:SelectResourceConfig` (+ `SelectAggregateResourceConfig` for aggregator) | Measured: both IAM sets documented |
| Operational dependencies | None beyond read-only creds | Requires a configuration recorder, delivery channel, and (for org) an aggregator to be deployed and recording | Measured: Config has a hard prerequisite the baseline does not |
| Expected cost | API calls only (negligible) | Config recording + delivery + Advanced Query/aggregator costs scale with resource count and change rate | **Not measurable in this environment**; non-zero and usage-dependent in real Config |

## Findings

1. **Config is not guaranteed available.** The baseline MUST keep working when no
   recorder is configured — proven by `test_direct_api_completes_when_config_unavailable`.
2. **Config normalizes into the same record model** with `inventory_source=AWS_CONFIG`
   — proven by `test_config_probe_normalizes_with_aws_config_source`.
3. **Provenance is preserved and conflicts surfaced**, never silently overwritten —
   proven by `test_provenance_preserves_both_sources_and_surfaces_conflict`.
4. **Config's advantage is org-scale aggregation** (uniform query API, fewer calls),
   not freshness or per-type coverage, both of which can be worse than direct APIs.
5. **Config carries a real operational prerequisite and cost** that the direct-API
   baseline does not.

## Decision

**DIRECT_API_PRIMARY** (with Config reserved for org-scale aggregation, re-evaluated
in Change 07).

Rationale:
- The direct-API collectors already deliver authoritative, live, version-complete
  inventory for all 11 families with no deployment prerequisite.
- Config's measurable advantages (uniform API, fewer calls) matter mainly at
  multi-account/org scale, which is Change 07's concern, not the single-account
  baseline's.
- Config's freshness lag, recording-group-dependent coverage, operational
  prerequisite, and cost make it a poor mandatory baseline dependency now.

### Impact on later changes

- **Change 06 (multi-region):** unaffected — stays direct-API fan-out per region.
- **Change 07 (organization):** MUST re-evaluate a **Config Aggregator** vs
  cross-account direct-API fan-out specifically for org-wide aggregation, using the
  Config source and provenance reconciliation delivered here. The decision there may
  move to `HYBRID` for org scope while the per-account baseline remains
  `DIRECT_API_PRIMARY`.
- The Config source and provenance utilities remain in the codebase as the measured,
  optional building blocks for that re-evaluation.
