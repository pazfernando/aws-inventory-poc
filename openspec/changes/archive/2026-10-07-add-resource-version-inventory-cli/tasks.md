# Tasks

## 1. Project scaffolding

- [x] 1.1 Create `pyproject.toml` with Python 3.12 target and deps (`boto3`, `pydantic`; dev `pytest`, `moto`) and verify `pip install -e .[dev]` succeeds in a fresh venv
- [x] 1.2 Create `src/aws_lifecycle_inventory/` package layout (`cli.py`, `models.py`, `orchestration.py`, `inventory/direct_api/`, `output/`) and verify `python -c "import aws_lifecycle_inventory"` succeeds

## 2. Normalized record model and CSV writer

- [x] 2.1 Implement `ResourceVersionRecord` in `models.py` with baseline fields and ISO-8601 UTC `collected_at`; verify a unit test constructs a record and asserts all baseline fields
- [x] 2.2 Implement `output/csv_writer.py` with a central ordered baseline column list; verify a unit test asserts header order and that an empty `version` serializes to an empty cell

## 3. Collector interface and scan engine

- [x] 3.1 Define the `Collector` protocol returning `(records, collector_status)` and implement `orchestration.run_scan()` that aggregates records and statuses; verify a unit test with a deliberately failing fake collector shows the scan completes and reports that collector as failed while others still emit records
- [x] 3.2 Wire `cli.py` to parse profile/region/output path and call `run_scan()`; verify `--help` runs and an end-to-end run against moto writes a CSV

## 4. Baseline direct-API collectors

- [x] 4.1 Implement Lambda collector (runtime → software_name/version, e.g. `python3.12`→`python`/`3.12`); verify moto `@mock_aws` test asserts normalized output
- [x] 4.2 Implement RDS + Aurora collector (engine + engine version for instances and clusters); verify moto test asserts `postgres`/`15.4` and that a missing version stays empty
- [x] 4.3 Implement ElastiCache collector (engine + engine version); verify moto test asserts normalized output
- [x] 4.4 Implement EKS collector (Kubernetes version via ListClusters/DescribeCluster); verify moto test asserts `kubernetes`/version

## 5. End-to-end verification

- [x] 5.1 Add an integration test running `run_scan()` across all baseline collectors against a moto account with mixed resources and verify the written CSV contains one correctly normalized row per resource with stable baseline columns
- [x] 5.2 Document CLI usage and required read-only IAM actions in the package README/`cli.py` help and verify the documented invocation runs as written

## Workflow follow-up

- Run `openspec validate add-resource-version-inventory-cli --strict` before archive.
- Archive the change after implementation and verification are complete.
