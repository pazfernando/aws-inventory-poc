# Design

## Context

Managed-service collectors (Changes 01-02) never see inside EC2 guests. See
`proposal.md` for motivation. SSM Inventory is the guest-depth source, kept
separate from Inspector so lifecycle stays distinct from CVE management.

## Goals / Non-Goals

**Goals:**
- An `ssm.py` source that reads SSM Inventory and normalizes selected OS/software.
- Explicit coverage-gap reporting for unmanaged instances.

**Non-Goals:**
- CVE/vulnerability scanning (Inspector, Change 10).
- Deep per-package lifecycle evaluation beyond what the lifecycle providers cover.

## Decisions

- **Cross-reference `ec2:DescribeInstances` with `ssm:DescribeInstanceInformation`**
  to classify managed vs unmanaged. Rationale: unmanaged instances must be a
  visible coverage gap, not silently absent.
- **Select a bounded OS/software subset** (OS platform/version, a configurable set
  of package types) rather than ingesting all inventory, to keep records focused
  and the CSV meaningful.
- **No inference rule enforced at the source**: if SSM returns no inventory for a
  managed instance, it is a gap, not an empty-but-present guess.
- **Coverage status carried on the record/summary**, reusing the operational
  coverage-status field, so gaps are machine-visible.

## Risks / Trade-offs

- [Large package inventories bloat output] → select a bounded subset and document
  it; allow configuration.
- [Instances managed but not reporting inventory] → treated as a coverage gap with
  a reason, distinct from unmanaged.
- [Mixing guest software with managed-service records] → `resource_type` and
  `inventory_source` keep them distinguishable.
