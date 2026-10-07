"""Amazon Redshift version collector.

Redshift exposes a cluster version only where available; when the API does not
expose it, the version stays explicitly empty (no invention).
"""

from __future__ import annotations

import boto3

from aws_lifecycle_inventory.models import ResourceVersionRecord
from aws_lifecycle_inventory.orchestration import CollectorStatus


class RedshiftCollector:
    name = "redshift"
    resource_type = "AWS::Redshift::Cluster"

    def collect(
        self, session: boto3.Session, account_id: str, region: str
    ) -> tuple[list[ResourceVersionRecord], CollectorStatus]:
        client = session.client("redshift", region_name=region)
        records: list[ResourceVersionRecord] = []

        for page in client.get_paginator("describe_clusters").paginate():
            for cluster in page.get("Clusters", []):
                cluster_id = cluster.get("ClusterIdentifier", "")
                records.append(
                    ResourceVersionRecord(
                        account_id=account_id,
                        region=region,
                        resource_type=self.resource_type,
                        resource_id=cluster_id,
                        resource_arn=(
                            f"arn:aws:redshift:{region}:{account_id}:cluster:{cluster_id}"
                            if cluster_id
                            else ""
                        ),
                        software_type="cluster-version",
                        software_name="redshift",
                        version=cluster.get("ClusterVersion", "") or "",
                    )
                )

        return records, CollectorStatus(name=self.name, ok=True, record_count=len(records))
