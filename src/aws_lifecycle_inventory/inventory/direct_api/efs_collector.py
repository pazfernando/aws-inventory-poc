"""EFS file system presence collector (non-version-bearing)."""

from __future__ import annotations

import boto3

from aws_lifecycle_inventory.models import ResourceVersionRecord
from aws_lifecycle_inventory.orchestration import CollectorStatus


class EFSCollector:
    name = "efs-filesystems"
    resource_type = "AWS::EFS::FileSystem"

    def collect(
        self, session: boto3.Session, account_id: str, region: str
    ) -> tuple[list[ResourceVersionRecord], CollectorStatus]:
        client = session.client("efs", region_name=region)
        records: list[ResourceVersionRecord] = []
        for page in client.get_paginator("describe_file_systems").paginate():
            for fs in page.get("FileSystems", []):
                fs_id = fs["FileSystemId"]
                records.append(
                    ResourceVersionRecord(
                        account_id=account_id,
                        region=region,
                        resource_type=self.resource_type,
                        resource_id=fs_id,
                        resource_arn=fs.get("FileSystemArn", "")
                        or f"arn:aws:elasticfilesystem:{region}:{account_id}:file-system/{fs_id}",
                    )
                )
        return records, CollectorStatus(name=self.name, ok=True, record_count=len(records))
