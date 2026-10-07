"""Tests for the AWS Health lifecycle provider (Change 05, tasks 1.1-3.2)."""

from __future__ import annotations

from datetime import date, datetime, timezone

from aws_lifecycle_inventory.lifecycle.evaluator import evaluate_record
from aws_lifecycle_inventory.lifecycle.providers.aws_health import AWSHealthProvider
from aws_lifecycle_inventory.lifecycle.models import LifecycleEvidence
from aws_lifecycle_inventory.lifecycle.providers.endoflife import EndOfLifeProvider
from aws_lifecycle_inventory.models import ResourceVersionRecord

REGION = "us-east-1"
ACCOUNT_ID = "123456789012"
EKS_ARN = f"arn:aws:eks:{REGION}:{ACCOUNT_ID}:cluster/my-eks"
TODAY = date(2026, 1, 1)


def _eks_record(arn=EKS_ARN, version="1.30"):
    return ResourceVersionRecord(
        account_id=ACCOUNT_ID,
        region=REGION,
        resource_type="AWS::EKS::Cluster",
        resource_id="my-eks",
        resource_arn=arn,
        software_name="kubernetes",
        version=version,
    )


# --- Stub Health client (moto has no Health backend) -----------------------

class _StubHealthClient:
    def __init__(self, events, entities):
        self._events = events
        self._entities = entities  # event_arn -> [entities]

    def get_paginator(self, op):
        return _StubPaginator(op, self)


class _StubPaginator:
    def __init__(self, op, client):
        self._op = op
        self._client = client

    def paginate(self, **kwargs):
        if self._op == "describe_events":
            # Mirror the AWS Health enum validation so an invalid filter category
            # (the kind of bug that slips past a lax stub) fails loudly here too.
            categories = kwargs.get("filter", {}).get("eventTypeCategories", [])
            valid = {"investigation", "accountNotification", "issue", "scheduledChange"}
            invalid = [c for c in categories if c not in valid]
            if invalid:
                raise ValueError(f"invalid eventTypeCategories: {invalid}")
            yield {"events": self._client._events}
        elif self._op == "describe_affected_entities":
            arns = kwargs.get("filter", {}).get("eventArns", [])
            entities = []
            for arn in arns:
                entities.extend(self._client._entities.get(arn, []))
            yield {"entities": entities}


class _StubSession:
    def __init__(self, client=None, raise_exc=None):
        self._client = client
        self._raise = raise_exc

    def client(self, _service, region_name=None):
        if self._raise is not None:
            raise self._raise
        return self._client


def _health_provider_with_event():
    event_arn = f"arn:aws:health:global::event/EKS/AWS_EKS_PLANNED_LIFECYCLE_EVENT/{ACCOUNT_ID}"
    events = [
        {
            "arn": event_arn,
            "eventTypeCode": "AWS_EKS_PLANNED_LIFECYCLE_EVENT",
            "eventTypeCategory": "scheduledChange",
            "startTime": datetime(2026, 3, 1, tzinfo=timezone.utc),
            "endTime": datetime(2026, 3, 1, tzinfo=timezone.utc),
        }
    ]
    entities = {
        event_arn: [{"entityArn": EKS_ARN, "statusCode": "IMPAIRED"}]
    }
    session = _StubSession(client=_StubHealthClient(events, entities))
    return AWSHealthProvider.build(session, REGION), event_arn


# --- task 1.1: match by ARN + evidence attached ----------------------------

def test_lifecycle_filter_category_is_valid_aws_enum():
    from aws_lifecycle_inventory.lifecycle.providers.aws_health import (
        _LIFECYCLE_EVENT_CATEGORY,
    )

    # Guard against using a category AWS does not accept (regression test).
    assert _LIFECYCLE_EVENT_CATEGORY in {
        "investigation", "accountNotification", "issue", "scheduledChange",
    }

def test_health_matches_record_by_arn():
    provider, event_arn = _health_provider_with_event()
    assert provider.available is True
    ev = provider.match(_eks_record())
    assert ev is not None
    assert ev.source == "AWS_HEALTH"
    assert ev.evidence_id == event_arn
    assert ev.eol_date == date(2026, 3, 1)


