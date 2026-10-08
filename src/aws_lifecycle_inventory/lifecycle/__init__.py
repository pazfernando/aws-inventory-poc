"""Lifecycle evaluation (Change 04).

Public surface: the reusable, flow-independent assessment service.
"""

from aws_lifecycle_inventory.lifecycle.assessment import assess_records

__all__ = ["assess_records"]
