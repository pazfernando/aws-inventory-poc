"""Amazon EMR release-label collector."""

from __future__ import annotations

import boto3

from aws_lifecycle_inventory.models import ResourceVersionRecord
from aws_lifecycle_inventory.orchestration import CollectorStatus


class EMRCollector:
    name = "emr"
    resource_type = "AWS::EMR::Cluster"

    def collect(
        self, session: boto3.Session, account_id: str, region: str
    ) -> tuple[list[ResourceVersionRecord], CollectorStatus]:
        client = session.client("emr", region_name=region)
        records: list[ResourceVersionRecord] = []

        for page in client.get_paginator("list_clusters").paginate():
            for summary in page.get("Clusters", []):
                cluster_id = summary.get("Id")
                if not cluster_id:
                    continue
                cluster = client.describe_cluster(ClusterId=cluster_id).get("Cluster", {})
                records.append(
                    ResourceVersionRecord(
                        account_id=account_id,
                        region=region,
                        resource_type=self.resource_type,
                        resource_id=cluster_id,
                        resource_arn=cluster.get("ClusterArn", ""),
                        software_type="release-label",
                        software_name="emr",
                        # The EMR release label (e.g. emr-7.1.0) is the version.
                        version=cluster.get("ReleaseLabel", "") or "",
                    )
                )

        return records, CollectorStatus(name=self.name, ok=True, record_count=len(records))
