"""Tests for the lifecycle evaluation model (tasks 1.1, 1.2, 2.1, 2.2, 3.1, 3.2)."""

from __future__ import annotations

import io
from datetime import date, timedelta

from aws_lifecycle_inventory.lifecycle.evaluator import evaluate_record
from aws_lifecycle_inventory.lifecycle.models import LifecycleEvidence, LifecycleStatus
from aws_lifecycle_inventory.lifecycle.providers.endoflife import EndOfLifeProvider
from aws_lifecycle_inventory.models import ResourceVersionRecord
from aws_lifecycle_inventory.output.csv_writer import BASELINE_COLUMNS, COLUMNS, write_records

TODAY = date(2026, 1, 1)


def _record(software_name="python", version="3.12"):
    return ResourceVersionRecord(
        account_id="123456789012",
        region="us-east-1",
        resource_type="AWS::Lambda::Function",
        resource_id="fn",
        software_name=software_name,
        version=version,
    )


# --- task 1.1: all eight states exist --------------------------------------

def test_lifecycle_status_has_eight_states():
    names = {s.name for s in LifecycleStatus}
    assert names == {
        "SUPPORTED", "EOL_365", "EOL_180", "EOL_90", "EOL_30",
        "EOL", "UNSUPPORTED", "UNKNOWN",
    }


# --- task 1.2: lifecycle columns appended after baseline -------------------

def test_lifecycle_columns_appended_after_baseline():
    assert COLUMNS[: len(BASELINE_COLUMNS)] == BASELINE_COLUMNS
    for col in ("lifecycle_status", "eol_date", "days_to_eol",
                "lifecycle_source", "lifecycle_evidence_id", "evaluated_at"):
        assert col in COLUMNS


# --- task 2.1: evaluator buckets + UNKNOWN default -------------------------

class _FixedProvider:
    source = "TEST"

    def __init__(self, evidence):
        self._evidence = evidence

    def match(self, record):
        return self._evidence


def _eval_with_eol(days_ahead):
    eol = TODAY + timedelta(days=days_ahead)
    provider = _FixedProvider(LifecycleEvidence(source="TEST", evidence_id="e1", eol_date=eol))
    return evaluate_record(_record(), [provider], today=TODAY)


def test_bucket_supported_far_future():
    assert _eval_with_eol(400).lifecycle_status == "SUPPORTED"


def test_bucket_eol_365():
    assert _eval_with_eol(300).lifecycle_status == "EOL_365"


def test_bucket_eol_180():
    assert _eval_with_eol(120).lifecycle_status == "EOL_180"


def test_bucket_eol_90():
    assert _eval_with_eol(60).lifecycle_status == "EOL_90"


def test_bucket_eol_30():
    assert _eval_with_eol(15).lifecycle_status == "EOL_30"


def test_bucket_past_eol():
    r = _eval_with_eol(-10)
    assert r.lifecycle_status == "EOL"
    assert r.days_to_eol == -10


def test_explicit_status_overrides_bucket():
    provider = _FixedProvider(
        LifecycleEvidence(source="TEST", evidence_id="e1", status=LifecycleStatus.UNSUPPORTED)
    )
    assert evaluate_record(_record(), [provider], today=TODAY).lifecycle_status == "UNSUPPORTED"


def test_no_match_yields_unknown_not_supported():
    class _NoMatch:
        source = "NONE"
        def match(self, record):
            return None

    r = evaluate_record(_record(), [_NoMatch()], today=TODAY)
    assert r.lifecycle_status == "UNKNOWN"
    assert r.lifecycle_status != "SUPPORTED"
    assert r.lifecycle_source == ""
    assert r.lifecycle_evidence_id == ""


# --- task 2.2: evidence present + UNKNOWN distinguishable in CSV -----------

def test_non_unknown_carries_evidence():
    r = _eval_with_eol(300)
    assert r.lifecycle_source == "TEST"
    assert r.lifecycle_evidence_id == "e1"


def test_unknown_distinguishable_from_supported_in_csv():
    unknown = evaluate_record(
        _record(software_name="nothing", version="9.9"),
        [EndOfLifeProvider.load(allow_refresh=False)],
        today=TODAY,
    )
    supported = _eval_with_eol(400)

    stream = io.StringIO()
    write_records([unknown, supported], stream)
    lines = stream.getvalue().splitlines()
    header = lines[0].split(",")
    status_idx = header.index("lifecycle_status")
    src_idx = header.index("lifecycle_source")

    u = lines[1].split(",")
    s = lines[2].split(",")
    assert u[status_idx] == "UNKNOWN"
    assert u[src_idx] == ""          # no evidence for UNKNOWN
    assert s[status_idx] == "SUPPORTED"
    assert s[src_idx] == "TEST"      # evidence present for SUPPORTED


# --- EndOfLife provider classifies a known runtime ------------------------

def test_endoflife_provider_classifies_known_runtime():
    provider = EndOfLifeProvider.load(allow_refresh=False)
    ev = provider.match(_record(software_name="python", version="3.10"))
    assert ev is not None
    assert ev.source == "ENDOFLIFE"
    # evidence id is the official source link
    assert ev.evidence_id.startswith("http")
    assert ev.eol_date is not None


def test_endoflife_provider_no_entry_returns_none():
    provider = EndOfLifeProvider.load(allow_refresh=False)
    assert provider.match(_record(software_name="python", version="99.99")) is None


# --- end-to-end supported / approaching / EOL / unknown -------------------

def test_end_to_end_cases_through_endoflife_provider():
    provider = EndOfLifeProvider.load(allow_refresh=False)

    # python 3.8 EOL 2027-08-31 — within a year of TODAY (2026-01-01) is EOL_* ;
    # just assert it is a dated, evidence-backed conclusion (not UNKNOWN).
    py38 = evaluate_record(
        _record(software_name="python", version="3.8"), [provider], today=TODAY
    )
    assert py38.lifecycle_status != "UNKNOWN"
    assert py38.lifecycle_source == "ENDOFLIFE"
    assert py38.eol_date is not None

    # python 3.12 EOL far in the future -> SUPPORTED
    supported = evaluate_record(
        _record(software_name="python", version="3.12"), [provider], today=TODAY
    )
    assert supported.lifecycle_status == "SUPPORTED"

    # unmapped version -> UNKNOWN
    unknown = evaluate_record(
        _record(software_name="python", version="99.99"), [provider], today=TODAY
    )
    assert unknown.lifecycle_status == "UNKNOWN"
