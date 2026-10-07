"""Tests for the scan engine partial-failure isolation (task 3.1)."""

from __future__ import annotations

from aws_lifecycle_inventory.models import ResourceVersionRecord
from aws_lifecycle_inventory.orchestration import CollectorStatus, run_scan


class _GoodCollector:
    name = "good"

    def collect(self, session, account_id, region):
        record = ResourceVersionRecord(
            account_id=account_id,
            region=region,
            resource_type="AWS::Test::Resource",
            resource_id="good-1",
            software_name="thing",
            version="1.0",
        )
        return [record], CollectorStatus(name=self.name, ok=True, record_count=1)


class _ExplodingCollector:
    name = "boom"

    def collect(self, session, account_id, region):
        raise RuntimeError("simulated collector failure")


def test_failing_collector_does_not_abort_scan():
    result = run_scan(
        [_ExplodingCollector(), _GoodCollector()],
        session=None,
        region="us-east-1",
        account_id="123456789012",
    )

    # The good collector still produced its record.
    assert len(result.records) == 1
    assert result.records[0].resource_id == "good-1"

    by_name = {s.name: s for s in result.collector_statuses}
    assert by_name["good"].ok is True
    assert by_name["boom"].ok is False
    assert by_name["boom"].error_code == "RuntimeError"
    assert "simulated collector failure" in by_name["boom"].error_message
