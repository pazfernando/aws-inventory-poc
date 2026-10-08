"""Reusable, flow-independent usage assessment service.

Takes normalized records from any source and annotates each with a usage signal
(IN_USE / IDLE / NO_DATA / NO_METRIC) plus the supporting activity value, derived
from read-only CloudWatch metrics over a configurable window (default 30 days).

It is independent of discovery: it requires no scan, only a boto3 session for
CloudWatch. A run composes it as a separate step after discovery (and optional
lifecycle assessment). Partial failures are isolated per record; a failed query
yields NO_DATA rather than a fabricated value. Read-only.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import boto3

from aws_lifecycle_inventory.models import ResourceVersionRecord
from aws_lifecycle_inventory.usage.models import UsageStatus
from aws_lifecycle_inventory.usage.registry import MetricSpec, metric_spec_for

DEFAULT_WINDOW_DAYS = 30


def assess_usage(
    records: list[ResourceVersionRecord],
    *,
    session: boto3.Session,
    window_days: int = DEFAULT_WINDOW_DAYS,
    today: date | None = None,
) -> list[ResourceVersionRecord]:
    """Annotate records with a usage signal from CloudWatch over the window.

    Args:
        records: Normalized records from any source (scan, loaded CSV, etc.).
        session: boto3 session used for read-only CloudWatch queries.
        window_days: Observation window in days (default 30).
        today: Optional reference date (defaults to now, UTC).

    Returns:
        Records annotated with usage fields. Records whose resource type has no
        usage metric are NO_METRIC (no CloudWatch call). Query failures yield
        NO_DATA; other resources are still assessed.
    """
    now = datetime.now(timezone.utc)
    end = (
        datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
        if today is not None
        else now
    )
    start = end - timedelta(days=window_days)

    out: list[ResourceVersionRecord] = []
    # Group assessable records by region for batched CloudWatch calls.
    by_region: dict[str, list[tuple[int, MetricSpec]]] = {}
    for idx, record in enumerate(records):
        spec = metric_spec_for(record.resource_type)
        if spec is None:
            out.append(
                record.model_copy(
                    update={
                        "usage_status": UsageStatus.NO_METRIC.value,
                        "usage_window_days": window_days,
                        "usage_assessed_at": now,
                    }
                )
            )
            continue
        # Placeholder; filled after the region's metric query resolves.
        out.append(record)
        by_region.setdefault(record.region, []).append((idx, spec))

    for region, items in by_region.items():
        results = _query_region(session, region, items, records, start, end)
        for idx, spec in items:
            value, had_data = results.get(idx, (None, False))
            out[idx] = _annotate(
                records[idx], spec, value, had_data, window_days, now
            )

    return out


def _annotate(
    record: ResourceVersionRecord,
    spec: MetricSpec,
    value: float | None,
    had_data: bool,
    window_days: int,
    now: datetime,
) -> ResourceVersionRecord:
    if not had_data:
        status = UsageStatus.NO_DATA
        usage_value = None
    elif (value or 0) > 0:
        status = UsageStatus.IN_USE
        usage_value = value
    else:
        status = UsageStatus.IDLE
        usage_value = 0.0
    return record.model_copy(
        update={
            "usage_status": status.value,
            "usage_metric": "+".join(spec.metric_names),
            "usage_value": usage_value,
            "usage_window_days": window_days,
            "usage_source": spec.source,
            "usage_assessed_at": now,
        }
    )


def _query_region(
    session: boto3.Session,
    region: str,
    items: list[tuple[int, MetricSpec]],
    records: list[ResourceVersionRecord],
    start: datetime,
    end: datetime,
) -> dict[int, tuple[float | None, bool]]:
    """Run a batched GetMetricData for one region.

    Returns {record_index: (summed_value, had_any_datapoints)}. On a region-level
    failure, every record in the region gets (None, False) -> NO_DATA, isolating
    the failure without aborting other regions.
    """
    client = session.client("cloudwatch", region_name=region)

    queries = []
    # Map each CloudWatch query id back to its record index.
    qid_to_idx: dict[str, int] = {}
    for n, (idx, spec) in enumerate(items):
        dimension_value = records[idx].resource_id
        for m, metric_name in enumerate(spec.metric_names):
            qid = f"q{n}_{m}"
            qid_to_idx[qid] = idx
            queries.append(
                {
                    "Id": qid,
                    "MetricStat": {
                        "Metric": {
                            "Namespace": spec.namespace,
                            "MetricName": metric_name,
                            "Dimensions": [
                                {"Name": spec.dimension_name, "Value": dimension_value}
                            ],
                        },
                        "Period": max(int((end - start).total_seconds()), 60),
                        "Stat": spec.statistic,
                    },
                    "ReturnData": True,
                }
            )

    results: dict[int, tuple[float | None, bool]] = {}
    try:
        paginator_queries = queries
        response_results: list[dict] = []
        next_token: str | None = None
        while True:
            kwargs = {
                "MetricDataQueries": paginator_queries,
                "StartTime": start,
                "EndTime": end,
            }
            if next_token:
                kwargs["NextToken"] = next_token
            resp = client.get_metric_data(**kwargs)
            response_results.extend(resp.get("MetricDataResults", []))
            next_token = resp.get("NextToken")
            if not next_token:
                break
    except Exception:
        # Region-level failure isolated: every record here becomes NO_DATA.
        return {idx: (None, False) for idx, _ in items}

    for res in response_results:
        idx = qid_to_idx.get(res.get("Id", ""))
        if idx is None:
            continue
        values = res.get("Values", []) or []
        prev_value, prev_had = results.get(idx, (None, False))
        if values:
            summed = (prev_value or 0.0) + sum(values)
            results[idx] = (summed, True)
        else:
            # No datapoints for this metric; keep any value from a sibling metric.
            results[idx] = (prev_value, prev_had)

    # Records with no result entry at all had no datapoints.
    for idx, _ in items:
        results.setdefault(idx, (None, False))
    return results
