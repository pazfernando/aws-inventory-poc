"""Registration + failure-isolation tests for extended collectors (tasks 2.1, 2.2)."""

from __future__ import annotations

import boto3
from moto import mock_aws

from aws_lifecycle_inventory.inventory.direct_api import default_collectors
from aws_lifecycle_inventory.orchestration import run_scan

REGION = "us-east-1"
ACCOUNT_ID = "123456789012"

EXPECTED_COLLECTORS = {
    "lambda",
    "rds",
    "elasticache",
    "eks",
    "msk",
    "opensearch",
    "emr",
    "glue",
    "redshift",
    "mq",
    "mwaa",
}


def test_all_extended_collectors_registered():
    names = {c.name for c in default_collectors()}
    assert EXPECTED_COLLECTORS.issubset(names)


@mock_aws
def test_scan_runs_all_collectors_and_normalizes(monkeypatch):
    # Create a couple of extended resources alongside baseline ones.
    boto3.client("glue", region_name=REGION).create_job(
        Name="gj", Role="r", Command={"Name": "glueetl"}, GlueVersion="4.0"
    )
    boto3.client("redshift", region_name=REGION).create_cluster(
        ClusterIdentifier="rc",
        NodeType="dc2.large",
        MasterUsername="admin",
        MasterUserPassword="Password123!",
        DBName="db",
    )

    # MWAA has no moto backend; exclude it so the scan uses only moto-backed ones.
    collectors = [c for c in default_collectors() if c.name != "mwaa"]
    result = run_scan(collectors, boto3.Session(), REGION, account_id=ACCOUNT_ID)

    # No collector aborted; every one reported a status.
    assert {s.name for s in result.collector_statuses} == {c.name for c in collectors}
    assert all(s.ok for s in result.collector_statuses)

    by_id = {r.resource_id: r for r in result.records}
    assert by_id["gj"].software_name == "glue"
    assert by_id["gj"].version == "4.0"
    assert by_id["rc"].software_name == "redshift"


class _ExplodingMSK:
    name = "msk"

    def collect(self, session, account_id, region):
        raise RuntimeError("boom msk")


def test_one_extended_collector_failure_is_isolated():
    collectors = [_ExplodingMSK()] + [
        c for c in default_collectors() if c.name in {"glue"}
    ]

    @mock_aws
    def _run():
        boto3.client("glue", region_name=REGION).create_job(
            Name="gj", Role="r", Command={"Name": "glueetl"}, GlueVersion="4.0"
        )
        return run_scan(collectors, boto3.Session(), REGION, account_id=ACCOUNT_ID)

    result = _run()
    by_name = {s.name: s for s in result.collector_statuses}
    assert by_name["msk"].ok is False
    assert by_name["msk"].error_code == "RuntimeError"
    assert by_name["glue"].ok is True
    # The healthy collector still produced its record.
    assert any(r.resource_id == "gj" for r in result.records)
