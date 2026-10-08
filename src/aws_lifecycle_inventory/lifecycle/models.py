"""Lifecycle status set and evidence model (Change 04).

Lifecycle semantics are kept independent of inventory: collectors and Config
queries never own deprecation policy. A conclusion is only non-UNKNOWN when a
provider supplies evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class LifecycleStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    EOL_365 = "EOL_365"
    EOL_180 = "EOL_180"
    EOL_90 = "EOL_90"
    EOL_30 = "EOL_30"
    EOL = "EOL"
    UNSUPPORTED = "UNSUPPORTED"
    UNKNOWN = "UNKNOWN"
    # A resource type that carries no software version to evaluate. Distinct from
    # UNKNOWN (absence of evidence) and SUPPORTED. Assigned without consulting any
    # provider.
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass
class LifecycleEvidence:
    """Evidence backing a non-UNKNOWN lifecycle conclusion.

    ``status`` may be left None when the provider supplies only an EOL date and
    lets the evaluator derive the bucket. ``evidence_id`` identifies the specific
    piece of evidence (e.g. a curated entry id or a Health event id). ``details``
    holds source-specific provenance fields (e.g. AWS Health event type, affected
    entity, affected-resource status) without bloating the core schema.
    """

    source: str
    evidence_id: str
    eol_date: date | None = None
    status: LifecycleStatus | None = None
    details: dict = field(default_factory=dict)
