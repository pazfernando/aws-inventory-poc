"""Lifecycle evaluator and provider abstraction (Change 04, extended in Change 05).

The evaluator runs a record through ordered providers. Ordering expresses
precedence: the first provider that returns evidence supplies the conclusion
(e.g. AWS Health before curated). Evidence from other matching providers is
preserved as provenance, never discarded. When no provider matches, the record
stays ``UNKNOWN`` — never silently ``SUPPORTED``.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Protocol

from aws_lifecycle_inventory.inventory.resource_kinds import (
    NON_VERSION_BEARING_RESOURCE_TYPES,
)
from aws_lifecycle_inventory.lifecycle.models import LifecycleEvidence, LifecycleStatus
from aws_lifecycle_inventory.models import ResourceVersionRecord


class LifecycleProvider(Protocol):
    source: str

    def match(self, record: ResourceVersionRecord) -> LifecycleEvidence | None:
        ...


def _bucket_for_days(days_to_eol: int) -> LifecycleStatus:
    """Map days-until-EOL into a lifecycle bucket.

    Past EOL -> EOL. Otherwise the nearest upcoming window. A version with more
    than 365 days of runway is SUPPORTED.
    """
    if days_to_eol < 0:
        return LifecycleStatus.EOL
    if days_to_eol <= 30:
        return LifecycleStatus.EOL_30
    if days_to_eol <= 90:
        return LifecycleStatus.EOL_90
    if days_to_eol <= 180:
        return LifecycleStatus.EOL_180
    if days_to_eol <= 365:
        return LifecycleStatus.EOL_365
    return LifecycleStatus.SUPPORTED


def _resolve_status(
    evidence: LifecycleEvidence, today: date
) -> tuple[LifecycleStatus, int | None]:
    """Return (status, days_to_eol) from evidence.

    An explicit status on the evidence is authoritative. Otherwise derive from
    the EOL date. With neither, fall back to SUPPORTED (the provider matched and
    asserted applicability but gave no EOL — treated as currently supported).
    """
    days_to_eol: int | None = None
    if evidence.eol_date is not None:
        days_to_eol = (evidence.eol_date - today).days

    if evidence.status is not None:
        return evidence.status, days_to_eol
    if days_to_eol is not None:
        return _bucket_for_days(days_to_eol), days_to_eol
    return LifecycleStatus.SUPPORTED, None


def evaluate_record(
    record: ResourceVersionRecord,
    providers: list[LifecycleProvider],
    today: date | None = None,
) -> ResourceVersionRecord:
    """Evaluate one record, returning a copy annotated with lifecycle fields.

    Providers are consulted in order. The first provider that returns evidence
    supplies the conclusion (so ordering expresses precedence, e.g. AWS Health
    before curated). Evidence from every other matching provider is preserved as
    provenance and never silently discarded.
    """
    today = today or datetime.now(timezone.utc).date()
    now = datetime.now(timezone.utc)

    # Non-version-bearing resources have no version to evaluate: assign
    # NOT_APPLICABLE without consulting any provider. This stays distinct from
    # UNKNOWN (absence of evidence) and SUPPORTED.
    if record.resource_type in NON_VERSION_BEARING_RESOURCE_TYPES:
        return record.model_copy(
            update={
                "lifecycle_status": LifecycleStatus.NOT_APPLICABLE.value,
                "evaluated_at": now,
            }
        )

    matches: list[LifecycleEvidence] = []
    for provider in providers:
        evidence = provider.match(record)
        if evidence is not None:
            matches.append(evidence)

    if not matches:
        # No provider matched -> UNKNOWN, with a timestamp but no evidence.
        return record.model_copy(
            update={
                "lifecycle_status": LifecycleStatus.UNKNOWN.value,
                "evaluated_at": now,
            }
        )

    primary = matches[0]
    status, days_to_eol = _resolve_status(primary, today)
    # Preserve provenance of every other matching source without overwriting.
    other_provenance = [
        {"source": e.source, "evidence_id": e.evidence_id}
        for e in matches[1:]
    ]
    return record.model_copy(
        update={
            "lifecycle_status": status.value,
            "eol_date": primary.eol_date,
            "days_to_eol": days_to_eol,
            "lifecycle_source": primary.source,
            "lifecycle_evidence_id": primary.evidence_id,
            "evaluated_at": now,
            "lifecycle_other_sources": other_provenance,
        }
    )


def evaluate_all(
    records: list[ResourceVersionRecord],
    providers: list[LifecycleProvider],
    today: date | None = None,
) -> list[ResourceVersionRecord]:
    return [evaluate_record(r, providers, today=today) for r in records]
