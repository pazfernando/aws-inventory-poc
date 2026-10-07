# Proposal

## Why

There is no tool to answer "which version-bearing AWS managed resources exist in
my account and what runtime/engine version are they running?" We need the smallest
executable, read-only CLI that proves resource discovery and version extraction
are correct before any lifecycle/deprecation intelligence is layered on top.

## What Changes

- Introduce a Python 3.12+ / boto3 CLI that scans one AWS account/profile in a
  single region using read-only direct service APIs.
- Add an initial set of per-service collectors isolated from one another: AWS
  Lambda (runtime), Amazon RDS + Aurora (engine + engine version), Amazon
  ElastiCache (engine + engine version), Amazon EKS (Kubernetes version).
- Define the normalized `ResourceVersionRecord` model that every collector emits
  and that all later sources (Config, Health, SSM, Lambda) will reuse.
- Write discovered records to CSV with the stable baseline columns.
- Guarantee partial failures (one collector/service erroring) never abort the
  whole scan; they are surfaced as collector status.

## Capabilities

### New Capabilities
- `resource-version-inventory`: Read-only discovery of version-bearing AWS
  resources via direct service APIs, producing normalized version records.
- `normalized-record-model`: The shared normalized record schema and its CSV
  serialization contract used by every inventory and lifecycle source.

### Modified Capabilities

(none — greenfield)

## Impact

- New `src/aws_lifecycle_inventory/` package: `cli.py`, `models.py`,
  `orchestration.py`, `inventory/direct_api/`, `output/csv_writer.py`.
- New dependencies: `boto3`, `pydantic`. Dev: `pytest`, `moto`.
- Required read-only IAM: `lambda:ListFunctions`, `rds:DescribeDBInstances`,
  `rds:DescribeDBClusters`, `elasticache:DescribeCacheClusters`,
  `elasticache:DescribeReplicationGroups`, `eks:ListClusters`,
  `eks:DescribeCluster`, `sts:GetCallerIdentity`.
