"""AWS Lambda runtime collector."""

from __future__ import annotations

import boto3

from aws_lifecycle_inventory.inventory.direct_api._common import split_lambda_runtime
from aws_lifecycle_inventory.models import ResourceVersionRecord
from aws_lifecycle_inventory.orchestration import CollectorStatus


class LambdaCollector:
    name = "lambda"
    resource_type = "AWS::Lambda::Function"

    def collect(
        self, session: boto3.Session, account_id: str, region: str
    ) -> tuple[list[ResourceVersionRecord], CollectorStatus]:
        client = session.client("lambda", region_name=region)
        records: list[ResourceVersionRecord] = []
        for page in client.get_paginator("list_functions").paginate():
            for fn in page.get("Functions", []):
                runtime = fn.get("Runtime", "") or ""
                software_name, version = split_lambda_runtime(runtime)
                records.append(
                    ResourceVersionRecord(
                        account_id=account_id,
                        region=region,
                        resource_type=self.resource_type,
                        resource_id=fn["FunctionName"],
                        resource_arn=fn.get("FunctionArn", ""),
                        software_type="runtime",
                        software_name=software_name,
                        version=version,
                    )
                )
        return records, CollectorStatus(name=self.name, ok=True, record_count=len(records))
