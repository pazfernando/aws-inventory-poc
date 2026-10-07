"""Tests for the AWS Config inventory source spike (tasks 1.1, 1.2, 2.1, 2.2)."""

from __future__ import annotations

import boto3
from moto import mock_aws

from aws_lifecycle_inventory.inventory.config import (
    INVENTORY_SOURCE,
    collect_from_config,
    detect_availability,
)
from aws_lifecycle_inventory.inventory.config.provenance import conflicts, reconcile
from aws_lifecycle_inventory.inventory.direct_api import default_collectors
from aws_lifecycle_inventory.models import ResourceVersionRecord
from aws_lifecycle_inventory.orchestration import run_scan

REGION = "us-east-1"
ACCOUNT_ID = "123456789012"


# --- task 1.1: availability detection --------------------------------------

@mock_aws
def test_config_unavailable_when_no_recorder():
    avail = detect_availability(boto3.Session(), REGION)
    assert avail.available is False
    assert "recorder" in avail.reason


@mock_aws
def test_config_available_when_recorder_recording():
    client = boto3.client("config", region_name=REGION)
    client.put_configuration_recorder(
        ConfigurationRecorder={
            "name": "default",
            "roleARN": f"arn:aws:iam::{ACCOUNT_ID}:role/config",
        }
    )
    client.put_delivery_channel(
        DeliveryChannel={"name": "default", "s3BucketName": "config-bucket"}
    )
    client.start_configuration_recorder(ConfigurationRecorderName="default")

    avail = detect_availability(boto3.Session(), REGION)
    assert avail.available is True


# --- task 1.2: direct-API still completes when Config unavailable ----------

@mock_aws
def test_direct_api_completes_when_config_unavailable():
    # No Config recorder configured -> Config unavailable.
    records, status = collect_from_config(boto3.Session(), ACCOUNT_ID, REGION)
    assert status.ok is False
    assert status.error_code == "CONFIG_UNAVAILABLE"
    assert records == []

    # Direct-API inventory still runs independently.
    boto3.client("glue", region_name=REGION).create_job(
        Name="gj", Role="r", Command={"Name": "glueetl"}, GlueVersion="4.0"
    )
    collectors = [c for c in default_collectors() if c.name == "glue"]
    result = run_scan(collectors, boto3.Session(), REGION, account_id=ACCOUNT_ID)
    assert any(r.resource_id == "gj" for r in result.records)


# --- task 2.1: Config probe normalization (stubbed, moto has no query data) -

class _StubConfigClient:
    """Stub returning Advanced Query results for one Lambda function."""

    def describe_configuration_recorder_status(self):
        return {"ConfigurationRecordersStatus": [{"recording": True}]}

    def select_resource_config(self, Expression, NextToken=""):  # noqa: N803
        if "AWS::Lambda::Function" in Expression and not NextToken:
            return {
                "Results": [
                    {
                        "resourceId": "my-fn",
                        "resourceName": "my-fn",
                        "arn": f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:my-fn",
                        "configuration": {"runtime": "python3.12"},
                    }
                ],
                "NextToken": "",
            }
        return {"Results": [], "NextToken": ""}


class _StubSession:
    def client(self, _service, region_name=None):
        return _StubConfigClient()


def test_config_probe_normalizes_with_aws_config_source():
    records, status = collect_from_config(_StubSession(), ACCOUNT_ID, REGION)
    assert status.ok is True
    fn = [r for r in records if r.resource_id == "my-fn"]
    assert len(fn) == 1
    assert fn[0].inventory_source == INVENTORY_SOURCE
    assert fn[0].software_name == "python"
    assert fn[0].version == "3.12"


# --- task 2.2: provenance preserved, conflicts surfaced --------------------

def test_provenance_preserves_both_sources_and_surfaces_conflict():
    arn = f"arn:aws:rds:{REGION}:{ACCOUNT_ID}:db:my-db"
    direct = ResourceVersionRecord(
        account_id=ACCOUNT_ID,
        region=REGION,
        resource_type="AWS::RDS::DBInstance",
        resource_id="my-db",
        resource_arn=arn,
        software_name="postgres",
        version="15.4",
        inventory_source="DIRECT_API",
    )
    config = ResourceVersionRecord(
        account_id=ACCOUNT_ID,
        region=REGION,
        resource_type="AWS::RDS::DBInstance",
        resource_id="my-db",
        resource_arn=arn,
        software_name="postgres",
        version="15.3",  # stale/conflicting version from Config
        inventory_source=INVENTORY_SOURCE,
    )

    grouped = reconcile([direct, config])
    assert len(grouped) == 1
    only = next(iter(grouped.values()))
    # Both observations preserved; neither overwrote the other.
    assert len(only.observations) == 2
    assert only.sources == {"DIRECT_API", INVENTORY_SOURCE}

    # The disagreement is surfaced, not hidden.
    conflicting = conflicts([direct, config])
    assert len(conflicting) == 1
    assert conflicting[0].versions == {"15.4", "15.3"}


def test_no_conflict_when_versions_agree():
    arn = f"arn:aws:eks:{REGION}:{ACCOUNT_ID}:cluster/my-eks"
    a = ResourceVersionRecord(
        account_id=ACCOUNT_ID, region=REGION, resource_type="AWS::EKS::Cluster",
        resource_id="my-eks", resource_arn=arn, software_name="kubernetes",
        version="1.30", inventory_source="DIRECT_API",
    )
    b = ResourceVersionRecord(
        account_id=ACCOUNT_ID, region=REGION, resource_type="AWS::EKS::Cluster",
        resource_id="my-eks", resource_arn=arn, software_name="kubernetes",
        version="1.30", inventory_source=INVENTORY_SOURCE,
    )
    assert conflicts([a, b]) == []
