# Tasks

## 1. Dataset, mapping, and loading

- [x] 1.1 Define the dataset JSON shape (`updated_at` + `products`) and bake a seed file into the package; verify a test loads the seed and reads at least Lambda/EKS/RDS entries
- [x] 1.2 Implement the product-mapping table (software/version → endoflife product + cycle, incl. Lambda runtime direct, RDS by major, EKS by cycle); verify unit tests map representative records and leave unmapped ones unmatched
- [x] 1.3 Implement dataset loading that prefers the on-disk runtime cache and falls back to the packaged seed; verify a test covers cache-present and cache-absent

## 2. Provider and precedence

- [x] 2.1 Implement `EndOfLifeProvider.match(record)` returning evidence (EOL date + source link as `evidence_id`, `support` in details); verify a test classifies `python`/`3.10` with its source link and returns None for unmapped products
- [x] 2.2 Wire provider precedence Health → EndOfLife as the default provider list, and remove the curated provider (`providers/curated.py`, `curated_data.yaml`) and its tests; verify tests assert EndOfLife is used when Health is absent, Health outranks EndOfLife (EndOfLife preserved as provenance), and that the curated provider no longer exists

## 3. Refresh policy (age-based, configurable, non-fatal)

- [x] 3.1 Implement freshness threshold from `LIFECYCLE_REFRESH_MAX_AGE_DAYS` (default 30); verify tests cover default and overridden values
- [x] 3.2 Implement age-based refresh that fetches from endoflife.date only when stale and rewrites the runtime cache with a new `updated_at`; verify a test (mocked fetch) asserts refresh on stale and no fetch when fresh
- [x] 3.3 Make refresh non-fatal: on fetch/parse/write failure keep the existing dataset, mark it stale, and still serve evidence; verify a test asserts stale-keep behavior and that evaluation still completes
- [x] 3.4 Write the runtime cache to a local on-disk location (OS cache dir, `/tmp` fallback); verify a test asserts the cache file is written locally after a refresh

## Workflow follow-up

- Run `openspec validate add-endoflife-lifecycle-source --strict` before archive.
- Archive after implementation and verification; a future change will add S3-backed refresh.
