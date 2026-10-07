# Design

## Context

AWS Health (Change 05) is authoritative but gated behind Business/Enterprise
Support. See `proposal.md` for motivation. The lifecycle evaluator already consults
ordered providers and preserves provenance of every match, so adding a provider is
mechanically simple; the work here is the data source, caching, and refresh policy.

endoflife.date exposes per-product JSON (e.g. `GET https://endoflife.date/api/aws-lambda.json`)
with entries carrying `cycle`, `eol`, `support`, and often an official `link`. The
`cycle` for Lambda is exactly our runtime string (e.g. `python3.10`).

## Goals / Non-Goals

**Goals:**
- An `EndOfLifeProvider` as the primary contingency when Health is unavailable.
- Verifiable evidence: each entry's `evidence_id` references its official source link.
- Offline-capable: baked seed in the package; runtime cache on disk; refresh only
  when stale; refresh failures are non-fatal.
- Replace the curated seed provider (Change 04) with EndOfLife.

**Non-Goals:**
- S3/remote cache (explicitly deferred to a future change).
- Any network dependency in the critical path that could fail the scan.

## Decisions

- **Precedence Health → EndOfLife.** Rationale: Health is AWS-authoritative;
  EndOfLife is broad and verifiable. The curated seed is removed because it is
  unverifiable and EndOfLife supersedes it. The evaluator already preserves
  non-primary matches as provenance.
- **Remove the curated provider** (`providers/curated.py`, `curated_data.yaml`) and
  its tests; the evaluator's default provider list becomes `[AWSHealth, EndOfLife]`.
- **Product mapping table** from our identity to endoflife products:
  - Lambda: `software_name` + `version` → key `cycle` in `aws-lambda` (direct, e.g. `python3.10`).
  - RDS/Aurora: engine → `amazon-rds-postgresql` / `amazon-rds-mysql` / etc.; match by major `cycle`.
  - EKS: `kubernetes` + version → `amazon-eks` by `cycle` (e.g. `1.30`).
  - ElastiCache/OpenSearch: analogous product keys.
  Unmapped products simply return no evidence (handed to the next provider).
- **Dataset shape**: a single JSON file with `{ "updated_at": <date>, "products": { <product>: [entries] } }`.
  Baked seed ships in the package; the runtime cache mirrors this shape.
- **Refresh policy**: on provider build, compare `updated_at` against
  `now - threshold`. If stale, fetch each mapped product, rewrite the cache, set a
  fresh `updated_at`. Threshold from `LIFECYCLE_REFRESH_MAX_AGE_DAYS` (default 30).
- **Non-fatal refresh**: any fetch/parse/write error leaves the existing dataset in
  place, flagged `stale=True`; the provider still serves evidence and the scan
  completes. Mirrors the Health provider's non-fatal contract.
- **Cache location**: an OS cache dir (e.g. `platformdirs`-style `~/.cache/...`, or
  `/tmp` when not writable, as on Lambda). Packaged seed is read-only fallback.
- **EOL vs support**: use `eol` for the EOL date that drives the `EOL_*` buckets;
  retain `support` in evidence details for context. (Extended-support semantics are
  out of scope here.)

## Risks / Trade-offs

- [endoflife.date schema/endpoint drift] → pin to the documented `/api/<product>.json`
  shape; parse defensively; refresh is non-fatal so drift degrades to stale, not failure.
- [Outbound network now in the tool] → gated by freshness and fully non-fatal; the
  seed guarantees the tool works fully offline on first run.
- [Stale data on long-lived offline runs] → `stale` flag surfaced; S3 refresh (future
  change) will address fleet-wide freshness.
- [Version granularity mismatch (e.g. `15.4` vs cycle `15`)] → match RDS by major
  version cycle; document the rule and cover with fixtures.

## Open Questions

- Whether to adopt `platformdirs` for the cache path or use a minimal hand-rolled
  resolver. Deferrable: it does not change specs or the provider contract.
