"""Usage status set for resource usage assessment.

Four states, kept distinct so a resource without a usage metric is never reported
as idle:

- IN_USE: activity above zero in the observation window.
- IDLE: a usage metric exists but shows no activity across the window.
- NO_DATA: the metric exists but returned no datapoints (or the query failed).
- NO_METRIC: the resource type has no meaningful usage metric.
"""

from __future__ import annotations

from enum import Enum


class UsageStatus(str, Enum):
    IN_USE = "IN_USE"
    IDLE = "IDLE"
    NO_DATA = "NO_DATA"
    NO_METRIC = "NO_METRIC"
