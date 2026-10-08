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


# --- add-resource-usage-metrics: usage columns -----------------------------

def test_usage_columns_appended_after_existing():
    from aws_lifecycle_inventory.output.csv_writer import (
        COVERAGE_COLUMNS,
        LIFECYCLE_COLUMNS,
        USAGE_COLUMNS,
    )

    expected_prefix = BASELINE_COLUMNS + LIFECYCLE_COLUMNS + COVERAGE_COLUMNS
    assert COLUMNS[: len(expected_prefix)] == expected_prefix
    assert COLUMNS[len(expected_prefix):] == USAGE_COLUMNS


def test_unassessed_record_has_empty_usage_cells():
    record = ResourceVersionRecord(
        account_id="123456789012",
        region="us-east-1",
        resource_type="AWS::EC2::VPC",
        resource_id="vpc-1",
    )
    stream = io.StringIO()
    write_records([record], stream)
    header = stream.getvalue().splitlines()[0].split(",")
    data = stream.getvalue().splitlines()[1].split(",")
    row = dict(zip(header, data))
    for col in (
        "usage_status", "usage_metric", "usage_value",
        "usage_window_days", "usage_source", "usage_assessed_at",
    ):
        assert row[col] == ""


def test_no_metric_distinct_from_idle_zero():
    no_metric = ResourceVersionRecord(
        account_id="123456789012", region="us-east-1",
        resource_type="AWS::EC2::VPC", resource_id="vpc-1",
        usage_status="NO_METRIC",
    )
    idle = ResourceVersionRecord(
        account_id="123456789012", region="us-east-1",
        resource_type="AWS::Lambda::Function", resource_id="fn",
        usage_status="IDLE", usage_value=0.0,
    )
    stream = io.StringIO()
    write_records([no_metric, idle], stream)
    lines = stream.getvalue().splitlines()
    header = lines[0].split(",")
    r_no_metric = dict(zip(header, lines[1].split(",")))
    r_idle = dict(zip(header, lines[2].split(",")))
    assert r_no_metric["usage_status"] == "NO_METRIC"
    assert r_no_metric["usage_value"] == ""        # no value
    assert r_idle["usage_status"] == "IDLE"
    assert r_idle["usage_value"] == "0.0"          # explicit zero, distinct
