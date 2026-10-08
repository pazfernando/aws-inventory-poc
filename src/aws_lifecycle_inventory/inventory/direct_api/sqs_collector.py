"""SQS queue presence collector (non-version-bearing)."""

from __future__ import annotations

import boto3

from aws_lifecycle_inventory.models import ResourceVersionRecord
from aws_lifecycle_inventory.orchestration import CollectorStatus


class SQSCollector:
    name = "sqs-queues"
    resource_type = "AWS::SQS::Queue"

    def collect(
        self, session: boto3.Session, account_id: str, region: str
    ) -> tuple[list[ResourceVersionRecord], CollectorStatus]:
        client = session.client("sqs", region_name=region)
        records: list[ResourceVersionRecord] = []
        for page in client.get_paginator("list_queues").paginate():
            for queue_url in page.get("QueueUrls", []):
                # The queue name is the last URL path segment.
                queue_name = queue_url.rstrip("/").rsplit("/", 1)[-1]
                records.append(
                    ResourceVersionRecord(
                        account_id=account_id,
                        region=region,
                        resource_type=self.resource_type,
                        resource_id=queue_name,
                        resource_arn=(
                            f"arn:aws:sqs:{region}:{account_id}:{queue_name}"
                        ),
                    )
                )
        return records, CollectorStatus(name=self.name, ok=True, record_count=len(records))
