"""Amazon EKS Kubernetes version collector."""

from __future__ import annotations

import boto3

from aws_lifecycle_inventory.models import ResourceVersionRecord
from aws_lifecycle_inventory.orchestration import CollectorStatus


class EKSCollector:
    name = "eks"
    resource_type = "AWS::EKS::Cluster"

    def collect(
        self, session: boto3.Session, account_id: str, region: str
    ) -> tuple[list[ResourceVersionRecord], CollectorStatus]:
        client = session.client("eks", region_name=region)
        records: list[ResourceVersionRecord] = []

        for page in client.get_paginator("list_clusters").paginate():
            for name in page.get("clusters", []):
                cluster = client.describe_cluster(name=name)["cluster"]
                records.append(
                    ResourceVersionRecord(
                        account_id=account_id,
                        region=region,
                        resource_type=self.resource_type,
                        resource_id=cluster.get("name", name),
                        resource_arn=cluster.get("arn", ""),
                        software_type="orchestrator",
                        software_name="kubernetes",
                        version=cluster.get("version", "") or "",
                    )
                )

        return records, CollectorStatus(name=self.name, ok=True, record_count=len(records))
