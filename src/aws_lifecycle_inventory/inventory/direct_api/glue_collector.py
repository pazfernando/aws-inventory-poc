"""AWS Glue Jobs version collector."""

from __future__ import annotations

import boto3

from aws_lifecycle_inventory.models import ResourceVersionRecord
from aws_lifecycle_inventory.orchestration import CollectorStatus


class GlueJobsCollector:
    name = "glue"
    resource_type = "AWS::Glue::Job"

    def collect(
        self, session: boto3.Session, account_id: str, region: str
    ) -> tuple[list[ResourceVersionRecord], CollectorStatus]:
        client = session.client("glue", region_name=region)
        records: list[ResourceVersionRecord] = []

        for page in client.get_paginator("get_jobs").paginate():
            for job in page.get("Jobs", []):
                name = job.get("Name", "")
                records.append(
                    ResourceVersionRecord(
                        account_id=account_id,
                        region=region,
                        resource_type=self.resource_type,
                        resource_id=name,
                        resource_arn=(
                            f"arn:aws:glue:{region}:{account_id}:job/{name}"
                            if name
                            else ""
                        ),
                        software_type="glue-version",
                        software_name="glue",
                        version=job.get("GlueVersion", "") or "",
                    )
                )

        return records, CollectorStatus(name=self.name, ok=True, record_count=len(records))
