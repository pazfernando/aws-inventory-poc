# Tasks

## 1. Lifecycle model and record fields

- [x] 1.1 Define the lifecycle status enum and `LifecycleEvidence` type in the lifecycle package; verify a unit test asserts all eight states exist
- [x] 1.2 Extend `ResourceVersionRecord` and the CSV writer with the lifecycle fields appended after baseline columns; verify a test asserts column order and that baseline columns are unchanged

## 2. Provider abstraction and evaluator

- [x] 2.1 Define the `LifecycleProvider` protocol (`match(record) -> LifecycleEvidence | None`) and implement `evaluator.py` that runs ordered providers, maps days-to-EOL into `EOL_*` buckets, and defaults to `UNKNOWN`; verify unit tests cover supported, each EOL window, past-EOL, and no-match → UNKNOWN
- [x] 2.2 Verify a test asserts every non-UNKNOWN conclusion carries `lifecycle_source` and `lifecycle_evidence_id`, and that UNKNOWN stays distinguishable from SUPPORTED in CSV output

## 3. Curated provider

- [x] 3.1 Implement the curated provider backed by a versioned local data file keyed by software_name/version with per-entry evidence ids; verify a test classifies a known runtime and returns the expected status and EOL date
- [x] 3.2 Add fixtures proving supported, approaching-EOL, already-EOL, and unknown cases end-to-end through the evaluator and verify the CSV reflects each case

## Workflow follow-up

- Run `openspec validate add-lifecycle-evaluation-model --strict` before archive.
- Archive after implementation and verification; Change 05 adds AWS Health as a provider.
