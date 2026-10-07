"""Amazon ElastiCache engine/version collector."""

from __future__ import annotations

import boto3

from aws_lifecycle_inventory.models import ResourceVersionRecord
from aws_lifecycle_inventory.orchestration import CollectorStatus


class ElastiCacheCollector:
    name = "elasticache"
    resource_type = "AWS::ElastiCache::CacheCluster"

    def collect(
        self, session: boto3.Session, account_id: str, region: str
    ) -> tuple[list[ResourceVersionRecord], CollectorStatus]:
        client = session.client("elasticache", region_name=region)
        records: list[ResourceVersionRecord] = []

        for page in client.get_paginator("describe_cache_clusters").paginate():
            for cluster in page.get("CacheClusters", []):
                records.append(
                    ResourceVersionRecord(
                        account_id=account_id,
                        region=region,
                        resource_type=self.resource_type,
                        resource_id=cluster["CacheClusterId"],
                        resource_arn=cluster.get("ARN", ""),
                        software_type="cache-engine",
                        software_name=cluster.get("Engine", "") or "",
                        version=cluster.get("EngineVersion", "") or "",
                    )
                )

        return records, CollectorStatus(name=self.name, ok=True, record_count=len(records))
