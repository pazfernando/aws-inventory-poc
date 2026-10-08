# Tasks

## 1. Lifecycle status + evaluator

- [x] 1.1 Add `NOT_APPLICABLE = "NOT_APPLICABLE"` to `LifecycleStatus`
  (`lifecycle/models.py`).
- [x] 1.2 In `lifecycle/evaluator.py::evaluate_record`, add an early branch:
  records whose `resource_type` is in a known non-version-bearing set (or with
  empty `version` per the resolved open question) get `NOT_APPLICABLE` with
  `evaluated_at` set, without consulting providers.
- [x] 1.3 Unit tests: a no-version record yields `NOT_APPLICABLE`, distinct from
  `UNKNOWN` and `SUPPORTED`; a version-bearing record is unaffected.

## 2. Non-version-bearing collectors

Each collector follows the existing `Collector` pattern, read-only, returning
`(records, CollectorStatus)` and never inventing a version.

- [x] 2.1 `ec2_collector.py` — `ec2:describe_instances` → `AWS::EC2::Instance`.
- [x] 2.2 `vpc_collector.py` — `ec2:describe_vpcs` → `AWS::EC2::VPC`.
- [x] 2.3 `dynamodb_collector.py` — `dynamodb:list_tables` → `AWS::DynamoDB::Table`.
- [x] 2.4 `sns_collector.py` — `sns:list_topics` → `AWS::SNS::Topic`.
- [x] 2.5 `sqs_collector.py` — `sqs:list_queues` → `AWS::SQS::Queue`.
- [x] 2.6 `efs_collector.py` — `elasticfilesystem:describe_file_systems` →
  `AWS::EFS::FileSystem`.
- [x] 2.7 `cloudformation_collector.py` — `describe_stacks` +
  `list_stack_sets` → `AWS::CloudFormation::Stack` and
  `AWS::CloudFormation::StackSet`.
- [x] 2.8 `route53_collector.py` — `route53:list_hosted_zones` →
  `AWS::Route53::HostedZone`, emitted once with a `global` region marker.
- [x] 2.9 Construct standard ARNs where the API does not return one (VPC,
  DynamoDB, Route53); use API-provided ARNs otherwise.

## 3. Engine registration

- [x] 3.1 Register all new collectors in `default_collectors()`
  (`inventory/direct_api/__init__.py`).
- [x] 3.2 Confirm multi-region and org scans include them (no separate wiring);
  verify Route53 is not duplicated across regions.

## 4. Tests

- [x] 4.1 Per-collector unit tests with `moto` (`@mock_aws`): resources
  enumerated, empty version/software fields, correct `resource_type`/`resource_id`.
- [x] 4.2 Partial-failure test: one group denied → failed `CollectorStatus`, scan
  and other collectors still complete.
- [x] 4.3 Route53 global test: single record across a multi-region scan.
- [x] 4.4 End-to-end CSV test: a no-version row serializes with empty
  version/evidence cells and `lifecycle_status=NOT_APPLICABLE`.

## 5. Docs + diagram

- [x] 5.1 README: add the new read-only IAM actions (ec2, dynamodb, sns, sqs,
  elasticfilesystem, cloudformation, route53).
- [x] 5.2 Regenerate the execution-sequence diagram (update-execution-diagram
  skill) if the discovery scope depiction changes; stage `.mmd` + `.svg`.
- [x] 5.3 Update `AGENTS.md` status/structure to reflect the new collectors and
  `NOT_APPLICABLE`.

## 6. Validation

- [x] 6.1 `openspec validate add-general-resource-inventory --strict` passes.
- [x] 6.2 `python -m pytest -s` passes.
- [x] 6.3 Optional live check against account 179733518853 across
  `us-east-1,us-east-2`; compare counts with the peer collector (EC2, VPC,
  DynamoDB, SNS, CloudFormation).
