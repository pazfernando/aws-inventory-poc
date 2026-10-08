"""CSV serialization of normalized records.

Owns the baseline column order centrally so later changes append columns without
touching collectors, and never silently remove an existing column.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import TextIO

from aws_lifecycle_inventory.models import ResourceVersionRecord

# Fixed, ordered baseline columns (Change 01). Append-only across future changes.
BASELINE_COLUMNS: tuple[str, ...] = (
    "account_id",
    "region",
    "resource_type",
    "resource_id",
    "resource_arn",
    "software_type",
    "software_name",
    "version",
    "inventory_source",
    "collected_at",
)

# Lifecycle columns (Change 04), appended after the baseline. Never reorder or
# remove an existing column; UNKNOWN must stay distinguishable from SUPPORTED.
LIFECYCLE_COLUMNS: tuple[str, ...] = (
    "lifecycle_status",
    "eol_date",
    "days_to_eol",
    "lifecycle_source",
    "lifecycle_evidence_id",
    "evaluated_at",
)

# Coverage columns (Change 08), appended after the lifecycle columns. Other
# operational fields (collector_status, error_code, error_message) are added by
# their owning changes; never reorder or remove an existing column.
COVERAGE_COLUMNS: tuple[str, ...] = (
    "coverage_status",
)

# Usage columns (add-resource-usage-metrics), appended after coverage. Empty when
# a record has not been through usage assessment; NO_METRIC stays distinct from
# IDLE and NO_DATA. Never reorder or remove an existing column.
USAGE_COLUMNS: tuple[str, ...] = (
    "usage_status",
    "usage_metric",
    "usage_value",
    "usage_window_days",
    "usage_source",
    "usage_assessed_at",
)

COLUMNS: tuple[str, ...] = (
    BASELINE_COLUMNS + LIFECYCLE_COLUMNS + COVERAGE_COLUMNS + USAGE_COLUMNS
)


def _cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _row(record: ResourceVersionRecord) -> list[str]:
    return [_cell(getattr(record, column)) for column in COLUMNS]


def write_records(records: Iterable[ResourceVersionRecord], stream: TextIO) -> int:
    """Write records to an open text stream. Returns the number of data rows."""
    writer = csv.writer(stream)
    writer.writerow(COLUMNS)
    count = 0
    for record in records:
        writer.writerow(_row(record))
        count += 1
    return count


def write_csv(records: Iterable[ResourceVersionRecord], path: str | Path) -> int:
    """Write records to a CSV file at ``path``. Returns the number of data rows."""
    path = Path(path)
    with path.open("w", newline="", encoding="utf-8") as handle:
        return write_records(records, handle)
