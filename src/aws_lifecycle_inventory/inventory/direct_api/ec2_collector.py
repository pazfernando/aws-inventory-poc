"""EC2 instance presence collector (non-version-bearing)."""

from __future__ import annotations

import boto3

from aws_lifecycle_inventory.models import ResourceVersionRecord
from aws_lifecycle_inventory.orchestration import CollectorStatus


class EC2InstanceCollector:
    name = "ec2-instances"
    resource_type = "AWS::EC2::Instance"

    def collect(
        self, session: boto3.Session, account_id: str, region: str
    ) -> tuple[list[ResourceVersionRecord], CollectorStatus]:
        client = session.client("ec2", region_name=region)
        records: list[ResourceVersionRecord] = []
        for page in client.get_paginator("describe_instances").paginate():
            for reservation in page.get("Reservations", []):
                for inst in reservation.get("Instances", []):
                    instance_id = inst["InstanceId"]
                    records.append(
                        ResourceVersionRecord(
                            account_id=account_id,
                            region=region,
                            resource_type=self.resource_type,
                            resource_id=instance_id,
                            resource_arn=(
                                f"arn:aws:ec2:{region}:{account_id}:instance/{instance_id}"
                            ),
                        )
                    )
        return records, CollectorStatus(name=self.name, ok=True, record_count=len(records))
