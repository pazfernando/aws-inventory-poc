"""Shared test fixtures.

Sets dummy AWS credentials so boto3 never looks for real ones. All tests use
moto (@mock_aws) and never contact real AWS.
"""

from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def _aws_dummy_credentials(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    # Ensure no local profile/config leaks into tests.
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    yield


REGION = "us-east-1"
ACCOUNT_ID = "123456789012"
