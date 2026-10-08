"""Moto-backed tests for the non-version-bearing general-inventory collectors
(add-general-resource-inventory, tasks 4.1-4.4)."""

from __future__ import annotations

import io

import boto3
import pytest
from moto import mock_aws

from aws_lifecycle_inventory.inventory.direct_api import default_collectors
from aws_lifecycle_inventory.inventory.direct_api.cloudformation_collector import (
    CloudFormationCollector,
)
from aws_lifecycle_inventory.inventory.direct_api.dynamodb_collector import (
    DynamoDBCollector,
)
from aws_lifecycle_inventory.inventory.direct_api.ec2_collector import (
    EC2InstanceCollector,
)
from aws_lifecycle_inventory.inventory.direct_api.route53_collector import (
    Route53Collector,
)
from aws_lifecycle_inventory.inventory.direct_api.sns_collector import SNSCollector
from aws_lifecycle_inventory.inventory.direct_api.sqs_collector import SQSCollector
from aws_lifecycle_inventory.inventory.direct_api.vpc_collector import VPCCollector
from aws_lifecycle_inventory.lifecycle.evaluator import evaluate_all
from aws_lifecycle_inventory.models import ResourceVersionRecord
from aws_lifecycle_inventory.orchestration import run_scan_multi_region
from aws_lifecycle_inventory.output.csv_writer import COLUMNS, write_records

REGION = "us-east-1"
REGION2 = "us-east-2"
ACCOUNT_ID = "123456789012"


# --- task 4.1: per-collector enumeration, empty version/software -----------

@mock_aws
def test_ec2_instance_collector_enumerates_with_empty_version():
    ec2 = boto3.client("ec2", region_name=REGION)
    images = ec2.describe_images(Owners=["amazon"])["Images"]
    ami = images[0]["ImageId"] if images else "ami-12345678"
    ec2.run_instances(ImageId=ami, MinCount=2, MaxCount=2)

    records, status = EC2InstanceCollector().collect(boto3.Session(), ACCOUNT_ID, REGION)

    assert status.ok is True
    assert len(records) == 2
    for rec in records:
        assert rec.resource_type == "AWS::EC2::Instance"
        assert rec.version == ""
        assert rec.software_type == ""
        assert rec.software_name == ""
        assert rec.resource_id.startswith("i-")
        assert rec.resource_arn.endswith(f"instance/{rec.resource_id}")


@mock_aws
def test_vpc_collector_enumerates():
    ec2 = boto3.client("ec2", region_name=REGION)
    ec2.create_vpc(CidrBlock="10.0.0.0/16")
    records, status = VPCCollector().collect(boto3.Session(), ACCOUNT_ID, REGION)
    assert status.ok is True
    # moto provides a default VPC plus the one we created.
    assert len(records) >= 1
    assert all(r.resource_type == "AWS::EC2::VPC" and r.version == "" for r in records)


@mock_aws
def test_dynamodb_collector_enumerates():
    ddb = boto3.client("dynamodb", region_name=REGION)
    ddb.create_table(
        TableName="my-table",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    records, status = DynamoDBCollector().collect(boto3.Session(), ACCOUNT_ID, REGION)
    assert status.ok is True
    assert [r.resource_id for r in records] == ["my-table"]
    assert records[0].version == ""
    assert records[0].resource_arn.endswith("table/my-table")


@mock_aws
def test_sns_collector_enumerates_topic_name():
    sns = boto3.client("sns", region_name=REGION)
    sns.create_topic(Name="my-topic")
    records, status = SNSCollector().collect(boto3.Session(), ACCOUNT_ID, REGION)
    assert status.ok is True
    assert any(r.resource_id == "my-topic" for r in records)
    assert all(r.version == "" for r in records)


@mock_aws
def test_sqs_collector_enumerates_queue_name():
    sqs = boto3.client("sqs", region_name=REGION)
    sqs.create_queue(QueueName="my-queue")
    records, status = SQSCollector().collect(boto3.Session(), ACCOUNT_ID, REGION)
    assert status.ok is True
    assert any(r.resource_id == "my-queue" for r in records)
    assert all(r.version == "" for r in records)


@mock_aws
def test_cloudformation_collector_enumerates_stacks():
    cfn = boto3.client("cloudformation", region_name=REGION)
    cfn.create_stack(
        StackName="my-stack",
        TemplateBody='{"Resources":{"W":{"Type":"AWS::SNS::Topic"}}}',
    )
    records, status = CloudFormationCollector().collect(
        boto3.Session(), ACCOUNT_ID, REGION
    )
    assert status.ok is True
    stacks = [r for r in records if r.resource_type == "AWS::CloudFormation::Stack"]
    assert any(r.resource_id == "my-stack" for r in stacks)
    assert all(r.version == "" for r in records)


# --- task 4.2: partial-failure isolation -----------------------------------

@mock_aws
def test_partial_failure_one_collector_denied_does_not_abort(monkeypatch):
    # A collector raising mid-scan must surface as a failed status without
    # aborting the others (engine backstop).
    ddb = boto3.client("dynamodb", region_name=REGION)
    ddb.create_table(
        TableName="t",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    class _BoomCollector:
        name = "boom"

        def collect(self, session, account_id, region):
            raise RuntimeError("access denied")

    collectors = [_BoomCollector(), DynamoDBCollector()]
    result = run_scan_multi_region(collectors, boto3.Session(), [REGION], ACCOUNT_ID)

    by_name = {s.name: s for s in result.collector_statuses}
    assert by_name["boom"].ok is False
    assert by_name["dynamodb-tables"].ok is True
    # The good collector still produced its record.
    assert any(r.resource_id == "t" for r in result.records)


# --- task 4.3: Route53 global, single record across regions ----------------

@mock_aws
def test_route53_hosted_zone_not_duplicated_across_regions():
    r53 = boto3.client("route53")
    r53.create_hosted_zone(Name="example.com.", CallerReference="ref-1")

    collector = Route53Collector()
    result = run_scan_multi_region(
        [collector], boto3.Session(), [REGION, REGION2], ACCOUNT_ID
    )
    zones = [r for r in result.records if r.resource_type == "AWS::Route53::HostedZone"]
    # Exactly one record despite two regions.
    assert len(zones) == 1
    assert zones[0].region == "global"


# --- task 4.4: CSV serialization of a NOT_APPLICABLE record ----------------

def test_non_version_record_csv_is_not_applicable():
    rec = ResourceVersionRecord(
        account_id=ACCOUNT_ID,
        region=REGION,
        resource_type="AWS::SNS::Topic",
        resource_id="t",
        resource_arn=f"arn:aws:sns:{REGION}:{ACCOUNT_ID}:t",
    )
    [evaluated] = evaluate_all([rec], [])

    buf = io.StringIO()
    write_records([evaluated], buf)
    buf.seek(0)
    lines = buf.read().splitlines()
    header = lines[0].split(",")
    row = dict(zip(header, lines[1].split(",")))

    assert row["lifecycle_status"] == "NOT_APPLICABLE"
    assert row["version"] == ""
    assert row["software_type"] == ""
    assert row["software_name"] == ""
    assert row["eol_date"] == ""
    assert row["lifecycle_source"] == ""
    assert row["lifecycle_evidence_id"] == ""


def test_default_collectors_includes_general_inventory():
    names = {c.name for c in default_collectors()}
    for expected in (
        "ec2-instances",
        "vpcs",
        "dynamodb-tables",
        "sns-topics",
        "sqs-queues",
        "efs-filesystems",
        "cloudformation",
        "route53-hosted-zones",
    ):
        assert expected in names
