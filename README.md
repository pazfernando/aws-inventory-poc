# AWS Resource Lifecycle Inventory Tool

Read-only AWS tool that discovers version-bearing AWS resources, normalizes their
software/runtime/engine versions, and produces a CSV report. See `AGENTS.md` and
`openspec/` for the full roadmap.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

```bash
aws-lifecycle-inventory --region us-east-1 --output inventory.csv
# or, with a named profile / AWS SSO
aws-lifecycle-inventory --profile my-profile --region us-east-1 --output inventory.csv
```

Authentication uses the standard boto3 credential chain. If `--profile` is
omitted, boto3 resolves credentials from environment variables, `AWS_PROFILE`,
AWS SSO, the shared credentials file, or an instance/container role. The tool only
issues read-only (`list`/`describe`) API calls.

### Required read-only IAM actions

```
sts:GetCallerIdentity
lambda:ListFunctions
rds:DescribeDBInstances
rds:DescribeDBClusters
elasticache:DescribeCacheClusters
elasticache:DescribeReplicationGroups
eks:ListClusters
eks:DescribeCluster
```

## Development

```bash
python -m pytest -s
```

Tests use `moto` (`@mock_aws`) and never contact real AWS; dummy credentials are
set in the test fixtures.
