"""Scan is discovery-only; lifecycle is a separate composable step
(refactor-lifecycle-assessment-reuse, tasks 2.1 and 2.2)."""

from __future__ import annotations

import boto3
from moto import mock_aws

from aws_lifecycle_inventory.inventory.direct_api.lambda_collector import LambdaCollector
from aws_lifecycle_inventory.lifecycle import assess_records
from aws_lifecycle_inventory.lifecycle.models import LifecycleStatus
from aws_lifecycle_inventory.orchestration import run_scan

REGION = "us-east-1"
ACCOUNT_ID = "123456789012"


def _create_lambda(runtime="python3.12"):
    role = boto3.client("iam", region_name=REGION).create_role(
        RoleName="r",
        AssumeRolePolicyDocument="{}",
    )["Role"]["Arn"]
    boto3.client("lambda", region_name=REGION).create_function(
        FunctionName="fn",
        Runtime=runtime,
        Role=role,
        Handler="index.handler",
        Code={"ZipFile": b"def handler(e,c): return 1"},
    )


# --- task 2.1: scan does not evaluate lifecycle ----------------------------

@mock_aws
def test_scan_output_has_unevaluated_lifecycle_fields():
    _create_lambda()
    result = run_scan([LambdaCollector()], boto3.Session(), REGION, ACCOUNT_ID)

    assert len(result.records) == 1
    rec = result.records[0]
    # Discovery produced the record and its version, but lifecycle is untouched:
    assert rec.version == "3.12"
    assert rec.lifecycle_status == LifecycleStatus.UNKNOWN.value  # model default
    assert rec.eol_date is None
    assert rec.lifecycle_source == ""
    assert rec.evaluated_at is None


# --- task 2.2: scan then assess composes -----------------------------------

@mock_aws
def test_scan_then_assess_populates_lifecycle():
    _create_lambda()
    result = run_scan([LambdaCollector()], boto3.Session(), REGION, ACCOUNT_ID)

    # Compose the separate assessment step (session=None -> EndOfLife only).
    assessed = assess_records(result.records, session=None)

    assert len(assessed) == 1
    rec = assessed[0]
    assert rec.evaluated_at is not None
    # EndOfLife seed knows python 3.12 -> a concrete (non-UNKNOWN) conclusion.
    assert rec.lifecycle_status != LifecycleStatus.UNKNOWN.value
    assert rec.lifecycle_source != ""
