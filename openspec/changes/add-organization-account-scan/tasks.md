# Tasks

## 1. Cross-account access

- [ ] 1.1 Implement an assume-role session factory (configurable role name, read-only) producing a per-account boto3 session; verify a test (mocked STS) asserts a session is built for each target account
- [ ] 1.2 Implement account isolation so an un-assumable role yields an inaccessible status without aborting; verify a test shows one failing account while others are scanned

## 2. Multi-account orchestration

- [ ] 2.1 Extend `orchestration.py` to iterate accounts × regions reusing the Change 06 engine, recording `account_id` provenance; verify a test asserts account provenance is preserved when accounts are combined
- [ ] 2.2 Extend the execution summary to break down by account, region, source, and collector; verify a test asserts the account level is present

## 3. Source strategy application

- [ ] 3.1 Read the Change 03 decision and select cross-account direct-API fan-out (or Config Aggregator consideration under HYBRID/CONFIG_PRIMARY); verify a test asserts the fan-out path under `DIRECT_API_PRIMARY` preserves per-account provenance without silent overwrite
- [ ] 3.2 Document the org-level vs per-account AWS Health visibility choice and verify the documented behavior matches the non-fatal provider model

## Workflow follow-up

- Run `openspec validate add-organization-account-scan --strict` before archive.
- Archive after validating against at least two accounts.
