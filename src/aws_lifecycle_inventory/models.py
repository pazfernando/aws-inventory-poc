"""Normalized record model shared by every inventory source and lifecycle provider."""

from __future__ import annotations

from datetime import date, datetime, timezone

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ResourceVersionRecord(BaseModel):
    """One normalized, version-bearing resource observation.

    This is the single record model reused by the CLI, CSV output, and later
    sources (AWS Config, AWS Health, SSM, Lambda). Baseline fields plus lifecycle
    fields (Change 04); operational and security fields are added by their owning
    OpenSpec changes.
    """

    account_id: str
    region: str
    resource_type: str
    resource_id: str
    resource_arn: str = ""
    software_type: str = ""
    software_name: str = ""
    # Version stays an explicit empty string when the AWS API exposes none.
    # Collectors MUST NOT invent or infer a version.
    version: str = ""
    inventory_source: str = "DIRECT_API"
    collected_at: datetime = Field(default_factory=_utcnow)

    # --- Lifecycle fields (Change 04) ---
    # UNKNOWN by default: absence of evidence is never SUPPORTED, and UNKNOWN must
    # stay distinguishable from SUPPORTED.
    lifecycle_status: str = "UNKNOWN"
    eol_date: date | None = None
    days_to_eol: int | None = None
    lifecycle_source: str = ""
    lifecycle_evidence_id: str = ""
    evaluated_at: datetime | None = None
    # Provenance of other sources that also matched this resource (preserved so a
    # lower-precedence source is never silently discarded). Not a CSV column.
    lifecycle_other_sources: list[dict] = Field(default_factory=list)

    # --- Operational coverage fields (Change 08) ---
    # Machine-visible coverage status; empty for sources without coverage
    # semantics. Coverage gaps (e.g. EC2 instances not managed by SSM) carry an
    # explicit gap code here instead of fabricated software.
    coverage_status: str = ""

    # --- Usage assessment fields (add-resource-usage-metrics) ---
    # Populated by the opt-in usage assessment service. Empty when a record has
    # not been through usage assessment (distinct from an assessed IDLE/NO_METRIC
    # result). usage_status is one of IN_USE / IDLE / NO_DATA / NO_METRIC.
    usage_status: str = ""
    usage_metric: str = ""
    # Activity value backing the status (e.g. invocation/connection count in the
    # window). None when unassessed or no metric; distinct from an explicit 0.
    usage_value: float | None = None
    usage_window_days: int | None = None
    usage_source: str = ""
    usage_assessed_at: datetime | None = None
