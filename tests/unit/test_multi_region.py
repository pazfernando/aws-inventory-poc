"""Tests for multi-region scan orchestration (Change 06)."""

from __future__ import annotations

import io
import json

import boto3
from moto import mock_aws

from aws_lifecycle_inventory.cli import build_parser, run
from aws_lifecycle_inventory.inventory.direct_api import default_collectors
from aws_lifecycle_inventory.models import ResourceVersionRecord
from aws_lifecycle_inventory.orchestration import (
    CollectorStatus,
    run_scan_multi_region,
)

REGIONS = ["us-east-1", "eu-west-1"]
ACCOUNT_ID = "123456789012"


def _create_lambda_role() -> str:
    iam = boto3.client("iam", region_name="us-east-1")
    role = iam.create_role(
        RoleName="lambda-exec",
        AssumeRolePolicyDocument=json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "lambda.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    }
                ],
            }
        ),
    )
    return role["Role"]["Arn"]


# --- task 1.1: region list accepted, collectors run per region ----------------


@mock_aws
def test_two_regions_produce_records_for_both():
    role_arn = _create_lambda_role()
    for region in REGIONS:
        boto3.client("lambda", region_name=region).create_function(
            FunctionName=f"fn-{region}",
            Runtime="python3.12",
            Role=role_arn,
            Handler="index.handler",
            Code={"ZipFile": b"def handler(e,c): return 1"},
        )

    session = boto3.Session(region_name="us-east-1")
    result = run_scan_multi_region(
        default_collectors(), session, REGIONS, account_id=ACCOUNT_ID
    )

    assert {r.region for r in result.records} == set(REGIONS)
    assert {r.resource_id for r in result.records} == {"fn-us-east-1", "fn-eu-west-1"}


# --- task 2.1: per-region provenance survives combining ------------------------


class _RegionCollector:
    name = "regioned"

    def collect(self, session, account_id, region):
        record = ResourceVersionRecord(
            account_id=account_id,
            region=region,
            resource_type="AWS::Test::Resource",
            resource_id=f"res-{region}",
            software_name="thing",
            version="1.0",
        )
        return [record], CollectorStatus(name=self.name, ok=True, record_count=1)


def test_records_keep_originating_region_when_combined():
    session = boto3.Session(region_name="us-east-1")
    result = run_scan_multi_region(
        [_RegionCollector()], session, REGIONS, account_id=ACCOUNT_ID
    )

    assert [(r.region, r.resource_id) for r in result.records] == [
        ("us-east-1", "res-us-east-1"),
        ("eu-west-1", "res-eu-west-1"),
    ]


# --- task 2.2: one region failing, others complete -----------------------------


class _WestFailCollector:
    """Fails only in eu-west-1 (e.g. service not available in that region)."""

    name = "west-fail"

    def collect(self, session, account_id, region):
        if region == "eu-west-1":
            raise RuntimeError("service not available in region")
        record = ResourceVersionRecord(
            account_id=account_id,
            region=region,
            resource_type="AWS::Test::Resource",
            resource_id=f"ok-{region}",
            software_name="thing",
            version="1.0",
        )
        return [record], CollectorStatus(name=self.name, ok=True, record_count=1)


def test_one_region_fails_others_complete():
    session = boto3.Session(region_name="us-east-1")
    result = run_scan_multi_region(
        [_RegionCollector(), _WestFailCollector()], session, REGIONS, account_id=ACCOUNT_ID
    )

    # eu-west-1 still produced records via the healthy collector.
    assert {r.region for r in result.records} == set(REGIONS)

    by_region_name = {(s.region, s.name): s for s in result.collector_statuses}
    failed = by_region_name[("eu-west-1", "west-fail")]
    assert failed.ok is False
    assert failed.error_code == "RuntimeError"
    # The same collector succeeded in the other region: isolation, not abort.
    assert by_region_name[("us-east-1", "west-fail")].ok is True


# --- task 3.1: structured execution summary ------------------------------------


class _CustomSourceCollector:
    name = "custom"
    source = "TEST_SOURCE"

    def collect(self, session, account_id, region):
        return [], CollectorStatus(name=self.name, ok=True, record_count=0)


def test_execution_summary_breaks_down_by_region_source_collector():
    session = boto3.Session(region_name="us-east-1")
    result = run_scan_multi_region(
        [_RegionCollector(), _WestFailCollector(), _CustomSourceCollector()],
        session,
        REGIONS,
        account_id=ACCOUNT_ID,
    )

    summary = result.execution_summary()

    # Every breakdown level reports status: region -> source -> collector.
    assert set(summary) == set(REGIONS)
    east = summary["us-east-1"]
    assert set(east) == {"DIRECT_API", "TEST_SOURCE"}
    assert east["DIRECT_API"]["regioned"]["ok"] is True
    assert east["DIRECT_API"]["regioned"]["record_count"] == 1
    assert east["DIRECT_API"]["west-fail"]["ok"] is True
    assert east["TEST_SOURCE"]["custom"]["ok"] is True

    west = summary["eu-west-1"]
    assert west["DIRECT_API"]["west-fail"]["ok"] is False
    assert west["DIRECT_API"]["west-fail"]["error_code"] == "RuntimeError"
    assert west["DIRECT_API"]["regioned"]["record_count"] == 1


# --- task 1.2: CLI --regions option --------------------------------------------


def test_cli_help_shows_regions_option():
    parser = build_parser()
    help_text = io.StringIO()
    parser.print_help(help_text)
    assert "--regions" in help_text.getvalue()


@mock_aws
def test_cli_regions_run_honors_multiple_regions(tmp_path):
    role_arn = _create_lambda_role()
    for region in REGIONS:
        boto3.client("lambda", region_name=region).create_function(
            FunctionName=f"fn-{region}",
            Runtime="python3.12",
            Role=role_arn,
            Handler="index.handler",
            Code={"ZipFile": b"def handler(e,c): return 1"},
        )

    output = tmp_path / "inventory.csv"
    args = build_parser().parse_args(
        ["--regions", "us-east-1,eu-west-1", "--output", str(output)]
    )
    result = run(args)

    assert {r.region for r in result.records} == set(REGIONS)
    rows = output.read_text().splitlines()
    assert "fn-us-east-1" in "\n".join(rows)
    assert "fn-eu-west-1" in "\n".join(rows)


@mock_aws
def test_cli_regions_default_to_session_region(tmp_path):
    role_arn = _create_lambda_role()
    boto3.client("lambda", region_name="us-east-1").create_function(
        FunctionName="fn-east",
        Runtime="python3.12",
        Role=role_arn,
        Handler="index.handler",
        Code={"ZipFile": b"def handler(e,c): return 1"},
    )

    output = tmp_path / "inventory.csv"
    # No --regions/--region: defaults to the session's configured region
    # (AWS_DEFAULT_REGION=us-east-1, set by the shared test fixture).
    args = build_parser().parse_args(["--output", str(output)])
    result = run(args)

    assert {r.region for r in result.records} == {"us-east-1"}
