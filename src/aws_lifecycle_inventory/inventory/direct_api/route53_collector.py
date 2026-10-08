"""Route53 hosted zone presence collector (non-version-bearing, global).

Route53 is a global service. To avoid duplicating a hosted zone once per region
in a multi-region scan, this collector emits each zone only once per collector
instance and stamps the record ``region`` with the ``global`` marker.
"""

from __future__ import annotations

import boto3

from aws_lifecycle_inventory.models import ResourceVersionRecord
from aws_lifecycle_inventory.orchestration import CollectorStatus

GLOBAL_REGION_MARKER = "global"


class Route53Collector:
    name = "route53-hosted-zones"
    resource_type = "AWS::Route53::HostedZone"

    def __init__(self) -> None:
        # Emit global resources only once across a multi-region scan that reuses
        # this instance.
        self._emitted = False

    def collect(
        self, session: boto3.Session, account_id: str, region: str
    ) -> tuple[list[ResourceVersionRecord], CollectorStatus]:
        if self._emitted:
            # Already emitted for this scan; report an empty, successful pass so a
            # second region does not duplicate zones.
            return [], CollectorStatus(name=self.name, ok=True, record_count=0)

        client = session.client("route53")
        records: list[ResourceVersionRecord] = []
        for page in client.get_paginator("list_hosted_zones").paginate():
            for zone in page.get("HostedZones", []):
                # Zone Id looks like "/hostedzone/Z123"; keep the bare id.
                zone_id = zone["Id"].rsplit("/", 1)[-1]
                records.append(
                    ResourceVersionRecord(
                        account_id=account_id,
                        region=GLOBAL_REGION_MARKER,
                        resource_type=self.resource_type,
                        resource_id=zone_id,
                        resource_arn=f"arn:aws:route53:::hostedzone/{zone_id}",
                    )
                )
        self._emitted = True
        return records, CollectorStatus(name=self.name, ok=True, record_count=len(records))
