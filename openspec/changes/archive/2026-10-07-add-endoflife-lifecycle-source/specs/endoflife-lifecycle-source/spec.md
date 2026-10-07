# Spec Delta

## Purpose

A verifiable, non-fatal, self-refreshing lifecycle provider backed by
endoflife.date data for AWS products, used as the primary contingency source when
AWS Health is unavailable.

## ADDED Requirements

### Requirement: EndOfLife-backed lifecycle evidence
The provider SHALL supply lifecycle evidence for AWS products from endoflife.date
data, mapping a record's software/version to an EOL date and carrying the entry's
official source link as evidence.

#### Scenario: Known Lambda runtime classified with source link
- **WHEN** a record has `software_name=python` and `version=3.10`
- **THEN** the provider returns evidence with an EOL date and an `evidence_id`
  that references the official source link for that runtime

#### Scenario: Unmapped product returns no evidence
- **WHEN** a record's software/version has no corresponding endoflife entry
- **THEN** the provider returns `None` and the record is left for other providers

### Requirement: Baked seed with runtime cache
The provider SHALL load its dataset from an on-disk runtime cache when present and
otherwise fall back to a dataset baked into the package.

#### Scenario: Cache present is used
- **WHEN** a runtime cache dataset exists and is readable
- **THEN** the provider loads lifecycle entries from the cache

#### Scenario: No cache falls back to packaged seed
- **WHEN** no runtime cache exists
- **THEN** the provider loads lifecycle entries from the packaged seed dataset

### Requirement: Age-based auto-refresh
The provider SHALL refresh its dataset from endoflife.date when the dataset is
older than a freshness threshold, and SHALL rewrite the runtime cache with the
refreshed data.

#### Scenario: Stale dataset triggers refresh
- **WHEN** the dataset's last-updated date is older than the threshold
- **THEN** the provider fetches current data from endoflife.date and updates the
  runtime cache with a new last-updated date

#### Scenario: Fresh dataset is not refreshed
- **WHEN** the dataset's last-updated date is within the threshold
- **THEN** the provider does not fetch from the network

### Requirement: Configurable freshness threshold
The freshness threshold SHALL be read from an environment variable and SHALL
default to 30 days when the variable is unset.

#### Scenario: Default threshold
- **WHEN** the freshness environment variable is not set
- **THEN** the threshold used is 30 days

#### Scenario: Overridden threshold
- **WHEN** the freshness environment variable is set to a number of days
- **THEN** that value is used as the threshold

### Requirement: Non-fatal refresh
If refreshing from endoflife.date fails, the provider SHALL continue using the
existing (stale) dataset, mark it stale, and SHALL NOT abort the scan.

#### Scenario: Network failure keeps stale data
- **WHEN** a refresh is attempted but the network or API is unavailable
- **THEN** the provider keeps serving evidence from the existing dataset
- **AND** the dataset is marked stale
- **AND** the scan completes

### Requirement: Runtime-only cache location
The runtime cache SHALL be written to local disk only; the provider SHALL NOT
require any remote store for its cache.

#### Scenario: Cache written locally
- **WHEN** the provider refreshes its dataset
- **THEN** it writes the cache to a local on-disk location
