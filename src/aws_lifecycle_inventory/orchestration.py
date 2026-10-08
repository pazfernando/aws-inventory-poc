"""Scan engine shared by the CLI and (later) the Lambda handler.

Collectors are isolated: each returns its own records plus a status. A failure in
one collector never aborts the whole scan; the engine wraps each call as a
backstop and surfaces the failure as collector status.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import boto3

from aws_lifecycle_inventory.account_access import (
    AccountAccessStatus,
    resolve_account_session,
)
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
    # Account provenance of this status; set by organization-wide scans.
    account: str | None = None
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


# Change 03's measured decision (src/aws_lifecycle_inventory/inventory/config/
# EVALUATION_REPORT.md): direct APIs stay primary; Config is reserved for
# org-scale aggregation and was re-evaluated in Change 07, which applies this
# recorded conclusion instead of re-litigating it.
ORG_SOURCE_STRATEGY = "DIRECT_API_PRIMARY"


@dataclass
class OrgScanResult:
    """Combined result of a scan across accounts x regions of an organization."""

    regions: list[str] = field(default_factory=list)
    accounts: list[str] = field(default_factory=list)
    records: list[ResourceVersionRecord] = field(default_factory=list)
    account_statuses: list[AccountAccessStatus] = field(default_factory=list)
    collector_statuses: list[CollectorStatus] = field(default_factory=list)

    def execution_summary(self) -> dict:
        """Structured status breakdown by account -> (access, regions -> source -> collector).

        Inaccessible accounts appear with ``access.ok == False`` and no regions.
        """
        summary: dict = {}
        for status in self.account_statuses:
            summary.setdefault(
                status.account_id,
                {
                    "access": {
                        "ok": status.ok,
                        "error_code": status.error_code,
                    },
                    "regions": {},
                },
            )
        for status in self.collector_statuses:
            account = summary.setdefault(
                status.account or "",
                {"access": {"ok": True, "error_code": ""}, "regions": {}},
            )
            per_collector = (
                account["regions"]
                .setdefault(status.region or "", {})
                .setdefault(status.source, {})
            )
            per_collector[status.name] = {
                "ok": status.ok,
                "record_count": status.record_count,
                "error_code": status.error_code,
            }
        return summary


def run_org_scan(
    collectors: list[Collector],
    session: boto3.Session,
    regions: list[str],
    accounts: list[str],
    role_name: str,
    external_id: str | None = None,
) -> OrgScanResult:
    """Scan every target account x region via cross-account direct-API fan-out.

    Applies the Change 03 decision (``ORG_SOURCE_STRATEGY``): org-wide inventory
    is gathered by assuming a read-only role per account and running the shared
    multi-region engine (Change 06) with that session. Accounts are isolated:
    an un-assumable role is reported, never an abort.
    """
    if ORG_SOURCE_STRATEGY != "DIRECT_API_PRIMARY":
        raise NotImplementedError(
            "Only the DIRECT_API_PRIMARY strategy is implemented "
            f"(recorded decision: {ORG_SOURCE_STRATEGY})"
        )

    result = OrgScanResult(regions=list(regions), accounts=list(accounts))
    for account_id in accounts:
        account_session, access = resolve_account_session(
            session, account_id, role_name, external_id=external_id
        )
        if account_session is None:
            result.account_statuses.append(access)
            continue

        region_result = run_scan_multi_region(
            collectors, account_session, regions, account_id=account_id
        )
        for status in region_result.collector_statuses:
            status.account = account_id
        result.records.extend(region_result.records)
        result.collector_statuses.extend(region_result.collector_statuses)
        access.record_count = len(region_result.records)
        result.account_statuses.append(access)
    return result


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
