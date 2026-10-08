"""Tests for SSM-managed node inventory (Change 08).

moto has no SSM Inventory backend, so SSM is exercised via stub clients while
EC2 runs on moto — mirroring the stub approach used for MWAA, Config Advanced
Queries, and AWS Health.
"""

from __future__ import annotations

import io

import boto3
from moto import mock_aws

from aws_lifecycle_inventory.managed_nodes.ssm import (
    COVERAGE_NO_INVENTORY,
    COVERAGE_OK,
    COVERAGE_UNMANAGED,
    SsmNodeCollector,
)
from aws_lifecycle_inventory.output.csv_writer import COLUMNS, write_records

REGION = "us-east-1"
ACCOUNT_ID = "123456789012"


class _StubPager:
    def __init__(self, pages):
        self._pages = pages

    def paginate(self, **_):
        return iter(self._pages)


class _StubSsm:
    def __init__(self, instance_information, inventory_entities=None):
        self._info = instance_information
        self._entities = inventory_entities or []

    def get_paginator(self, operation_name):
        if operation_name == "describe_instance_information":
            return _StubPager([{"InstanceInformationList": self._info}])
        if operation_name == "get_inventory":
            return _StubPager([{"Entities": self._entities}])
        raise AssertionError(f"unexpected paginator {operation_name}")


class _HybridSession:
    """Stub SSM, real (moto) EC2."""

    def __init__(self, ssm):
        self._ssm = ssm

    def client(self, service, region_name=None):
        if service == "ssm":
            return self._ssm
        return boto3.Session().client(service, region_name=region_name)


def _managed_info(instance_id, platform="Ubuntu", version="22.04"):
    return {
        "InstanceId": instance_id,
        "PingStatus": "Online",
        "PlatformName": platform,
        "PlatformVersion": version,
    }


def _run_instances(count):
    ec2 = boto3.client("ec2", region_name=REGION)
    response = ec2.run_instances(
        MinCount=count, MaxCount=count, ImageId="ami-12345678"
    )
    return [i["InstanceId"] for i in response["Instances"]]


# --- task 1.1: SSM inventory normalized for a managed instance ----------------


@mock_aws
def test_managed_instance_os_normalized():
    instance_id = _run_instances(1)[0]
    session = _HybridSession(_StubSsm([_managed_info(instance_id)]))

    records, status = SsmNodeCollector().collect(session, ACCOUNT_ID, REGION)

    assert status.ok is True
    os_records = [r for r in records if r.software_type == "os"]
    assert len(os_records) == 1
    record = os_records[0]
    assert record.resource_id == instance_id
    assert record.software_name == "Ubuntu"
    assert record.version == "22.04"
    assert record.inventory_source == "SSM_INVENTORY"
    assert record.coverage_status == COVERAGE_OK


@mock_aws
def test_application_subset_normalized_when_enabled():
    instance_id = _run_instances(1)[0]
    session = _HybridSession(
        _StubSsm(
            [_managed_info(instance_id)],
            inventory_entities=[
                {
                    "Data": {
                        "AWS:Application": {
                            "Content": [
                                {"Name": "nginx", "Version": "1.24"},
                                {"Name": "docker", "Version": ""},
                            ]
                        }
                    }
                }
            ],
        )
    )

    records, _ = SsmNodeCollector(include_applications=True).collect(
        session, ACCOUNT_ID, REGION
    )

    apps = [r for r in records if r.software_type == "application"]
    assert [(a.software_name, a.version) for a in apps] == [
        ("nginx", "1.24"),
        ("docker", ""),
    ]


# --- task 1.2: no-inference rule -----------------------------------------------


@mock_aws
def test_managed_instance_without_inventory_is_gap_not_guess():
    instance_id = _run_instances(1)[0]
    session = _HybridSession(_StubSsm([_managed_info(instance_id, "", "")]))

    records, _ = SsmNodeCollector().collect(session, ACCOUNT_ID, REGION)

    assert len(records) == 1
    gap = records[0]
    assert gap.coverage_status == COVERAGE_NO_INVENTORY
    # No software is fabricated for a managed instance that reports nothing.
    assert gap.software_name == ""
    assert gap.version == ""


# --- task 2.1: managed vs unmanaged cross-reference ----------------------------


@mock_aws
def test_one_managed_one_unmanaged_instance():
    managed_id, unmanaged_id = _run_instances(2)
    session = _HybridSession(_StubSsm([_managed_info(managed_id)]))

    records, _ = SsmNodeCollector().collect(session, ACCOUNT_ID, REGION)

    by_id = {r.resource_id: r for r in records}
    assert set(by_id) == {managed_id, unmanaged_id}
    # The managed instance yields software records.
    assert by_id[managed_id].software_type == "os"
    assert by_id[managed_id].version == "22.04"
    # The unmanaged instance remains visible as a coverage gap, not a guess.
    assert by_id[unmanaged_id].coverage_status == COVERAGE_UNMANAGED
    assert by_id[unmanaged_id].software_name == ""
    assert by_id[unmanaged_id].version == ""


# --- task 2.2: coverage status machine-visible via the CSV field ---------------


@mock_aws
def test_coverage_gap_machine_visible_in_csv():
    managed_id, unmanaged_id = _run_instances(2)
    session = _HybridSession(_StubSsm([_managed_info(managed_id)]))

    records, _ = SsmNodeCollector().collect(session, ACCOUNT_ID, REGION)

    assert "coverage_status" in COLUMNS
    stream = io.StringIO()
    write_records(records, stream)
    lines = stream.getvalue().splitlines()
    header = lines[0].split(",")
    coverage_index = header.index("coverage_status")
    rows = [dict(zip(header, line.split(","))) for line in lines[1:]]
    by_id = {row["resource_id"]: row for row in rows}
    assert by_id[managed_id][header[coverage_index]] == COVERAGE_OK
    assert by_id[unmanaged_id][header[coverage_index]] == COVERAGE_UNMANAGED
