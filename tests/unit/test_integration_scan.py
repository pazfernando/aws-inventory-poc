"""End-to-end integration test: full scan across baseline collectors to CSV.

Covers tasks 4.1 (Lambda via the real collector), 3.2 (CLI wiring), and 5.1.
"""

from __future__ import annotations

import io
import json

import boto3
from moto import mock_aws

from aws_lifecycle_inventory.cli import build_parser, run
from aws_lifecycle_inventory.output.csv_writer import BASELINE_COLUMNS

REGION = "us-east-1"


def _create_lambda_role() -> str:
    iam = boto3.client("iam", region_name=REGION)
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


@mock_aws
def test_full_scan_writes_normalized_csv(tmp_path):
    # Lambda function
    role_arn = _create_lambda_role()
    lam = boto3.client("lambda", region_name=REGION)
    lam.create_function(
        FunctionName="my-fn",
        Runtime="python3.12",
        Role=role_arn,
        Handler="index.handler",
        Code={"ZipFile": b"def handler(e,c): return 1"},
    )

    # RDS instance
    boto3.client("rds", region_name=REGION).create_db_instance(
        DBInstanceIdentifier="my-db",
        Engine="postgres",
        EngineVersion="15.4",
        DBInstanceClass="db.t3.micro",
        AllocatedStorage=20,
        MasterUsername="admin",
        MasterUserPassword="Password123!",
    )

    # ElastiCache cluster
    boto3.client("elasticache", region_name=REGION).create_cache_cluster(
        CacheClusterId="my-cache",
        Engine="redis",
        EngineVersion="7.1",
        CacheNodeType="cache.t3.micro",
        NumCacheNodes=1,
    )

    # EKS cluster
    boto3.client("eks", region_name=REGION).create_cluster(
        name="my-eks",
        version="1.30",
        roleArn=role_arn,
        resourcesVpcConfig={},
    )

    output = tmp_path / "inventory.csv"
    args = build_parser().parse_args(["--region", REGION, "--output", str(output)])
    result = run(args)

    # The baseline Change 01 collectors all succeeded. (MWAA has no moto backend,
    # so it reports a failed status; that failure must not abort the scan, which
    # is itself the partial-failure guarantee.)
    by_status = {s.name: s for s in result.collector_statuses}
    for name in ("lambda", "rds", "elasticache", "eks"):
        assert by_status[name].ok is True

    # CSV header keeps the baseline columns first (append-only), one row per resource.
    lines = output.read_text().splitlines()
    header = lines[0].split(",")
    assert header[: len(BASELINE_COLUMNS)] == list(BASELINE_COLUMNS)
    rows = [dict(zip(header, line.split(","))) for line in lines[1:]]

    by_id = {r["resource_id"]: r for r in rows}
    assert by_id["my-fn"]["software_name"] == "python"
    assert by_id["my-fn"]["version"] == "3.12"
    assert by_id["my-db"]["software_name"] == "postgres"
    assert by_id["my-db"]["version"] == "15.4"
    assert by_id["my-cache"]["software_name"] == "redis"
    assert by_id["my-cache"]["version"] == "7.1"
    assert by_id["my-eks"]["software_name"] == "kubernetes"
    assert by_id["my-eks"]["version"] == "1.30"


def test_cli_help_runs():
    parser = build_parser()
    help_text = io.StringIO()
    parser.print_help(help_text)
    assert "aws-lifecycle-inventory" in help_text.getvalue()
    assert "--profile" in help_text.getvalue()


# --- refactor-lifecycle-assessment-reuse task 4.2 --------------------------

@mock_aws
def test_cli_composes_assessment_and_populates_lifecycle_columns(tmp_path):
    # The CLI composes scan -> assess -> write, so the output CSV carries
    # populated lifecycle columns (python 3.12 is known to the EndOfLife seed).
    role_arn = _create_lambda_role()
    boto3.client("lambda", region_name=REGION).create_function(
        FunctionName="my-fn",
        Runtime="python3.12",
        Role=role_arn,
        Handler="index.handler",
        Code={"ZipFile": b"def handler(e,c): return 1"},
    )

    output = tmp_path / "inventory.csv"
    args = build_parser().parse_args(["--region", REGION, "--output", str(output)])
    run(args)

    lines = output.read_text().splitlines()
    header = lines[0].split(",")
    rows = [dict(zip(header, line.split(","))) for line in lines[1:]]
    fn = next(r for r in rows if r["resource_id"] == "my-fn")

    # Lifecycle columns are populated by the composed assessment step.
    assert fn["lifecycle_status"] != ""
    assert fn["lifecycle_status"] != "UNKNOWN"
    assert fn["lifecycle_source"] != ""
    assert fn["evaluated_at"] != ""

