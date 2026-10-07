"""Amazon MQ broker engine/version collector."""

from __future__ import annotations

import boto3

from aws_lifecycle_inventory.models import ResourceVersionRecord
from aws_lifecycle_inventory.orchestration import CollectorStatus


class AmazonMQCollector:
    name = "mq"
    resource_type = "AWS::AmazonMQ::Broker"

    def collect(
        self, session: boto3.Session, account_id: str, region: str
    ) -> tuple[list[ResourceVersionRecord], CollectorStatus]:
        client = session.client("mq", region_name=region)
        records: list[ResourceVersionRecord] = []

        for page in client.get_paginator("list_brokers").paginate():
            for summary in page.get("BrokerSummaries", []):
                broker_id = summary.get("BrokerId")
                if not broker_id:
                    continue
                broker = client.describe_broker(BrokerId=broker_id)
                records.append(
                    ResourceVersionRecord(
                        account_id=account_id,
                        region=region,
                        resource_type=self.resource_type,
                        resource_id=broker.get("BrokerName", broker_id),
                        resource_arn=broker.get("BrokerArn", ""),
                        software_type="broker-engine",
                        software_name=(broker.get("EngineType", "") or "").lower(),
                        version=broker.get("EngineVersion", "") or "",
                    )
                )

        return records, CollectorStatus(name=self.name, ok=True, record_count=len(records))
