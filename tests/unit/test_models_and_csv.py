"""Tests for the normalized record model and CSV writer (tasks 2.1, 2.2)."""

from __future__ import annotations

import io

from aws_lifecycle_inventory.models import ResourceVersionRecord
from aws_lifecycle_inventory.output.csv_writer import (
    BASELINE_COLUMNS,
    COLUMNS,
    write_records,
)


def test_record_exposes_baseline_fields():
    record = ResourceVersionRecord(
        account_id="123456789012",
        region="us-east-1",
        resource_type="AWS::Lambda::Function",
        resource_id="my-fn",
        resource_arn="arn:aws:lambda:us-east-1:123456789012:function:my-fn",
        software_type="runtime",
        software_name="python",
        version="3.12",
    )
    for field in BASELINE_COLUMNS:
        assert hasattr(record, field)
    # collected_at defaults to an aware UTC timestamp.
    assert record.collected_at.tzinfo is not None
    assert record.inventory_source == "DIRECT_API"


def test_csv_header_keeps_baseline_first():
    stream = io.StringIO()
    write_records([], stream)
    header = stream.getvalue().splitlines()[0].split(",")
    # Baseline columns stay first and in order (append-only contract).
    assert header[: len(BASELINE_COLUMNS)] == list(BASELINE_COLUMNS)
    assert header == list(COLUMNS)


def test_csv_empty_version_serializes_as_empty_cell():
    record = ResourceVersionRecord(
        account_id="123456789012",
        region="us-east-1",
        resource_type="AWS::Redshift::Cluster",
        resource_id="no-version",
        version="",
    )
    stream = io.StringIO()
    count = write_records([record], stream)
    assert count == 1
    rows = stream.getvalue().splitlines()
    data = rows[1].split(",")
    version_index = BASELINE_COLUMNS.index("version")
    assert data[version_index] == ""
