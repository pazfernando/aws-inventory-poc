# Tasks

## 1. Config availability detection

- [x] 1.1 Implement availability detection via `DescribeConfigurationRecorderStatus` returning a usable/unavailable status; verify a test covers both enabled and not-enabled accounts
- [x] 1.2 Verify an integration test shows direct-API inventory still completes when Config is reported unavailable

## 2. Config inventory probe and normalization

- [x] 2.1 Implement the Config probe using Advanced Queries (`SelectResourceConfig`) with `ListDiscoveredResources`/`BatchGetResourceConfig` fallback for baseline resource types; verify a test asserts records normalize into `ResourceVersionRecord` with `inventory_source=AWS_CONFIG`
- [x] 2.2 Implement provenance handling so the same resource from Config and direct APIs keeps both sources; verify a test asserts conflicting versions are surfaced, not silently overwritten

## 3. Comparison and decision

- [x] 3.1 Collect comparison measurements (coverage, version completeness, freshness, latency, API complexity, IAM, operational dependencies, expected cost) into a report; verify every dimension has a recorded value or an explicit "not measurable" note
- [x] 3.2 Record exactly one decision (`DIRECT_API_PRIMARY` | `HYBRID` | `CONFIG_PRIMARY`) with rationale and verify the report states the chosen strategy and its impact on Changes 06/07

## Workflow follow-up

- Run `openspec validate evaluate-aws-config-inventory-source --strict` before archive.
- Archive after the decision is recorded; Changes 06/07 consume it.
