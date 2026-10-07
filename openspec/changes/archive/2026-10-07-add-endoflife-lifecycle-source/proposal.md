# Proposal

## Why

AWS Health is the authoritative lifecycle source but requires a Business or
Enterprise Support plan, which most accounts here will not have. Without it, the
only fallback is a hand-written curated seed of a few entries — too small and not
independently verifiable. We need a robust, verifiable contingency lifecycle
source that works without AWS Health, and it should replace the unverifiable
curated seed rather than sit alongside it.

## What Changes

- Add an `EndOfLifeProvider` that supplies lifecycle evidence from endoflife.date
  data for AWS products (Lambda runtimes, RDS/Aurora engines, EKS, ElastiCache,
  OpenSearch, etc.), each entry carrying the official AWS/source link as evidence.
- Ship a baked-in offline dataset (seed) in the package; at runtime, load it from
  an on-disk cache when present, else fall back to the packaged seed.
- Auto-refresh the dataset when it is older than a freshness threshold: re-fetch
  from endoflife.date and rewrite the runtime cache. The threshold comes from an
  environment variable, defaulting to 30 days.
- Make refresh non-fatal: if the network/API is unavailable, keep using the stale
  cache/seed and mark it stale; the scan still completes.
- **Replace the curated seed provider** (from Change 04) with EndOfLife as the
  contingency source. Lifecycle precedence becomes: AWS Health → EndOfLife.
  Evidence from every matching source is preserved (no silent overwrite).

## Capabilities

### New Capabilities
- `endoflife-lifecycle-source`: A verifiable, non-fatal, self-refreshing
  endoflife.date-backed lifecycle provider used as the primary contingency when
  AWS Health is unavailable.

### Modified Capabilities
- `lifecycle-evaluation`: redefine provider precedence as AWS Health → EndOfLife,
  and remove the curated provider requirement now that EndOfLife replaces it.

## Impact

- New `src/aws_lifecycle_inventory/lifecycle/providers/endoflife.py` plus a baked
  seed dataset file and a product-mapping table.
- **Removes** the curated provider and its `curated_data.yaml` (and their tests)
  introduced in Change 04.
- New runtime behavior: optional outbound HTTPS to endoflife.date during refresh
  (non-fatal, throttled by freshness). No AWS write calls; AWS access stays
  read-only.
- New env var (e.g. `LIFECYCLE_REFRESH_MAX_AGE_DAYS`, default 30).
- Runtime cache on local disk only; S3-backed refresh is explicitly deferred to a
  future change.
