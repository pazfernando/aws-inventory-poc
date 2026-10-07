"""Moto-backed tests for the baseline direct-API collectors (tasks 4.1-4.4)."""

from __future__ import annotations

import boto3
import pytest
from moto import mock_aws

from aws_lifecycle_inventory.inventory.direct_api._common import split_lambda_runtime
from aws_lifecycle_inventory.inventory.direct_api.eks_collector import EKSCollector
from aws_lifecycle_inventory.inventory.direct_api.elasticache_collector import (
    ElastiCacheCollector,
)
from aws_lifecycle_inventory.inventory.direct_api.rds_collector import RDSCollector

REGION = "us-east-1"
ACCOUNT_ID = "123456789012"


# --- task 4.1: Lambda runtime normalization --------------------------------

@pytest.mark.parametrize(
    "runtime,expected",
    [
        ("python3.12", ("python", "3.12")),
        ("nodejs20.x", ("nodejs", "20.x")),
        ("java21", ("java", "21")),
        ("dotnet8", ("dotnet", "8")),
        ("ruby", ("ruby", "")),  # no version exposed -> stays empty
    ],
)
def test_split_lambda_runtime(runtime, expected):
    assert split_lambda_runtime(runtime) == expected


# --- task 4.2: RDS + Aurora ------------------------------------------------

@mock_aws
def test_rds_collector_normalizes_engine_and_version_and_missing_stays_empty():
    rds = boto3.client("rds", region_name=REGION)
    rds.create_db_instance(
        DBInstanceIdentifier="my-db",
        Engine="postgres",
        EngineVersion="15.4",
        DBInstanceClass="db.t3.micro",
        AllocatedStorage=20,
        MasterUsername="admin",
        MasterUserPassword="Password123!",
    )

    records, status = RDSCollector().collect(boto3.Session(), ACCOUNT_ID, REGION)

    assert status.ok is True
    instances = [r for r in records if r.resource_type == "AWS::RDS::DBInstance"]
    assert len(instances) == 1
    rec = instances[0]
    assert rec.software_name == "postgres"
    assert rec.version == "15.4"

    # A record built with no engine version stays explicitly empty (no invention).
    from aws_lifecycle_inventory.models import ResourceVersionRecord

    empty = ResourceVersionRecord(
        account_id=ACCOUNT_ID,
        region=REGION,
        resource_type="AWS::RDS::DBInstance",
        resource_id="no-version",
    )
    assert empty.version == ""


# --- task 4.3: ElastiCache -------------------------------------------------

@mock_aws
def test_elasticache_collector_normalizes_engine_and_version():
    ec = boto3.client("elasticache", region_name=REGION)
    ec.create_cache_cluster(
        CacheClusterId="my-cache",
        Engine="redis",
        EngineVersion="7.1",
        CacheNodeType="cache.t3.micro",
        NumCacheNodes=1,
    )

    records, status = ElastiCacheCollector().collect(boto3.Session(), ACCOUNT_ID, REGION)

    assert status.ok is True
    assert len(records) == 1
    assert records[0].software_name == "redis"
    assert records[0].version == "7.1"


# --- task 4.4: EKS ---------------------------------------------------------

@mock_aws
def test_eks_collector_normalizes_kubernetes_version():
    eks = boto3.client("eks", region_name=REGION)
    eks.create_cluster(
        name="my-eks",
        version="1.30",
        roleArn=f"arn:aws:iam::{ACCOUNT_ID}:role/eks",
        resourcesVpcConfig={},
    )

    records, status = EKSCollector().collect(boto3.Session(), ACCOUNT_ID, REGION)

    assert status.ok is True
    assert len(records) == 1
    assert records[0].software_name == "kubernetes"
    assert records[0].version == "1.30"
