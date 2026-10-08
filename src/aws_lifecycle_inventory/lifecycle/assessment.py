"""Lifecycle assessment service — reusable, flow-independent.

This is the stable facade for lifecycle evaluation. It takes normalized records
from any source (a scan, a loaded CSV, anything) and returns them annotated with
lifecycle fields, owning provider construction so callers do not assemble
providers themselves.

It is deliberately independent of the scan flow: it requires no scan, account, or
region context. A flow composes discovery and assessment as separate steps.
Evaluation semantics live in ``evaluator``; this module only wires records to
providers.
"""

from __future__ import annotations

from datetime import date

import boto3

from aws_lifecycle_inventory.lifecycle.evaluator import LifecycleProvider, evaluate_all
from aws_lifecycle_inventory.lifecycle.providers import default_lifecycle_providers
from aws_lifecycle_inventory.models import ResourceVersionRecord


def assess_records(
    records: list[ResourceVersionRecord],
    *,
    session: boto3.Session | None = None,
    providers: list[LifecycleProvider] | None = None,
    today: date | None = None,
    health_region: str = "us-east-1",
) -> list[ResourceVersionRecord]:
    """Annotate records with lifecycle fields using the default (or given) providers.

    Args:
        records: Normalized records from any source. Not required to come from a
            scan.
        session: Optional boto3 session used to build the AWS Health provider. When
            ``None``, AWS Health is skipped (non-fatal) and EndOfLife still runs.
            Ignored when ``providers`` is given (explicit wins).
        providers: Optional explicit ordered provider list. When given, it is used
            verbatim and ``session``/``health_region`` are ignored.
        today: Optional reference date for EOL math (defaults to today, UTC).
        health_region: Region for the AWS Health provider when building defaults.

    Returns:
        The records annotated with lifecycle fields, per the evaluator's semantics
        (precedence AWS Health then EndOfLife; UNKNOWN distinct from SUPPORTED;
        NOT_APPLICABLE for non-version-bearing resources).
    """
    if providers is None:
        providers = default_lifecycle_providers(session, health_region)
    return evaluate_all(records, providers, today=today)
