"""Amazon OpenSearch Service engine/version collector."""

from __future__ import annotations

import boto3

from aws_lifecycle_inventory.models import ResourceVersionRecord
from aws_lifecycle_inventory.orchestration import CollectorStatus


def _split_engine_version(engine_version: str) -> tuple[str, str]:
    """Split ``OpenSearch_2.13`` / ``Elasticsearch_7.10`` into (name, version).

    If no underscore/version is present, keep the whole string as the name and
    leave the version empty rather than inventing one.
    """
    if not engine_version:
        return "", ""
    if "_" in engine_version:
        name, _, version = engine_version.partition("_")
        return name.lower(), version
    return engine_version.lower(), ""


class OpenSearchCollector:
    name = "opensearch"
    resource_type = "AWS::OpenSearchService::Domain"

    def collect(
        self, session: boto3.Session, account_id: str, region: str
    ) -> tuple[list[ResourceVersionRecord], CollectorStatus]:
        client = session.client("opensearch", region_name=region)
        records: list[ResourceVersionRecord] = []

        domain_names = [
            d["DomainName"]
            for d in client.list_domain_names().get("DomainNames", [])
            if d.get("DomainName")
        ]
        if not domain_names:
            return records, CollectorStatus(name=self.name, ok=True, record_count=0)

        described = client.describe_domains(DomainNames=domain_names).get(
            "DomainStatusList", []
        )
        for domain in described:
            software_name, version = _split_engine_version(
                domain.get("EngineVersion", "") or ""
            )
            records.append(
                ResourceVersionRecord(
                    account_id=account_id,
                    region=region,
                    resource_type=self.resource_type,
                    resource_id=domain.get("DomainName", ""),
                    resource_arn=domain.get("ARN", ""),
                    software_type="search-engine",
                    software_name=software_name,
                    version=version,
                )
            )

        return records, CollectorStatus(name=self.name, ok=True, record_count=len(records))
