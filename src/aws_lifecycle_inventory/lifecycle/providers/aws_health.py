"""AWS Health Planned Lifecycle Events provider (Change 05).

Enriches already-discovered resources with AWS-authoritative lifecycle evidence.
It does NOT discover resources. It is non-fatal: if the Health API is unavailable
(no Business/Enterprise Support, access denied, or unsupported), the provider
degrades to "unavailable" and matches nothing, so the scan still completes and
other providers continue. Absence of a Health event never implies SUPPORTED.
"""

from __future__ import annotations

from datetime import date, datetime

import boto3

from aws_lifecycle_inventory.lifecycle.models import LifecycleEvidence, LifecycleStatus
from aws_lifecycle_inventory.models import ResourceVersionRecord

SOURCE = "AWS_HEALTH"

# AWS Health event type category for scheduled/planned lifecycle changes.
# The Health API enum accepts: investigation, accountNotification, issue,
# scheduledChange. Planned lifecycle events are delivered under scheduledChange.
_LIFECYCLE_EVENT_CATEGORY = "scheduledChange"


def _as_date(value: object) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return None


class AWSHealthProvider:
    source = SOURCE

    def __init__(self) -> None:
        self.available: bool = False
        self.unavailable_reason: str = "not initialized"
        # ARN -> evidence built during prefetch.
        self._by_arn: dict[str, LifecycleEvidence] = {}

    @classmethod
    def build(cls, session: boto3.Session, region: str = "us-east-1") -> "AWSHealthProvider":
        """Construct and prefetch. The Health API is global via the us-east-1 endpoint."""
        provider = cls()
        provider._prefetch(session, region)
        return provider

    def _prefetch(self, session: boto3.Session, region: str) -> None:
        try:
            client = session.client("health", region_name=region)
            events = self._list_lifecycle_events(client)
            for event in events:
                self._index_event(client, event)
            self.available = True
            self.unavailable_reason = ""
        except Exception as exc:  # access denied, unsupported plan, endpoint, etc.
            self.available = False
            self.unavailable_reason = f"{type(exc).__name__}: {exc}"
            self._by_arn = {}

    def _list_lifecycle_events(self, client) -> list[dict]:
        events: list[dict] = []
        paginator = client.get_paginator("describe_events")
        for page in paginator.paginate(
            filter={"eventTypeCategories": [_LIFECYCLE_EVENT_CATEGORY]}
        ):
            events.extend(page.get("events", []))
        return events

    def _index_event(self, client, event: dict) -> None:
        event_arn = event.get("arn", "")
        if not event_arn:
            return
        eol_date = _as_date(event.get("endTime") or event.get("startTime"))
        entities = self._affected_entities(client, event_arn)
        for entity in entities:
            entity_arn = entity.get("entityArn", "") or entity.get("entityValue", "")
            # Only match on a reliable ARN identifier.
            if not entity_arn.startswith("arn:"):
                continue
            self._by_arn[entity_arn] = LifecycleEvidence(
                source=self.source,
                evidence_id=event_arn,
                eol_date=eol_date,
                # Health asserts a planned lifecycle change; let the evaluator bucket
                # by the event date rather than hard-coding a status.
                status=None,
                details={
                    "event_arn": event_arn,
                    "event_type_code": event.get("eventTypeCode", ""),
                    "event_type_category": event.get("eventTypeCategory", ""),
                    "event_date": eol_date.isoformat() if eol_date else "",
                    "affected_entity": entity_arn,
                    "affected_entity_status": entity.get("statusCode", ""),
                    "lifecycle_source": self.source,
                },
            )

    def _affected_entities(self, client, event_arn: str) -> list[dict]:
        entities: list[dict] = []
        paginator = client.get_paginator("describe_affected_entities")
        for page in paginator.paginate(filter={"eventArns": [event_arn]}):
            entities.extend(page.get("entities", []))
        return entities

    def match(self, record: ResourceVersionRecord) -> LifecycleEvidence | None:
        if not self.available or not record.resource_arn:
            return None
        return self._by_arn.get(record.resource_arn)
