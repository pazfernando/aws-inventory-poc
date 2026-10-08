"""Scan engine shared by the CLI and (later) the Lambda handler.

Collectors are isolated: each returns its own records plus a status. A failure in
one collector never aborts the whole scan; the engine wraps each call as a
backstop and surfaces the failure as collector status.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import boto3

from aws_lifecycle_inventory.models import ResourceVersionRecord


@dataclass
class CollectorStatus:
    name: str
    ok: bool
    record_count: int = 0
    error_code: str = ""
    error_message: str = ""
    # Region provenance of this status. ``None`` for single-region scans;
    # multi-region scans always set it.
    region: str | None = None
    # Inventory source the collector belongs to (e.g. DIRECT_API). Collectors may
    # declare their own ``source``; the engine defaults to DIRECT_API.
    source: str = "DIRECT_API"


@dataclass
class ScanResult:
    records: list[ResourceVersionRecord] = field(default_factory=list)
    collector_statuses: list[CollectorStatus] = field(default_factory=list)


@dataclass
class MultiRegionScanResult:
    """Combined result of a scan across one or more regions of one account."""

    account_id: str
    regions: list[str] = field(default_factory=list)
    records: list[ResourceVersionRecord] = field(default_factory=list)
    collector_statuses: list[CollectorStatus] = field(default_factory=list)

    def execution_summary(self) -> dict:
        """Structured status breakdown by region -> source -> collector.

        Machine-readable (Change 09's Lambda emits it alongside the CSV). Each
        collector entry reports ok/record_count/error_code at its breakdown
        level.
        """
        summary: dict = {}
        for status in self.collector_statuses:
            region = status.region or ""
            per_collector = (
                summary.setdefault(region, {})
                .setdefault(status.source, {})
            )
            per_collector[status.name] = {
                "ok": status.ok,
                "record_count": status.record_count,
                "error_code": status.error_code,
            }
        return summary


class Collector(Protocol):
    """A per-service, read-only collector.

    ``collect`` returns ``(records, status)``. Implementations should catch their
    own expected errors and report them via the returned status, but the engine
    also guards against unexpected exceptions.
    """

    name: str

    def collect(
        self, session: boto3.Session, account_id: str, region: str
    ) -> tuple[list[ResourceVersionRecord], CollectorStatus]:
        ...


def _resolve_account_id(session: boto3.Session) -> str:
    return session.client("sts").get_caller_identity()["Account"]


def _collect_in_region(
    collectors: list[Collector],
    session: boto3.Session,
    account_id: str,
    region: str,
) -> tuple[list[ResourceVersionRecord], list[CollectorStatus]]:
    """Run every collector against one account/region, isolating failures."""
    records: list[ResourceVersionRecord] = []
    statuses: list[CollectorStatus] = []
    for collector in collectors:
        name = getattr(collector, "name", collector.__class__.__name__)
        try:
            region_records, status = collector.collect(session, account_id, region)
        except Exception as exc:  # backstop: never abort the scan
            statuses.append(
                CollectorStatus(
                    name=name,
                    ok=False,
                    error_code=type(exc).__name__,
                    error_message=str(exc),
                    region=region,
                    source=getattr(collector, "source", "DIRECT_API"),
                )
            )
            continue
        status.region = region
        status.source = getattr(collector, "source", "DIRECT_API")
        statuses.append(status)
        records.extend(region_records)
    return records, statuses


def run_scan(
    collectors: list[Collector],
    session: boto3.Session,
    region: str,
    account_id: str | None = None,
) -> ScanResult:
    """Run all collectors against one account/region and aggregate the result."""
    if account_id is None:
        account_id = _resolve_account_id(session)

    records, statuses = _collect_in_region(collectors, session, account_id, region)
    return ScanResult(records=records, collector_statuses=statuses)


def run_scan_multi_region(
    collectors: list[Collector],
    session: boto3.Session,
    regions: list[str],
    account_id: str | None = None,
) -> MultiRegionScanResult:
    """Run all collectors across the given regions, combining the results.

    Regions are scanned sequentially with per-region service clients; a failure
    in one region or collector never aborts the rest.
    """
    if account_id is None:
        account_id = _resolve_account_id(session)

    result = MultiRegionScanResult(account_id=account_id, regions=list(regions))
    for region in regions:
        records, statuses = _collect_in_region(collectors, session, account_id, region)
        result.records.extend(records)
        result.collector_statuses.extend(statuses)
    return result
