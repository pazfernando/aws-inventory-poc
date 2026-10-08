"""SSM-managed node software inventory (Change 08).

Cross-references EC2 instances with SSM-managed instances and SSM Inventory to
normalize a bounded guest-software subset (OS platform/version, plus an opt-in
application package subset) into the shared record model. Unmanaged instances
and managed instances without inventory become explicit coverage gaps — guest
software is never invented.
"""

from __future__ import annotations

from typing import Protocol

import boto3

from aws_lifecycle_inventory.models import ResourceVersionRecord
from aws_lifecycle_inventory.orchestration import CollectorStatus

# Coverage-status codes (machine-visible via the record's coverage_status field).
COVERAGE_OK = "OK"
COVERAGE_UNMANAGED = "SSM_UNMANAGED"
COVERAGE_NO_INVENTORY = "SSM_NO_INVENTORY"


class _SsmClient(Protocol):  # pragma: no cover - typing only
    def get_paginator(self, operation_name: str): ...


class SsmNodeCollector:
    """Inventory guest software on EC2 instances via SSM."""

    name = "ssm-managed-nodes"
    source = "SSM_INVENTORY"
    resource_type = "AWS::EC2::Instance"

    def __init__(self, include_applications: bool = False) -> None:
        # Bounded subset: OS always; application packages opt-in so large guest
        # package lists cannot bloat the output by default.
        self._include_applications = include_applications

    def collect(
        self, session: boto3.Session, account_id: str, region: str
    ) -> tuple[list[ResourceVersionRecord], CollectorStatus]:
        ssm = session.client("ssm", region_name=region)
        ec2 = session.client("ec2", region_name=region)

        managed = self._managed_instances(ssm)
        ec2_instance_ids = self._ec2_instance_ids(ec2)

        records: list[ResourceVersionRecord] = []
        for instance_id in ec2_instance_ids:
            info = managed.get(instance_id)
            if info is None:
                records.append(
                    self._gap_record(account_id, region, instance_id, COVERAGE_UNMANAGED)
                )
                continue
            records.extend(self._instance_records(ssm, account_id, region, info))

        return records, CollectorStatus(
            name=self.name, ok=True, record_count=len(records)
        )

    # --- helpers ------------------------------------------------------------

    @staticmethod
    def _managed_instances(ssm: _SsmClient) -> dict[str, dict]:
        """InstanceId -> InstanceInformation entry for every SSM-managed node."""
        managed: dict[str, dict] = {}
        for page in ssm.get_paginator("describe_instance_information").paginate():
            for info in page.get("InstanceInformationList", []):
                managed[info["InstanceId"]] = info
        return managed

    @staticmethod
    def _ec2_instance_ids(ec2) -> list[str]:
        ids: list[str] = []
        for page in ec2.get_paginator("describe_instances").paginate():
            for reservation in page.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    if instance.get("State", {}).get("Name") != "terminated":
                        ids.append(instance["InstanceId"])
        return ids

    def _instance_records(
        self, ssm: _SsmClient, account_id: str, region: str, info: dict
    ) -> list[ResourceVersionRecord]:
        """Normalize one managed instance: OS record, optional package records.

        Managed-but-silent instances (no OS platform reported by SSM) are
        coverage gaps with a reason, distinct from unmanaged instances.
        """
        instance_id = info["InstanceId"]
        platform_name = info.get("PlatformName") or ""
        platform_version = info.get("PlatformVersion") or ""
        if not platform_name and not platform_version:
            return [
                self._gap_record(
                    account_id, region, instance_id, COVERAGE_NO_INVENTORY
                )
            ]

        records = [
            ResourceVersionRecord(
                account_id=account_id,
                region=region,
                resource_type=self.resource_type,
                resource_id=instance_id,
                software_type="os",
                software_name=platform_name,
                version=platform_version,
                inventory_source=self.source,
                coverage_status=COVERAGE_OK,
            )
        ]
        if self._include_applications:
            records.extend(
                self._application_records(ssm, account_id, region, instance_id)
            )
        return records

    def _application_records(
        self, ssm: _SsmClient, account_id: str, region: str, instance_id: str
    ) -> list[ResourceVersionRecord]:
        """Best-effort application package subset for one managed instance.

        Failures here never discard the instance's OS record (the OS record is
        the primary guest signal); a failed package query just contributes no
        package records — it MUST NOT invent any.
        """
        try:
            pages = ssm.get_paginator("get_inventory").paginate(
                Filters=[
                    {
                        "Key": "AWS:InstanceInformation.InstanceId",
                        "Values": [instance_id],
                    }
                ],
                ResultAttributes=[
                    {"TypeName": "AWS:Application", "Properties": ["Name", "Version"]}
                ],
            )
        except Exception:
            return []
        records: list[ResourceVersionRecord] = []
        for page in pages:
            for entity in page.get("Entities", []):
                content = (
                    entity.get("Data", {})
                    .get("AWS:Application", {})
                    .get("Content", [])
                )
                for entry in content:
                    name = entry.get("Name") or ""
                    version = entry.get("Version") or ""
                    if not name:
                        continue
                    records.append(
                        ResourceVersionRecord(
                            account_id=account_id,
                            region=region,
                            resource_type=self.resource_type,
                            resource_id=instance_id,
                            software_type="application",
                            software_name=name,
                            version=version,
                            inventory_source=self.source,
                            coverage_status=COVERAGE_OK,
                        )
                    )
        return records

    def _gap_record(
        self, account_id: str, region: str, instance_id: str, coverage: str
    ) -> ResourceVersionRecord:
        """A visible, machine-readable coverage gap with no fabricated software."""
        return ResourceVersionRecord(
            account_id=account_id,
            region=region,
            resource_type=self.resource_type,
            resource_id=instance_id,
            inventory_source=self.source,
            coverage_status=coverage,
        )
