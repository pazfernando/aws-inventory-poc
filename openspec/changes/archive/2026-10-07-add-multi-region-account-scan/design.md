# Design

## Context

Change 01's engine already takes a boto3 session and anticipated a region list.
See `proposal.md` for motivation. This change formalizes multi-region iteration
and the execution summary.

## Goals / Non-Goals

**Goals:**
- Region-list input, per-region collector execution, combined output.
- An execution summary structured by region/source/collector.

**Non-Goals:**
- Cross-account access (Change 07).
- Choosing Config vs direct-API aggregation strategy (depends on Change 03's
  decision; applied in Change 07).

## Decisions

- **Region loop around existing collectors, regional client per region**: each
  region gets its own service clients; collectors are unchanged. Rationale: keeps
  collectors region-agnostic and isolation intact.
- **Service/regional awareness via graceful skip**: a service not available in a
  region yields a skipped/failed collector status for that region, not an abort.
- **Summary is a structured object, not just logs**, so Lambda (Change 09) can
  emit it alongside the CSV. Alternative (log-only) rejected for poor machine
  consumption.
- **Sequential regions by default, parallelism optional later**: keeps behavior
  deterministic for tests; parallel execution is an optimization, not required.

## Risks / Trade-offs

- [Some services are global or unavailable per region] → treat as regional
  awareness: record a clear per-region collector status rather than erroring.
- [Record volume growth across regions] → streaming CSV write and per-region
  aggregation keep memory bounded.
