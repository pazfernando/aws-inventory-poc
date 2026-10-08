"""VPC presence collector (non-version-bearing)."""

from __future__ import annotations

import boto3

from aws_lifecycle_inventory.models import ResourceVersionRecord
from aws_lifecycle_inventory.orchestration import CollectorStatus


class VPCCollector:
    name = "vpcs"
    resource_type = "AWS::EC2::VPC"

    def collect(
        self, session: boto3.Session, account_id: str, region: str
    ) -> tuple[list[ResourceVersionRecord], CollectorStatus]:
        client = session.client("ec2", region_name=region)
        records: list[ResourceVersionRecord] = []
        for page in client.get_paginator("describe_vpcs").paginate():
            for vpc in page.get("Vpcs", []):
                vpc_id = vpc["VpcId"]
                records.append(
                    ResourceVersionRecord(
                        account_id=account_id,
                        region=region,
                        resource_type=self.resource_type,
                        resource_id=vpc_id,
                        resource_arn=(
                            f"arn:aws:ec2:{region}:{account_id}:vpc/{vpc_id}"
                        ),
                    )
                )
        return records, CollectorStatus(name=self.name, ok=True, record_count=len(records))
