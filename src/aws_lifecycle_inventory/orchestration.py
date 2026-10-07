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


@dataclass
class ScanResult:
    records: list[ResourceVersionRecord] = field(default_factory=list)
    collector_statuses: list[CollectorStatus] = field(default_factory=list)


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


def run_scan(
    collectors: list[Collector],
    session: boto3.Session,
    region: str,
    account_id: str | None = None,
) -> ScanResult:
    """Run all collectors against one account/region and aggregate the result."""
    if account_id is None:
        account_id = _resolve_account_id(session)

    result = ScanResult()
    for collector in collectors:
        try:
            records, status = collector.collect(session, account_id, region)
        except Exception as exc:  # backstop: never abort the scan
            result.collector_statuses.append(
                CollectorStatus(
                    name=getattr(collector, "name", collector.__class__.__name__),
                    ok=False,
                    error_code=type(exc).__name__,
                    error_message=str(exc),
                )
            )
            continue
        result.records.extend(records)
        result.collector_statuses.append(status)
    return result
