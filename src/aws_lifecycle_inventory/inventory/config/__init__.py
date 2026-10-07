"""AWS Config inventory source (Change 03 evaluation)."""

from aws_lifecycle_inventory.inventory.config.config_source import (
    INVENTORY_SOURCE,
    ConfigAvailability,
    collect_from_config,
    detect_availability,
)

__all__ = [
    "INVENTORY_SOURCE",
    "ConfigAvailability",
    "collect_from_config",
    "detect_availability",
]
