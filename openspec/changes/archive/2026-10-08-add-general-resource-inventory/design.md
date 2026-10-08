# Design

## Context

The tool's discovery layer is a set of per-service collectors that conform to the
`Collector` protocol (`name` + `collect(session, account_id, region) -> (records,
CollectorStatus)`), registered in `default_collectors()`. The shared engine
(`run_scan` → `run_scan_multi_region` → `run_org_scan`) iterates them with a
per-collector exception backstop. Lifecycle evaluation is a separate layer keyed
on `version`.

This change adds collectors for resources that have **no version**. The design
goal is to reuse every existing mechanism (record model, engine, CSV, provenance,
partial-failure isolation) and introduce the minimum new concept: a
`NOT_APPLICABLE` lifecycle status.

## Goals / Non-Goals

**Goals**
- Discover EC2, VPC, DynamoDB, SNS, SQS, EFS, CloudFormation stacks/stacksets,
  Route53 as presence records.
- Keep one record model and one CSV; no second output format.
- Mark no-version records `NOT_APPLICABLE`, distinct from `UNKNOWN`/`SUPPORTED`.
- Automatically covered by multi-region and org scans.

**Non-Goals**
- No usage/utilization metrics (invocations, throughput, idle detection) — a
  separate future spec.
- No lifecycle/EOL evaluation for these resources.
- No change to how version-bearing collectors work.

## Decisions

### Decision: Reuse `ResourceVersionRecord` with empty version
Non-version-bearing records use the existing model with `version=""`,
`software_type=""`, `software_name=""`. This honors "no invented versions" and
keeps a single CSV contract.
- **Alternative rejected:** a separate `ResourceRecord` model + second CSV. Adds a
  parallel contract and output path for no real benefit; the baseline columns
  already describe a resource without a version.

### Decision: `NOT_APPLICABLE` as a new `LifecycleStatus` enum value
Add `NOT_APPLICABLE = "NOT_APPLICABLE"` to `LifecycleStatus`. The evaluator, when
a record has an empty `version`, assigns `NOT_APPLICABLE` **without consulting any
provider**. This keeps the "absence of evidence = UNKNOWN" rule intact: no-version
is a different case from no-evidence.
- **Where:** `lifecycle/evaluator.py::evaluate_record` gains an early branch:
  `if not record.version: return record.model_copy(update={"lifecycle_status":
  NOT_APPLICABLE, "evaluated_at": now})`.
- **Note:** version-bearing collectors that legitimately could not read a version
  (API exposed none) also produce empty `version`. For those the status would
  become `NOT_APPLICABLE` too — which is acceptable and arguably more honest than
  today's `UNKNOWN`, but it is a behavior change for version-bearing resources
  with a missing version. See Open Question.

### Decision: One collector per resource group
Mirror the existing pattern: `ec2_collector.py`, `vpc_collector.py`,
`dynamodb_collector.py`, `sns_collector.py`, `sqs_collector.py`,
`efs_collector.py`, `cloudformation_collector.py` (stacks and stacksets),
`route53_collector.py`. Each registered in `default_collectors()`.

### Decision: resource_type and identity conventions
Use CloudFormation-style type names for consistency with existing records:

| Group | resource_type | resource_id | API |
|---|---|---|---|
| EC2 instance | `AWS::EC2::Instance` | InstanceId | `ec2:describe_instances` |
| VPC | `AWS::EC2::VPC` | VpcId | `ec2:describe_vpcs` |
| DynamoDB table | `AWS::DynamoDB::Table` | TableName | `dynamodb:list_tables` |
| SNS topic | `AWS::SNS::Topic` | topic name (from ARN) | `sns:list_topics` |
| SQS queue | `AWS::SQS::Queue` | queue name (from URL) | `sqs:list_queues` |
| EFS file system | `AWS::EFS::FileSystem` | FileSystemId | `elasticfilesystem:describe_file_systems` |
| CFN stack | `AWS::CloudFormation::Stack` | StackName | `cloudformation:describe_stacks` |
| CFN stackset | `AWS::CloudFormation::StackSet` | StackSetName | `cloudformation:list_stack_sets` |
| Route53 hosted zone | `AWS::Route53::HostedZone` | HostedZoneId | `route53:list_hosted_zones` |

ARNs: use the API-provided ARN where available (EC2, EFS, SNS, SQS via
GetQueueAttributes, CFN StackId). Where the API returns no ARN cheaply (VPC,
DynamoDB, Route53), construct the standard ARN from account/region/id.

### Decision: Route53 is global — record once
Route53 is not regional. The collector emits hosted zones only when invoked for a
designated region (the session's primary/first region) and stamps `region` with a
global marker (e.g. `global`) so a multi-region scan does not duplicate zones.
- **Alternative rejected:** emit per region — produces N duplicates.

## Risks / Trade-offs

- **`NOT_APPLICABLE` leaking onto version-bearing resources** whose version the
  API did not expose. Mitigation / open question below. Low blast radius: the
  value is still explicit and distinct from SUPPORTED.
- **SCP/permission gaps** (seen in the live account) will mark several collectors
  failed — handled by existing partial-failure isolation; not a new risk.
- **Record volume** grows (e.g. CloudFormation stack resources can be many). This
  change records stacks/stacksets themselves, not their nested resources, to keep
  volume bounded.

## Open Questions

- Should `NOT_APPLICABLE` apply to *any* empty-version record, or only to the new
  non-version-bearing resource types? Proposed: gate on resource_type membership
  in a known non-version-bearing set, so a version-bearing resource with a missing
  version stays `UNKNOWN` (preserves current behavior). To confirm during apply.
