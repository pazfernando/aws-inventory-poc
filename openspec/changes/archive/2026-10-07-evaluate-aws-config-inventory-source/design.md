# Design

## Context

This is an evaluation spike, not a commitment to Config. See `proposal.md` for
motivation. It consumes the Change 02 coverage matrix's "AWS Config equivalence"
column and reuses the normalized record model from Change 01.

## Goals / Non-Goals

**Goals:**
- A Config source behind the same normalization boundary as direct-API collectors.
- A measured, documented comparison yielding one of three decisions that steers
  the aggregation strategy in Changes 06/07.

**Non-Goals:**
- Making Config mandatory. The decision may be `DIRECT_API_PRIMARY`.
- Multi-account Config Aggregator wiring (only evaluated conceptually here; actual
  org aggregation is Change 07).

## Decisions

- **Advanced Queries (`SelectResourceConfig`) as primary probe** for version
  fields, with `ListDiscoveredResources`/`BatchGetResourceConfig` as fallback.
  Rationale: Advanced Queries express version extraction compactly; alternative of
  streaming all configuration items is costlier and noisier.
- **Availability detection via `DescribeConfigurationRecorderStatus`** before any
  query, so an account without Config degrades to "unavailable" instead of error.
- **Provenance model**: records keyed by resource ARN may carry multiple source
  observations; the engine records conflicts rather than merging. This anticipates
  the Change 04+ need to keep sources distinguishable.
- **Decision is an artifact, not code**: the change's deliverable is the comparison
  report + chosen strategy; code is the probe used to gather evidence.

## Risks / Trade-offs

- [Config freshness lag vs direct APIs] → measure and record freshness explicitly;
  a stale version is a correctness risk the report must quantify.
- [Config not enabled in test/sandbox] → the spike must run and conclude even with
  Config unavailable, reporting that as a finding.
- [Cost of broad recording] → document recorder/delivery/query cost assumptions in
  the report so the decision is cost-aware.

## Open Questions

- Whether Advanced Query coverage is sufficient for every baseline service or some
  still require direct APIs — this is exactly what the spike measures and may push
  the decision toward `HYBRID`.