def test_health_no_match_when_arn_differs():
    provider, _ = _health_provider_with_event()
    other = _eks_record(arn=f"arn:aws:eks:{REGION}:{ACCOUNT_ID}:cluster/other")
    assert provider.match(other) is None


# --- task 1.2: evidence fields preserved -----------------------------------

def test_health_evidence_preserves_all_fields():
    provider, event_arn = _health_provider_with_event()
    ev = provider.match(_eks_record())
    d = ev.details
    assert d["event_arn"] == event_arn
    assert d["event_type_code"] == "AWS_EKS_PLANNED_LIFECYCLE_EVENT"
    assert d["event_type_category"] == "scheduledChange"
    assert d["event_date"] == "2026-03-01"
    assert d["affected_entity"] == EKS_ARN
    assert d["affected_entity_status"] == "IMPAIRED"
    assert d["lifecycle_source"] == "AWS_HEALTH"


# --- task 2.1: Health precedence preserves EndOfLife provenance ------------

def test_health_precedence_preserves_endoflife_provenance():
    provider, event_arn = _health_provider_with_event()
    # EndOfLife also has amazon-eks 1.30; Health is listed first (higher precedence).
    result = evaluate_record(
        _eks_record(version="1.30"),
        [provider, EndOfLifeProvider.load(allow_refresh=False)],
        today=TODAY,
    )
    # Health supplies the conclusion.
    assert result.lifecycle_source == "AWS_HEALTH"
    assert result.lifecycle_evidence_id == event_arn
    # EndOfLife provenance is preserved, not discarded.
    other = {o["source"] for o in result.lifecycle_other_sources}
    assert "ENDOFLIFE" in other


# --- task 2.2: no Health event never implies SUPPORTED ---------------------

def test_no_health_event_never_supported():
    # Health available but with no matching event, and no other provider.
    provider, _ = _health_provider_with_event()
    unmatched = _eks_record(arn=f"arn:aws:eks:{REGION}:{ACCOUNT_ID}:cluster/nomatch")
    result = evaluate_record(unmatched, [provider], today=TODAY)
    assert result.lifecycle_status == "UNKNOWN"
    assert result.lifecycle_status != "SUPPORTED"


# --- task 3.1: non-fatal availability detection ----------------------------

def test_health_unavailable_degrades_gracefully():
    session = _StubSession(raise_exc=PermissionError("AccessDeniedException"))
    provider = AWSHealthProvider.build(session, REGION)
    assert provider.available is False
    assert "AccessDenied" in provider.unavailable_reason or "PermissionError" in provider.unavailable_reason
    # Matches nothing when unavailable.
    assert provider.match(_eks_record()) is None


def test_scan_completes_when_health_unavailable():
    session = _StubSession(raise_exc=PermissionError("denied"))
    health = AWSHealthProvider.build(session, REGION)
    # Unmatched record with Health unavailable + EndOfLife (no entry) -> UNKNOWN.
    result = evaluate_record(
        _eks_record(version="99.99"),
        [health, EndOfLifeProvider.load(allow_refresh=False)],
        today=TODAY,
    )
    assert result.lifecycle_status == "UNKNOWN"


# --- task 3.2: end-to-end available vs unavailable -------------------------

def test_end_to_end_health_available_and_unavailable():
    eol = EndOfLifeProvider.load(allow_refresh=False)
    # Available: Health supplies evidence.
    provider, _ = _health_provider_with_event()
    avail = evaluate_record(_eks_record(), [provider, eol], today=TODAY)
    assert avail.lifecycle_source == "AWS_HEALTH"

    # Unavailable: EndOfLife still evaluates, scan succeeds.
    down = AWSHealthProvider.build(_StubSession(raise_exc=RuntimeError("x")), REGION)
    result = evaluate_record(_eks_record(version="1.30"), [down, eol], today=TODAY)
    assert result.lifecycle_source == "ENDOFLIFE"
    assert result.lifecycle_status in {"SUPPORTED", "EOL_365", "EOL_180", "EOL_90", "EOL_30", "EOL"}
