# Spec Delta

## Purpose

Read-only discovery of non-version-bearing AWS resources so the tool produces a
complete account inventory, not only version-bearing resources. These resources
have no software version to evaluate for end-of-life; they are recorded for
presence and will later support a separate usage/utilization capability.

## ADDED Requirements

### Requirement: Non-version-bearing resource discovery

The system SHALL discover the following non-version-bearing resource groups using
read-only direct AWS APIs, one collector per group: EC2 instances, VPCs, DynamoDB
tables, SNS topics, SQS queues, EFS file systems, CloudFormation stacks,
CloudFormation stacksets, and Route53 hosted zones. Each discovered resource SHALL
produce one normalized record.

#### Scenario: Each resource group enumerated

- **WHEN** a scan runs against an account/region where these resources exist
- **THEN** each EC2 instance, VPC, DynamoDB table, SNS topic, SQS queue, EFS file
  system, CloudFormation stack, CloudFormation stackset, and Route53 hosted zone
  is emitted as its own record
- **AND** each record carries `account_id`, `region`, `resource_type`,
  `resource_id`, and `resource_arn`

#### Scenario: Resource without a version

- **WHEN** a non-version-bearing resource is recorded
- **THEN** its `version`, `software_type`, and `software_name` are empty
- **AND** the collector does NOT infer or invent a version

### Requirement: Global resources recorded once

Route53 hosted zones are a global (non-regional) resource. The system SHALL record
each hosted zone without duplicating it per region, using a stable region marker
for global resources.

#### Scenario: Hosted zone not duplicated across regions

- **WHEN** a multi-region scan runs
- **THEN** a given Route53 hosted zone appears once, not once per region

### Requirement: Partial failures isolated

Discovery of a non-version-bearing resource group SHALL follow the engine's
partial-failure rule: a denied or failing API call for one group SHALL surface as
that collector's status and SHALL NOT abort the scan or other collectors.

#### Scenario: One group denied

- **WHEN** the API call for one resource group returns AccessDenied
- **THEN** that collector reports a failed status with the error
- **AND** other collectors and the overall scan still complete

### Requirement: Engine and scope integration

The non-version-bearing collectors SHALL register into the shared scan engine the
same way as version-bearing collectors, so multi-region and organization
multi-account scans cover them without separate wiring.

#### Scenario: Covered by org scan

- **WHEN** an organization multi-account scan runs
- **THEN** the non-version-bearing resources are discovered per account and region
  alongside version-bearing resources, under the same provenance rules
