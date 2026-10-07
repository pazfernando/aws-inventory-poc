"""Amazon MSK (Managed Streaming for Apache Kafka) version collector."""

from __future__ import annotations

import boto3

from aws_lifecycle_inventory.models import ResourceVersionRecord
from aws_lifecycle_inventory.orchestration import CollectorStatus


class MSKCollector:
    name = "msk"
    resource_type = "AWS::MSK::Cluster"

    def collect(
        self, session: boto3.Session, account_id: str, region: str
    ) -> tuple[list[ResourceVersionRecord], CollectorStatus]:
        client = session.client("kafka", region_name=region)
        records: list[ResourceVersionRecord] = []

        for page in client.get_paginator("list_clusters_v2").paginate():
            for cluster in page.get("ClusterInfoList", []):
                # Kafka version is exposed for provisioned clusters; serverless
                # clusters expose none, which stays explicitly empty.
                version = ""
                provisioned = cluster.get("Provisioned") or {}
                version = provisioned.get("CurrentBrokerSoftwareInfo", {}).get(
                    "KafkaVersion", ""
                ) or ""
                records.append(
                    ResourceVersionRecord(
                        account_id=account_id,
                        region=region,
                        resource_type=self.resource_type,
                        resource_id=cluster.get("ClusterName", ""),
                        resource_arn=cluster.get("ClusterArn", ""),
                        software_type="streaming-engine",
                        software_name="kafka",
                        version=version,
                    )
                )

        return records, CollectorStatus(name=self.name, ok=True, record_count=len(records))
