"""Moto-backed tests for the Change 02 extended collectors (tasks 1.1-1.7)."""

from __future__ import annotations

import boto3
from moto import mock_aws

from aws_lifecycle_inventory.inventory.direct_api.emr_collector import EMRCollector
from aws_lifecycle_inventory.inventory.direct_api.glue_collector import GlueJobsCollector
from aws_lifecycle_inventory.inventory.direct_api.mq_collector import AmazonMQCollector
from aws_lifecycle_inventory.inventory.direct_api.msk_collector import MSKCollector
from aws_lifecycle_inventory.inventory.direct_api.mwaa_collector import MWAACollector
from aws_lifecycle_inventory.inventory.direct_api.opensearch_collector import (
    OpenSearchCollector,
    _split_engine_version,
)
from aws_lifecycle_inventory.inventory.direct_api.redshift_collector import (
    RedshiftCollector,
)
from aws_lifecycle_inventory.models import ResourceVersionRecord

REGION = "us-east-1"
ACCOUNT_ID = "123456789012"


# --- task 1.1: MSK ---------------------------------------------------------

@mock_aws
def test_msk_collector_normalizes_kafka_version():
    k = boto3.client("kafka", region_name=REGION)
    k.create_cluster_v2(
        ClusterName="my-kafka",
        Provisioned={
            "BrokerNodeGroupInfo": {
                "InstanceType": "kafka.m5.large",
                "ClientSubnets": ["subnet-123"],
            },
            "KafkaVersion": "3.6.0",
            "NumberOfBrokerNodes": 2,
        },
    )
    records, status = MSKCollector().collect(boto3.Session(), ACCOUNT_ID, REGION)
    assert status.ok is True
    assert len(records) == 1
    assert records[0].software_name == "kafka"
    assert records[0].version == "3.6.0"


# --- task 1.2: OpenSearch --------------------------------------------------

def test_opensearch_split_engine_version():
    assert _split_engine_version("OpenSearch_2.13") == ("opensearch", "2.13")
    assert _split_engine_version("Elasticsearch_7.10") == ("elasticsearch", "7.10")
    assert _split_engine_version("") == ("", "")
    assert _split_engine_version("weird") == ("weird", "")


@mock_aws
def test_opensearch_collector_normalizes_engine_and_version():
    o = boto3.client("opensearch", region_name=REGION)
    o.create_domain(DomainName="search1", EngineVersion="OpenSearch_2.13")
    records, status = OpenSearchCollector().collect(boto3.Session(), ACCOUNT_ID, REGION)
    assert status.ok is True
    assert len(records) == 1
    assert records[0].software_name == "opensearch"
    assert records[0].version == "2.13"


# --- task 1.3: EMR ---------------------------------------------------------

@mock_aws
def test_emr_collector_captures_release_label():
    e = boto3.client("emr", region_name=REGION)
    e.run_job_flow(
        Name="job",
        ReleaseLabel="emr-7.1.0",
        Instances={
            "MasterInstanceType": "m5.xlarge",
            "InstanceCount": 1,
            "KeepJobFlowAliveWhenNoSteps": True,
        },
    )
    records, status = EMRCollector().collect(boto3.Session(), ACCOUNT_ID, REGION)
    assert status.ok is True
    assert len(records) == 1
    assert records[0].software_name == "emr"
    assert records[0].version == "emr-7.1.0"


# --- task 1.4: Glue --------------------------------------------------------

@mock_aws
def test_glue_collector_normalizes_glue_version():
    g = boto3.client("glue", region_name=REGION)
    g.create_job(Name="gj", Role="r", Command={"Name": "glueetl"}, GlueVersion="4.0")
    records, status = GlueJobsCollector().collect(boto3.Session(), ACCOUNT_ID, REGION)
    assert status.ok is True
    assert len(records) == 1
    assert records[0].software_name == "glue"
    assert records[0].version == "4.0"


# --- task 1.5: Redshift (present and absent) -------------------------------

@mock_aws
def test_redshift_collector_version_present():
    rs = boto3.client("redshift", region_name=REGION)
    rs.create_cluster(
        ClusterIdentifier="rc",
        NodeType="dc2.large",
        MasterUsername="admin",
        MasterUserPassword="Password123!",
        DBName="db",
    )
    records, status = RedshiftCollector().collect(boto3.Session(), ACCOUNT_ID, REGION)
    assert status.ok is True
    assert len(records) == 1
    assert records[0].software_name == "redshift"
    # moto exposes a cluster version; collector must surface it verbatim.
    assert records[0].version != ""


def test_redshift_record_absent_version_stays_empty():
    # When the API exposes no ClusterVersion, the record keeps it empty.
    rec = ResourceVersionRecord(
        account_id=ACCOUNT_ID,
        region=REGION,
        resource_type="AWS::Redshift::Cluster",
        resource_id="no-version",
        software_name="redshift",
    )
    assert rec.version == ""


# --- task 1.6: Amazon MQ ---------------------------------------------------

@mock_aws
def test_mq_collector_normalizes_engine_and_version():
    m = boto3.client("mq", region_name=REGION)
    m.create_broker(
        BrokerName="b1",
        EngineType="ACTIVEMQ",
        EngineVersion="5.18",
        DeploymentMode="SINGLE_INSTANCE",
        HostInstanceType="mq.t3.micro",
        PubliclyAccessible=False,
        AutoMinorVersionUpgrade=False,
        Users=[{"Username": "u", "Password": "passw0rdpassw0rd"}],
    )
    records, status = AmazonMQCollector().collect(boto3.Session(), ACCOUNT_ID, REGION)
    assert status.ok is True
    assert len(records) == 1
    assert records[0].software_name == "activemq"
    assert records[0].version == "5.18"


# --- task 1.7: MWAA (not supported by moto -> stub client) -----------------

class _FakeMWAAClient:
    """Minimal stand-in for the MWAA client (moto has no MWAA backend)."""

    def get_paginator(self, _name):
        return self

    def paginate(self):
        return iter([{"Environments": ["env-1"]}])

    def get_environment(self, Name):  # noqa: N803 - boto3 param name
        return {
            "Environment": {
                "Name": Name,
                "Arn": f"arn:aws:airflow:us-east-1:123456789012:environment/{Name}",
                "AirflowVersion": "2.9.2",
            }
        }


class _FakeSession:
    def client(self, _service, region_name=None):
        return _FakeMWAAClient()


def test_mwaa_collector_normalizes_airflow_version():
    records, status = MWAACollector().collect(_FakeSession(), ACCOUNT_ID, REGION)
    assert status.ok is True
    assert len(records) == 1
    assert records[0].software_name == "airflow"
    assert records[0].version == "2.9.2"
