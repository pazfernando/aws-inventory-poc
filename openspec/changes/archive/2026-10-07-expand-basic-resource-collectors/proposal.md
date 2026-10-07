# Proposal

## Why

Change 01 proved discovery and version extraction for four resource families. To
be useful across real accounts the tool must cover the rest of the version-bearing
managed services without changing the normalized contract.

## What Changes

- Add isolated direct-API collectors for: Amazon MSK (Kafka version), Amazon
  OpenSearch Service (engine/version), Amazon EMR (release label), AWS Glue Jobs
  (Glue version), Amazon Redshift (cluster/release metadata where exposed),
  Amazon MQ (broker engine + version), Amazon MWAA (Airflow version).
- Each new collector emits the same normalized `ResourceVersionRecord` schema and
  honors no-invented-versions and partial-failure rules.
- Produce a coverage matrix documenting, per service: AWS API used, IAM
  permissions required, version field used, example normalized output, known
  gaps, and whether AWS Config exposes equivalent information (input to Change 03).

## Capabilities

### New Capabilities

(none)

### Modified Capabilities
- `resource-version-inventory`: extend collector coverage to seven additional
  managed-service families while preserving the existing contract.

## Impact

- New modules under `src/aws_lifecycle_inventory/inventory/direct_api/`.
- Added read-only IAM: `kafka:ListClusters*`, `es:ListDomainNames`/
  `es:DescribeDomains`, `elasticmapreduce:ListClusters`/`DescribeCluster`,
  `glue:GetJobs`, `redshift:DescribeClusters`, `mq:ListBrokers`/`DescribeBroker`,
  `airflow:ListEnvironments`/`GetEnvironment` (MWAA).
- A new coverage-matrix document artifact feeding the Change 03 Config evaluation.
