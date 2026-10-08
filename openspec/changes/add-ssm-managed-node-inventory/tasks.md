# Tasks

## 1. SSM inventory ingestion

- [x] 1.1 Implement `managed_nodes/ssm.py` to read SSM Inventory and normalize a bounded OS/software subset into records; verify a test (stubbed SSM) asserts normalized OS/software/version output for a managed instance
- [x] 1.2 Implement the no-inference rule so a managed instance without inventory becomes a coverage gap, not an empty guess; verify a test asserts no software is fabricated

## 2. Coverage gaps

- [x] 2.1 Cross-reference EC2 instances with SSM-managed instances to classify managed vs unmanaged and report unmanaged ones as coverage gaps; verify a test with one managed and one unmanaged instance asserts the managed yields records and the unmanaged remains a visible gap
- [x] 2.2 Surface coverage status on records/summary and verify a test asserts the gap is machine-visible via the coverage-status field

## Workflow follow-up

- Run `openspec validate add-ssm-managed-node-inventory --strict` before archive.
- Archive after comparing one managed and one unmanaged instance with the gap visible.
