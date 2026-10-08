# Proposal

## Why

Managed-service version inventory does not cover EC2 guest OS and installed
packages. SSM Inventory owns guest-software depth and must be added without
requiring Amazon Inspector, keeping lifecycle and vulnerability concerns separate.

## What Changes

- Add a managed-node software inventory capability that ingests SSM Inventory
  metadata and normalizes selected OS/software/version data into the shared record
  model.
- Identify unmanaged instances explicitly as coverage gaps rather than guessing.
- Never infer guest software when SSM metadata is unavailable.

## Capabilities

### New Capabilities
- `managed-node-software-inventory`: Guest OS/application inventory for
  SSM-managed nodes, with explicit coverage gaps for unmanaged instances.

### Modified Capabilities

(none — emits the same normalized records)

## Impact

- New `src/aws_lifecycle_inventory/managed_nodes/ssm.py`.
- Read-only IAM: `ssm:GetInventory`, `ssm:ListInventoryEntries`,
  `ssm:DescribeInstanceInformation`, `ec2:DescribeInstances`.
- CSV gains coverage-gap visibility via operational/coverage status fields.
