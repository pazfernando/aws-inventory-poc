"""AWS Config inventory source (Change 03 evaluation spike).

This module is an OPTIONAL, measured candidate source. It MUST NOT be required by
the baseline CLI. It detects Config availability, probes configuration data, and
normalizes results into the shared ResourceVersionRecord with
``inventory_source=AWS_CONFIG``. Where the AWS API exposes no version, the version
stays explicitly empty (no invented versions).
"""

from __future__ import annotations

from dataclasses import dataclass

import boto3

from aws_lifecycle_inventory.models import ResourceVersionRecord
from aws_lifecycle_inventory.orchestration import CollectorStatus

INVENTORY_SOURCE = "AWS_CONFIG"

# Advanced Query expressions per baseline resource type. The version field each
# Config configuration item exposes varies; these select the identity plus the
# configuration blob we normalize from.
_BASELINE_RESOURCE_TYPES: tuple[str, ...] = (
    "AWS::Lambda::Function",
    "AWS::RDS::DBInstance",
    "AWS::RDS::DBCluster",
    "AWS::ElastiCache::CacheCluster",
    "AWS::EKS::Cluster",
)


@dataclass
class ConfigAvailability:
    available: bool
    reason: str = ""


def detect_availability(session: boto3.Session, region: str) -> ConfigAvailability:
    """Determine whether AWS Config is enabled and usable in this account/region.

    Returns an explicit unavailable status rather than raising, so the baseline
    inventory can proceed when Config is not configured.
    """
    try:
        client = session.client("config", region_name=region)
        status = client.describe_configuration_recorder_status()
    except Exception as exc:  # access denied, service not available, etc.
        return ConfigAvailability(available=False, reason=f"{type(exc).__name__}: {exc}")

    recorders = status.get("ConfigurationRecordersStatus", [])
    if not recorders:
        return ConfigAvailability(
            available=False, reason="no configuration recorder in this account/region"
        )
    if any(r.get("recording") for r in recorders):
        return ConfigAvailability(available=True)
    return ConfigAvailability(available=False, reason="recorder present but not recording")


def _version_from_config_item(resource_type: str, item: dict) -> tuple[str, str, str]:
    """Return (software_type, software_name, version) from a Config item.

    Config exposes the resource configuration under a provider-specific shape.
    We read only fields the API exposes; anything absent stays empty.
    """
    cfg = item.get("configuration") or {}
    if resource_type == "AWS::Lambda::Function":
        runtime = cfg.get("runtime", "") or ""
        # reuse the same split logic as the direct-API collector
        from aws_lifecycle_inventory.inventory.direct_api._common import (
            split_lambda_runtime,
        )

        name, version = split_lambda_runtime(runtime)
        return "runtime", name, version
    if resource_type in ("AWS::RDS::DBInstance", "AWS::RDS::DBCluster"):
        return "db-engine", cfg.get("engine", "") or "", cfg.get("engineVersion", "") or ""
    if resource_type == "AWS::ElastiCache::CacheCluster":
        return "cache-engine", cfg.get("engine", "") or "", cfg.get("engineVersion", "") or ""
    if resource_type == "AWS::EKS::Cluster":
        return "orchestrator", "kubernetes", cfg.get("version", "") or ""
    return "", "", ""


def collect_from_config(
    session: boto3.Session, account_id: str, region: str
) -> tuple[list[ResourceVersionRecord], CollectorStatus]:
    """Probe AWS Config for baseline resource types and normalize the results.

    Uses Advanced Queries (``select_resource_config``). Returns an empty result
    with an explicit status when Config is unavailable; never raises to the caller.
    """
    availability = detect_availability(session, region)
    if not availability.available:
        return [], CollectorStatus(
            name="aws_config",
            ok=False,
            error_code="CONFIG_UNAVAILABLE",
            error_message=availability.reason,
        )

    client = session.client("config", region_name=region)
    records: list[ResourceVersionRecord] = []

    for resource_type in _BASELINE_RESOURCE_TYPES:
        expression = (
            "SELECT resourceId, resourceName, arn, configuration "
            f"WHERE resourceType = '{resource_type}'"
        )
        next_token = ""
        while True:
            kwargs = {"Expression": expression}
            if next_token:
                kwargs["NextToken"] = next_token
            page = client.select_resource_config(**kwargs)
            for raw in page.get("Results", []):
                item = raw if isinstance(raw, dict) else _safe_json(raw)
                if item is None:
                    continue
                software_type, software_name, version = _version_from_config_item(
                    resource_type, item
                )
                records.append(
                    ResourceVersionRecord(
                        account_id=account_id,
                        region=region,
                        resource_type=resource_type,
                        resource_id=item.get("resourceId", "")
                        or item.get("resourceName", ""),
                        resource_arn=item.get("arn", ""),
                        software_type=software_type,
                        software_name=software_name,
                        version=version,
                        inventory_source=INVENTORY_SOURCE,
                    )
                )
            next_token = page.get("NextToken", "")
            if not next_token:
                break

    return records, CollectorStatus(
        name="aws_config", ok=True, record_count=len(records)
    )


def _safe_json(raw: str) -> dict | None:
    import json

    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return None
