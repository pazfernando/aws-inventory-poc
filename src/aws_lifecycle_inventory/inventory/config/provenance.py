"""Provenance reconciliation across inventory sources.

When the same resource (by ARN, else account/region/type/id) is reported by more
than one source (e.g. DIRECT_API and AWS_CONFIG), we MUST preserve every source's
observation and surface disagreements instead of silently overwriting one value
with another.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from aws_lifecycle_inventory.models import ResourceVersionRecord


def resource_key(record: ResourceVersionRecord) -> str:
    """Stable identity for a resource across sources."""
    if record.resource_arn:
        return record.resource_arn
    return "|".join(
        (record.account_id, record.region, record.resource_type, record.resource_id)
    )


@dataclass
class ReconciledResource:
    key: str
    observations: list[ResourceVersionRecord] = field(default_factory=list)

    @property
    def sources(self) -> set[str]:
        return {o.inventory_source for o in self.observations}

    @property
    def versions(self) -> set[str]:
        return {o.version for o in self.observations}

    @property
    def has_conflict(self) -> bool:
        """True when sources disagree on a non-empty version."""
        non_empty = {v for v in self.versions if v}
        return len(non_empty) > 1


def reconcile(
    records: list[ResourceVersionRecord],
) -> dict[str, ReconciledResource]:
    """Group records by resource identity, preserving every observation."""
    grouped: dict[str, ReconciledResource] = {}
    buckets: dict[str, list[ResourceVersionRecord]] = defaultdict(list)
    for record in records:
        buckets[resource_key(record)].append(record)
    for key, observations in buckets.items():
        grouped[key] = ReconciledResource(key=key, observations=observations)
    return grouped


def conflicts(
    records: list[ResourceVersionRecord],
) -> list[ReconciledResource]:
    """Return only the resources whose sources disagree on a version."""
    return [r for r in reconcile(records).values() if r.has_conflict]
