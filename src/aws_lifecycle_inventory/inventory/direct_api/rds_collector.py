"""Amazon RDS and Aurora engine/version collector.

Covers both standalone DB instances and Aurora/DB clusters.
"""

from __future__ import annotations

import boto3

from aws_lifecycle_inventory.models import ResourceVersionRecord
from aws_lifecycle_inventory.orchestration import CollectorStatus


class RDSCollector:
    name = "rds"
    instance_type = "AWS::RDS::DBInstance"
    cluster_type = "AWS::RDS::DBCluster"

    def collect(
        self, session: boto3.Session, account_id: str, region: str
    ) -> tuple[list[ResourceVersionRecord], CollectorStatus]:
        client = session.client("rds", region_name=region)
        records: list[ResourceVersionRecord] = []

        for page in client.get_paginator("describe_db_instances").paginate():
            for db in page.get("DBInstances", []):
                records.append(
                    ResourceVersionRecord(
                        account_id=account_id,
                        region=region,
                        resource_type=self.instance_type,
                        resource_id=db["DBInstanceIdentifier"],
                        resource_arn=db.get("DBInstanceArn", ""),
                        software_type="db-engine",
                        software_name=db.get("Engine", "") or "",
                        version=db.get("EngineVersion", "") or "",
                    )
                )

        for page in client.get_paginator("describe_db_clusters").paginate():
            for cluster in page.get("DBClusters", []):
                records.append(
                    ResourceVersionRecord(
                        account_id=account_id,
                        region=region,
                        resource_type=self.cluster_type,
                        resource_id=cluster["DBClusterIdentifier"],
                        resource_arn=cluster.get("DBClusterArn", ""),
                        software_type="db-engine",
                        software_name=cluster.get("Engine", "") or "",
                        version=cluster.get("EngineVersion", "") or "",
                    )
                )

        return records, CollectorStatus(name=self.name, ok=True, record_count=len(records))
