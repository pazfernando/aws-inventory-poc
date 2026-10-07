# Tasks

## 1. Multi-region orchestration

- [ ] 1.1 Extend `orchestration.py` to accept a region list and build per-region service clients, running existing collectors per region; verify a moto test with resources in two regions produces records for both
- [ ] 1.2 Add the `--regions` CLI option defaulting to the caller's current region; verify `--help` shows it and a run honors multiple regions

## 2. Provenance and partial failure

- [ ] 2.1 Ensure every record retains its originating `region` when regions are combined; verify a test asserts region provenance is preserved
- [ ] 2.2 Implement per-region/collector failure isolation (e.g. service-not-in-region); verify a test shows one region failing while others complete

## 3. Execution summary

- [ ] 3.1 Produce a structured execution summary broken down by region, source, and collector; verify a test asserts the summary reports status at each breakdown level for a multi-region scan

## Workflow follow-up

- Run `openspec validate add-multi-region-account-scan --strict` before archive.
- Archive after verifying at least two regions.
