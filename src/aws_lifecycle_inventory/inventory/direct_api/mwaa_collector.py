"""Amazon MWAA (Managed Workflows for Apache Airflow) version collector."""

from __future__ import annotations

import boto3

from aws_lifecycle_inventory.models import ResourceVersionRecord
from aws_lifecycle_inventory.orchestration import CollectorStatus


class MWAACollector:
    name = "mwaa"
    resource_type = "AWS::MWAA::Environment"

    def collect(
        self, session: boto3.Session, account_id: str, region: str
    ) -> tuple[list[ResourceVersionRecord], CollectorStatus]:
        client = session.client("mwaa", region_name=region)
        records: list[ResourceVersionRecord] = []

        for page in client.get_paginator("list_environments").paginate():
            for env_name in page.get("Environments", []):
                env = client.get_environment(Name=env_name).get("Environment", {})
                records.append(
                    ResourceVersionRecord(
                        account_id=account_id,
                        region=region,
                        resource_type=self.resource_type,
                        resource_id=env.get("Name", env_name),
                        resource_arn=env.get("Arn", ""),
                        software_type="airflow-version",
                        software_name="airflow",
                        version=env.get("AirflowVersion", "") or "",
                    )
                )

        return records, CollectorStatus(name=self.name, ok=True, record_count=len(records))
