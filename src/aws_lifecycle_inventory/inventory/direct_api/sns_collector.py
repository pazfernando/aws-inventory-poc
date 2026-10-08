"""SNS topic presence collector (non-version-bearing)."""

from __future__ import annotations

import boto3

from aws_lifecycle_inventory.models import ResourceVersionRecord
from aws_lifecycle_inventory.orchestration import CollectorStatus


class SNSCollector:
    name = "sns-topics"
    resource_type = "AWS::SNS::Topic"

    def collect(
        self, session: boto3.Session, account_id: str, region: str
    ) -> tuple[list[ResourceVersionRecord], CollectorStatus]:
        client = session.client("sns", region_name=region)
        records: list[ResourceVersionRecord] = []
        for page in client.get_paginator("list_topics").paginate():
            for topic in page.get("Topics", []):
                arn = topic.get("TopicArn", "")
                # The topic name is the last ARN segment.
                topic_name = arn.rsplit(":", 1)[-1] if arn else ""
                records.append(
                    ResourceVersionRecord(
                        account_id=account_id,
                        region=region,
                        resource_type=self.resource_type,
                        resource_id=topic_name,
                        resource_arn=arn,
                    )
                )
        return records, CollectorStatus(name=self.name, ok=True, record_count=len(records))
