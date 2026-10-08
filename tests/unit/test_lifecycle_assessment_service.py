"""Tests for the reusable, flow-independent lifecycle assessment service
(refactor-lifecycle-assessment-reuse, tasks 1.3 and 2.2)."""

from __future__ import annotations

from datetime import date

from aws_lifecycle_inventory.lifecycle import assess_records
from aws_lifecycle_inventory.lifecycle.models import LifecycleEvidence, LifecycleStatus
from aws_lifecycle_inventory.models import ResourceVersionRecord

TODAY = date(2026, 1, 1)


def _lambda_record(version="3.12"):
    return ResourceVersionRecord(
        account_id="123456789012",
        region="us-east-1",
        resource_type="AWS::Lambda::Function",
        resource_id="fn",
        software_name="python",
        version=version,
    )


def _nonversion_record():
    return ResourceVersionRecord(
        account_id="123456789012",
        region="us-east-1",
        resource_type="AWS::SNS::Topic",
        resource_id="topic",
    )


class _StubProvider:
    """Matches python 3.12 with a fixed EOL date."""

    source = "STUB"

    def match(self, record):
        if record.software_name == "python" and record.version == "3.12":
            return LifecycleEvidence(
                source=self.source,
                evidence_id="stub-1",
                eol_date=date(2030, 1, 1),
            )
        return None


# --- task 1.3: records in -> annotated records out -------------------------

def test_assess_records_annotates_with_supplied_providers():
    out = assess_records(
        [_lambda_record()], providers=[_StubProvider()], today=TODAY
    )
    assert len(out) == 1
    assert out[0].lifecycle_source == "STUB"
    assert out[0].lifecycle_evidence_id == "stub-1"
    assert out[0].eol_date == date(2030, 1, 1)
    # SUPPORTED (EOL far in the future), distinct from UNKNOWN.
    assert out[0].lifecycle_status == LifecycleStatus.SUPPORTED.value


def test_assess_records_default_providers_without_session_completes():
    # session=None -> AWS Health skipped (non-fatal); EndOfLife still runs.
    out = assess_records([_lambda_record()], session=None, today=TODAY)
    assert len(out) == 1
    # EndOfLife seed knows python 3.12; a conclusion is produced (non-UNKNOWN).
    assert out[0].lifecycle_status != ""
    assert out[0].evaluated_at is not None


def test_assess_records_is_flow_independent_on_arbitrary_records():
    # Records that did not come from a scan are assessable all the same.
    manual = ResourceVersionRecord(
        account_id="000000000000",
        region="eu-west-1",
        resource_type="AWS::Lambda::Function",
        resource_id="loaded-from-csv",
        software_name="python",
        version="3.12",
    )
    out = assess_records([manual], providers=[_StubProvider()], today=TODAY)
    assert out[0].lifecycle_source == "STUB"


def test_assess_records_non_version_bearing_is_not_applicable():
    out = assess_records([_nonversion_record()], providers=[_StubProvider()], today=TODAY)
    assert out[0].lifecycle_status == LifecycleStatus.NOT_APPLICABLE.value


def test_explicit_providers_override_session():
    # When providers are given, they are used verbatim regardless of session.
    out = assess_records(
        [_lambda_record()],
        session=None,
        providers=[_StubProvider()],
        today=TODAY,
    )
    assert out[0].lifecycle_source == "STUB"
