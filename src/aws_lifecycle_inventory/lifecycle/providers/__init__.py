"""Lifecycle evidence providers.

Default precedence order (Change endoflife): AWS Health (authoritative, if
available) -> EndOfLife (verifiable contingency). The evaluator consults them in
order; the first match supplies the conclusion and other matches are preserved as
provenance.
"""

from __future__ import annotations

import boto3

from aws_lifecycle_inventory.lifecycle.providers.aws_health import AWSHealthProvider
from aws_lifecycle_inventory.lifecycle.providers.endoflife import EndOfLifeProvider


def default_lifecycle_providers(
    session: boto3.Session | None = None,
    health_region: str = "us-east-1",
) -> list:
    """Build the default ordered provider list: [AWS Health, EndOfLife].

    AWS Health is non-fatal; if ``session`` is None or Health is unavailable it
    simply matches nothing. EndOfLife loads from cache/seed and self-refreshes.
    """
    providers: list = []
    if session is not None:
        providers.append(AWSHealthProvider.build(session, health_region))
    providers.append(EndOfLifeProvider.load())
    return providers


__all__ = [
    "AWSHealthProvider",
    "EndOfLifeProvider",
    "default_lifecycle_providers",
]
