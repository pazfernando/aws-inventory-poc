"""Mapping tables for the EndOfLife lifecycle provider (Change endoflife).

Maps our normalized identity (software_name + version, derived from resource_type)
to endoflife.date products and the `cycle` key used to look up an entry.

This module owns the knowledge of WHICH endoflife products we track and HOW to
turn a record into a (product, cycle) lookup. The provider and the refresh
routine both use it, so the set of products stays in one place.
"""

from __future__ import annotations

from aws_lifecycle_inventory.models import ResourceVersionRecord

# endoflife.date products we fetch and bake into the seed.
ENDOFLIFE_PRODUCTS: tuple[str, ...] = (
    "aws-lambda",
    "amazon-rds-postgresql",
    "amazon-rds-mysql",
    "amazon-rds-mariadb",
    "amazon-eks",
    "amazon-elasticache-redis",
    "opensearch",
)

# Base URL for the public endoflife.date API.
API_BASE = "https://endoflife.date/api"


def _major(version: str) -> str:
    """Return the major component of a version (e.g. 15.4 -> 15, 7.1 -> 7)."""
    return version.split(".", 1)[0] if version else ""


def lookup_keys(record: ResourceVersionRecord) -> tuple[str, str] | None:
    """Return (endoflife_product, cycle) for a record, or None if unmapped.

    The cycle is matched against the endoflife entry's ``cycle`` field. Different
    products expose cycles at different granularity:
      - Lambda: the runtime cycle is exactly our runtime string (e.g. python3.10)
      - RDS/Aurora engines, EKS, ElastiCache, OpenSearch: major version cycle
    """
    rtype = record.resource_type
    name = record.software_name
    version = record.version

    # Lambda: cycle equals the raw runtime (e.g. "python3.10", "nodejs20.x").
    if rtype == "AWS::Lambda::Function":
        runtime = f"{name}{version}" if name and version else ""
        if name and version:
            # go1.x / nodejs20.x keep an ".x"; python3.10 is name+version directly.
            return "aws-lambda", runtime
        return None

    if rtype in ("AWS::RDS::DBInstance", "AWS::RDS::DBCluster"):
        engine = (name or "").lower()
        if "postgres" in engine:
            return "amazon-rds-postgresql", _major(version)
        if "mariadb" in engine:
            return "amazon-rds-mariadb", _major(version)
        if "mysql" in engine or "aurora-mysql" in engine or engine == "aurora":
            return "amazon-rds-mysql", _major(version)
        if "aurora-postgresql" in engine:
            return "amazon-rds-postgresql", _major(version)
        return None

    if rtype == "AWS::EKS::Cluster":
        # EKS cycle is the k8s major.minor (e.g. "1.30").
        parts = version.split(".")
        if len(parts) >= 2:
            return "amazon-eks", f"{parts[0]}.{parts[1]}"
        return None

    if rtype == "AWS::ElastiCache::CacheCluster":
        if (name or "").lower() == "redis":
            return "amazon-elasticache-redis", _major(version)
        return None

    if rtype == "AWS::OpenSearchService::Domain":
        # endoflife "opensearch" cycles are major versions (e.g. "2").
        if (name or "").lower() == "opensearch":
            return "opensearch", _major(version)
        return None

    return None
