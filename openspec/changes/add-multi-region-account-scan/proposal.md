# Proposal

## Why

The scan currently targets a single region. Real accounts deploy across many
regions, so the engine must scan multiple regions in one account while preserving
per-region provenance and partial-failure tolerance.

## What Changes

- Add a scan-orchestration capability that accepts one or more regions and runs
  collectors per region with service/regional awareness.
- Combine per-region results into one normalized output while recording region on
  every record.
- Tolerate partial failures per region/collector without aborting the whole scan.
- Produce an execution summary broken down by region, source, and collector.

## Capabilities

### New Capabilities
- `scan-orchestration`: Multi-region execution of the shared scan engine with
  per-region provenance, partial-failure handling, and an execution summary.

### Modified Capabilities

(none)

## Impact

- `src/aws_lifecycle_inventory/orchestration.py` extended to iterate regions.
- CLI gains a `--regions` option (defaulting to the caller's current region).
- No new IAM beyond existing per-service read-only actions, applied per region.
