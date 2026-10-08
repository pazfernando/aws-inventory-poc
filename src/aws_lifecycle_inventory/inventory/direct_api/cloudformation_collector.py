"""CloudFormation stacks and stacksets presence collector (non-version-bearing)."""

from __future__ import annotations

import boto3

from aws_lifecycle_inventory.models import ResourceVersionRecord
from aws_lifecycle_inventory.orchestration import CollectorStatus


class CloudFormationCollector:
    name = "cloudformation"
    stack_type = "AWS::CloudFormation::Stack"
    stackset_type = "AWS::CloudFormation::StackSet"

    def collect(
        self, session: boto3.Session, account_id: str, region: str
    ) -> tuple[list[ResourceVersionRecord], CollectorStatus]:
        client = session.client("cloudformation", region_name=region)
        records: list[ResourceVersionRecord] = []

        for page in client.get_paginator("describe_stacks").paginate():
            for stack in page.get("Stacks", []):
                records.append(
                    ResourceVersionRecord(
                        account_id=account_id,
                        region=region,
                        resource_type=self.stack_type,
                        resource_id=stack["StackName"],
                        resource_arn=stack.get("StackId", ""),
                    )
                )

        for page in client.get_paginator("list_stack_sets").paginate():
            for summary in page.get("Summaries", []):
                stackset_name = summary.get("StackSetName", "")
                records.append(
                    ResourceVersionRecord(
                        account_id=account_id,
                        region=region,
                        resource_type=self.stackset_type,
                        resource_id=stackset_name,
                        resource_arn=summary.get("StackSetId", ""),
                    )
                )

        return records, CollectorStatus(name=self.name, ok=True, record_count=len(records))
