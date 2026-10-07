# Tasks

## 1. Extended collectors

- [x] 1.1 Implement MSK collector (Kafka version) and verify a test asserts normalized `kafka`/version output
- [x] 1.2 Implement OpenSearch collector (engine/version) and verify a test asserts engine + normalized version
- [x] 1.3 Implement EMR collector (release label as version) and verify a test asserts the release label is captured
- [x] 1.4 Implement Glue Jobs collector (Glue version) and verify a test asserts `glue`/version output
- [x] 1.5 Implement Redshift collector (version where exposed, empty otherwise) and verify a test covers both the present and absent cases
- [x] 1.6 Implement Amazon MQ collector (broker engine + version) and verify a test asserts engine + version
- [x] 1.7 Implement MWAA collector (Airflow version) and verify a test asserts `airflow`/version output

## 2. Contract and failure-isolation verification

- [x] 2.1 Register all new collectors with the scan engine and verify an integration test runs them alongside the Change 01 collectors producing one normalized CSV
- [x] 2.2 Verify a test that forces one extended collector to fail shows the scan completes and reports only that collector as failed

## 3. Coverage matrix

- [x] 3.1 Produce a coverage matrix (API, IAM, version field, example output, known gaps, AWS Config equivalence) with one row per supported service and verify every supported family is represented
- [x] 3.2 Add a test or check asserting the matrix service list matches the registered collectors so the matrix cannot silently drift

## Workflow follow-up

- Run `openspec validate expand-basic-resource-collectors --strict` before archive.
- Archive after implementation and verification; the coverage matrix feeds Change 03.
