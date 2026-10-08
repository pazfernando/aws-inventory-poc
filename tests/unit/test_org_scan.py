"""Tests for organization-wide scanning (Change 07)."""

from __future__ import annotations

import boto3
from botocore.exceptions import ClientError
from moto import mock_aws

from aws_lifecycle_inventory.account_access import assume_role_session
from aws_lifecycle_inventory.models import ResourceVersionRecord
from aws_lifecycle_inventory.orchestration import (
    ORG_SOURCE_STRATEGY,
    CollectorStatus,
    run_org_scan,
)


# --- stubs --------------------------------------------------------------------


class _StubSTS:
    def __init__(self, deny_accounts: set[str]):
        self._deny = deny_accounts

    def assume_role(self, RoleArn, RoleSessionName, **_):
        account_id = RoleArn.split(":")[4]
        if account_id in self._deny:
            raise ClientError(
                {
                    "Error": {
                        "Code": "AccessDenied",
                        "Message": "not authorized to perform sts:AssumeRole",
                    }
                },
                "AssumeRole",
            )
        return {
            "Credentials": {
                "AccessKeyId": f"AKIA{account_id[:6]}",
                "SecretAccessKey": "secret",
                "SessionToken": "token",
            }
        }


class _StubBaseSession:
    region_name = "us-east-1"

    def __init__(self, deny_accounts: set[str] = frozenset()):
        self._deny = deny_accounts

    def client(self, service, region_name=None):
        assert service == "sts"
        return _StubSTS(self._deny)


class _AccountCollector:
    name = "accounted"

    def collect(self, session, account_id, region):
        record = ResourceVersionRecord(
            account_id=account_id,
            region=region,
            resource_type="AWS::Test::Resource",
            resource_id=f"{account_id}-{region}",
            software_name="thing",
            version="1.0",
        )
        return [record], CollectorStatus(name=self.name, ok=True, record_count=1)


ACCOUNTS = ["111111111111", "222222222222"]
ROLE = "ScanRole"


# --- task 1.1: assume-role session factory (mocked STS) -----------------------


@mock_aws
def test_session_factory_builds_session_per_target_account():
    base = boto3.Session(region_name="us-east-1")
    for account in ACCOUNTS:
        account_session = assume_role_session(base, account, ROLE)
        assert isinstance(account_session, boto3.Session)
        identity = account_session.client("sts").get_caller_identity()
        assert "assumed-role" in identity["Arn"]


# --- task 1.2: account isolation ----------------------------------------------


def test_inaccessible_account_does_not_abort_scan():
    session = _StubBaseSession(deny_accounts={"222222222222"})
    result = run_org_scan(
        [_AccountCollector()], session, ["us-east-1"], ACCOUNTS, role_name=ROLE
    )

    statuses = {s.account_id: s for s in result.account_statuses}
    assert statuses["222222222222"].ok is False
    assert statuses["222222222222"].error_code == "AccessDenied"
    assert statuses["111111111111"].ok is True
    # The other account was still scanned.
    assert {r.account_id for r in result.records} == {"111111111111"}


# --- task 2.1: account x regions iteration, account provenance ----------------


def test_records_keep_originating_account_when_combined():
    session = _StubBaseSession()
    result = run_org_scan(
        [_AccountCollector()],
        session,
        ["us-east-1", "eu-west-1"],
        ACCOUNTS,
        role_name=ROLE,
    )

    assert [(r.account_id, r.resource_id) for r in result.records] == [
        ("111111111111", "111111111111-us-east-1"),
        ("111111111111", "111111111111-eu-west-1"),
        ("222222222222", "222222222222-us-east-1"),
        ("222222222222", "222222222222-eu-west-1"),
    ]


# --- task 2.2: account-aware execution summary ---------------------------------


def test_execution_summary_breaks_down_by_account_region_source_collector():
    session = _StubBaseSession(deny_accounts={"222222222222"})
    result = run_org_scan(
        [_AccountCollector()], session, ["us-east-1"], ACCOUNTS, role_name=ROLE
    )

    summary = result.execution_summary()

    # Account level is present for every target account.
    assert set(summary) == set(ACCOUNTS)
    ok_account = summary["111111111111"]
    assert ok_account["access"]["ok"] is True
    assert ok_account["regions"]["us-east-1"]["DIRECT_API"]["accounted"]["ok"] is True

    failed = summary["222222222222"]
    assert failed["access"]["ok"] is False
    assert failed["access"]["error_code"] == "AccessDenied"
    assert failed["regions"] == {}


# --- task 3.1: DIRECT_API_PRIMARY fan-out with per-account provenance ----------


def test_direct_api_primary_fan_out_preserves_account_provenance():
    # Change 03's recorded decision drives the org-wide source strategy.
    assert ORG_SOURCE_STRATEGY == "DIRECT_API_PRIMARY"

    session = _StubBaseSession()
    result = run_org_scan(
        [_AccountCollector()], session, ["us-east-1"], ACCOUNTS, role_name=ROLE
    )

    assert result.records, "fan-out must gather records from both accounts"
    for record in result.records:
        assert record.inventory_source == "DIRECT_API"
    by_id = {r.resource_id: r for r in result.records}
    # Provenance preserved per account, no silent overwrite.
    assert by_id["111111111111-us-east-1"].account_id == "111111111111"
    assert by_id["222222222222-us-east-1"].account_id == "222222222222"
