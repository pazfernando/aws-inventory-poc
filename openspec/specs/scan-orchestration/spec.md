# scan-orchestration Specification

## Purpose

Runs the shared scan engine across multiple regions of one account, combining
results with preserved per-region provenance and partial-failure tolerance.

## Requirements

### Requirement: Multi-region scan
The system SHALL accept one or more regions and run collectors in each region with
service/regional awareness.

#### Scenario: Two regions scanned
- **WHEN** a scan is requested for `us-east-1` and `eu-west-1`
- **THEN** collectors run in both regions and records are produced for resources
  in each

### Requirement: Per-region provenance
Every record SHALL record the region it was discovered in, and combining regions
SHALL NOT lose or overwrite that provenance.

#### Scenario: Region recorded on each record
- **WHEN** records from multiple regions are combined into one output
- **THEN** each record retains its originating `region`

### Requirement: Per-region partial failure tolerance
A failure in one region or collector SHALL NOT abort scanning of other regions;
the scan SHALL continue and surface the failure.

#### Scenario: One region fails, others complete
- **WHEN** collectors in one region fail (e.g. service not available there)
- **THEN** the other regions still complete and the failure is reported in the
  execution summary

### Requirement: Execution summary
The system SHALL produce an execution summary broken down by region, source, and
collector.

#### Scenario: Summary breaks down by region, source, collector
- **WHEN** a multi-region scan completes
- **THEN** the execution summary reports status per region, per source, and per
  collector
