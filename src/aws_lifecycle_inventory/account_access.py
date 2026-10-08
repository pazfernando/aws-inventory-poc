"""Cross-account read-only access via STS AssumeRole (Change 07).

Account access is just a different session source for the shared engine: the
factory assumes a read-only role in each target account and hands back a
per-account boto3 session. Assume-role failures are isolated by
``resolve_account_session`` — they become an inaccessible account status, never
an abort.
"""

from __future__ import annotations

from dataclasses import dataclass

import boto3
from botocore.exceptions import ClientError

DEFAULT_ROLE_SESSION_NAME = "aws-lifecycle-inventory"


@dataclass
class AccountAccessStatus:
    """Outcome of resolving access to one target account."""

    account_id: str
    ok: bool
    record_count: int = 0
    error_code: str = ""
    error_message: str = ""


def assume_role_session(
    session: boto3.Session,
    account_id: str,
    role_name: str,
    external_id: str | None = None,
    role_session_name: str = DEFAULT_ROLE_SESSION_NAME,
    region: str | None = None,
) -> boto3.Session:
    """Assume the read-only role ``role_name`` in ``account_id``.

    The target role must grant read-only permissions to the running principal.
    Raises the underlying ClientError on failure; callers that need isolation
    should use :func:`resolve_account_session`.
    """
    params: dict = {
        "RoleArn": f"arn:aws:iam::{account_id}:role/{role_name}",
        "RoleSessionName": role_session_name,
    }
    if external_id:
        params["ExternalId"] = external_id
    credentials = session.client("sts").assume_role(**params)["Credentials"]
    return boto3.Session(
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
        region_name=region or session.region_name,
    )


def resolve_account_session(
    session: boto3.Session,
    account_id: str,
    role_name: str,
    external_id: str | None = None,
    role_session_name: str = DEFAULT_ROLE_SESSION_NAME,
) -> tuple[boto3.Session | None, AccountAccessStatus]:
    """Assume the target role, isolating failures per account.

    Returns ``(session, status)``. On any assume-role failure the session is
    ``None`` and the status reports the error; the caller continues with the
    remaining accounts.
    """
    try:
        account_session = assume_role_session(
            session,
            account_id,
            role_name,
            external_id=external_id,
            role_session_name=role_session_name,
        )
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", type(exc).__name__)
        return None, AccountAccessStatus(
            account_id=account_id,
            ok=False,
            error_code=code,
            error_message=str(exc),
        )
    return account_session, AccountAccessStatus(account_id=account_id, ok=True)
