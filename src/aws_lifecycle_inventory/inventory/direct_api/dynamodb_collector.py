"""DynamoDB table presence collector (non-version-bearing)."""

from __future__ import annotations

import boto3

from aws_lifecycle_inventory.models import ResourceVersionRecord
from aws_lifecycle_inventory.orchestration import CollectorStatus


class DynamoDBCollector:
    name = "dynamodb-tables"
    resource_type = "AWS::DynamoDB::Table"

    def collect(
        self, session: boto3.Session, account_id: str, region: str
    ) -> tuple[list[ResourceVersionRecord], CollectorStatus]:
        client = session.client("dynamodb", region_name=region)
        records: list[ResourceVersionRecord] = []
        for page in client.get_paginator("list_tables").paginate():
            for table_name in page.get("TableNames", []):
                records.append(
                    ResourceVersionRecord(
                        account_id=account_id,
                        region=region,
                        resource_type=self.resource_type,
                        resource_id=table_name,
                        resource_arn=(
                            f"arn:aws:dynamodb:{region}:{account_id}:table/{table_name}"
                        ),
                    )
                )
        return records, CollectorStatus(name=self.name, ok=True, record_count=len(records))
