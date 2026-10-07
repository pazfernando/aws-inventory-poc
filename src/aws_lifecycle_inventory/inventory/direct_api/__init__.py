"""Direct-API per-service collectors and the default collector registry."""

from __future__ import annotations

from aws_lifecycle_inventory.inventory.direct_api.eks_collector import EKSCollector
from aws_lifecycle_inventory.inventory.direct_api.elasticache_collector import (
    ElastiCacheCollector,
)
from aws_lifecycle_inventory.inventory.direct_api.emr_collector import EMRCollector
from aws_lifecycle_inventory.inventory.direct_api.glue_collector import GlueJobsCollector
from aws_lifecycle_inventory.inventory.direct_api.lambda_collector import LambdaCollector
from aws_lifecycle_inventory.inventory.direct_api.mq_collector import AmazonMQCollector
from aws_lifecycle_inventory.inventory.direct_api.msk_collector import MSKCollector
from aws_lifecycle_inventory.inventory.direct_api.mwaa_collector import MWAACollector
from aws_lifecycle_inventory.inventory.direct_api.opensearch_collector import (
    OpenSearchCollector,
)
from aws_lifecycle_inventory.inventory.direct_api.rds_collector import RDSCollector
from aws_lifecycle_inventory.inventory.direct_api.redshift_collector import (
    RedshiftCollector,
)


def default_collectors() -> list:
    """The baseline (Changes 01-02) set of direct-API collectors."""
    return [
        # Change 01 baseline
        LambdaCollector(),
        RDSCollector(),
        ElastiCacheCollector(),
        EKSCollector(),
        # Change 02 expanded coverage
        MSKCollector(),
        OpenSearchCollector(),
        EMRCollector(),
        GlueJobsCollector(),
        RedshiftCollector(),
        AmazonMQCollector(),
        MWAACollector(),
    ]


__all__ = [
    "AmazonMQCollector",
    "EKSCollector",
    "ElastiCacheCollector",
    "EMRCollector",
    "GlueJobsCollector",
    "LambdaCollector",
    "MSKCollector",
    "MWAACollector",
    "OpenSearchCollector",
    "RDSCollector",
    "RedshiftCollector",
    "default_collectors",
]
