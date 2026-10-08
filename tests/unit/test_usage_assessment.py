"""Tests for the usage assessment service (add-resource-usage-metrics, tasks 4.x).

CloudWatch GetMetricData is driven through a stub client (moto's get_metric_data
returns no datapoints for put metrics), giving deterministic IN_USE/IDLE/NO_DATA.
"""

from __future__ import annotations

from aws_lifecycle_inventory.models import ResourceVersionRecord
from aws_lifecycle_inventory.usage import DEFAULT_WINDOW_DAYS, UsageStatus, assess_usage

ACCOUNT_ID = "123456789012"
REGION = "us-east-1"


# --- stub CloudWatch ------------------------------------------------------


class _StubCloudWatch:
    """Returns pre-seeded Values per query Id; records the window it was asked."""

    def __init__(self, values_by_id=None, raise_exc=None):
        self._values_by_id = values_by_id or {}
        self._raise = raise_exc
        self.calls = []

    def get_metric_data(self, **kwargs):
        if self._raise is not None:
            raise self._raise
        self.calls.append(kwargs)
        results = []
        for q in kwargs["MetricDataQueries"]:
            results.append(
                {"Id": q["Id"], "Values": self._values_by_id.get(q["Id"], [])}
            )
        return {"MetricDataResults": results}


class _StubSession:
    def __init__(self, client):
        self._client = client

    def client(self, _service, region_name=None):
        return self._client


def _lambda_record(resource_id="fn"):
    return ResourceVersionRecord(
        account_id=ACCOUNT_ID,
        region=REGION,
        resource_type="AWS::Lambda::Function",
        resource_id=resource_id,
    )


def _vpc_record():
    return ResourceVersionRecord(
        account_id=ACCOUNT_ID,
        region=REGION,
        resource_type="AWS::EC2::VPC",
        resource_id="vpc-1",
    )


# --- task 4.1: IN_USE / IDLE / NO_DATA / NO_METRIC -------------------------

def test_in_use_when_activity_above_zero():
    cw = _StubCloudWatch(values_by_id={"q0_0": [3.0, 2.0]})  # Invocations sum=5
    out = assess_usage([_lambda_record()], session=_StubSession(cw))
    assert out[0].usage_status == UsageStatus.IN_USE.value
    assert out[0].usage_value == 5.0
    assert out[0].usage_metric == "Invocations"
    assert out[0].usage_source.startswith("cloudwatch:")


def test_idle_when_metric_present_but_zero_activity():
    cw = _StubCloudWatch(values_by_id={"q0_0": [0.0, 0.0]})
    out = assess_usage([_lambda_record()], session=_StubSession(cw))
    assert out[0].usage_status == UsageStatus.IDLE.value
    assert out[0].usage_value == 0.0


def test_no_data_when_no_datapoints():
    cw = _StubCloudWatch(values_by_id={"q0_0": []})
    out = assess_usage([_lambda_record()], session=_StubSession(cw))
    assert out[0].usage_status == UsageStatus.NO_DATA.value
    assert out[0].usage_value is None


def test_no_metric_for_unmapped_type_makes_no_cloudwatch_call():
    cw = _StubCloudWatch()
    out = assess_usage([_vpc_record()], session=_StubSession(cw))
    assert out[0].usage_status == UsageStatus.NO_METRIC.value
    assert out[0].usage_value is None
    # No CloudWatch call was made for a NO_METRIC resource.
    assert cw.calls == []


# --- task 4.2: window -------------------------------------------------------

def test_default_window_is_30_days():
    cw = _StubCloudWatch(values_by_id={"q0_0": [1.0]})
    out = assess_usage([_lambda_record()], session=_StubSession(cw))
    assert out[0].usage_window_days == DEFAULT_WINDOW_DAYS == 30


def test_caller_overrides_window():
    cw = _StubCloudWatch(values_by_id={"q0_0": [1.0]})
    out = assess_usage([_lambda_record()], session=_StubSession(cw), window_days=90)
    assert out[0].usage_window_days == 90
    # The stub recorded a ~90-day span.
    call = cw.calls[0]
    span_days = (call["EndTime"] - call["StartTime"]).days
    assert span_days == 90


# --- task 4.3: partial-failure isolation -----------------------------------

def test_region_query_failure_yields_no_data_not_abort():
    cw = _StubCloudWatch(raise_exc=RuntimeError("AccessDenied"))
    out = assess_usage([_lambda_record("a"), _lambda_record("b")],
                       session=_StubSession(cw))
    assert all(r.usage_status == UsageStatus.NO_DATA.value for r in out)
    assert all(r.usage_value is None for r in out)


def test_dynamodb_sums_read_and_write_capacity():
    rec = ResourceVersionRecord(
        account_id=ACCOUNT_ID, region=REGION,
        resource_type="AWS::DynamoDB::Table", resource_id="t",
    )
    # Two metrics (read q0_0, write q0_1) summed.
    cw = _StubCloudWatch(values_by_id={"q0_0": [2.0], "q0_1": [3.0]})
    out = assess_usage([rec], session=_StubSession(cw))
    assert out[0].usage_status == UsageStatus.IN_USE.value
    assert out[0].usage_value == 5.0


# --- task 4.4: flow-independent / composition ------------------------------

def test_runs_on_records_not_from_a_scan():
    manual = _lambda_record("loaded-from-csv")
    cw = _StubCloudWatch(values_by_id={"q0_0": [7.0]})
    out = assess_usage([manual], session=_StubSession(cw))
    assert out[0].usage_status == UsageStatus.IN_USE.value
    assert out[0].usage_value == 7.0
