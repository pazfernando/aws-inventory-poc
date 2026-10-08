"""Direct-API per-service collectors and the default collector registry."""

from __future__ import annotations

from aws_lifecycle_inventory.inventory.direct_api.cloudformation_collector import (
    CloudFormationCollector,
)
from aws_lifecycle_inventory.inventory.direct_api.dynamodb_collector import (
    DynamoDBCollector,
)
from aws_lifecycle_inventory.inventory.direct_api.ec2_collector import (
    EC2InstanceCollector,
)
from aws_lifecycle_inventory.inventory.direct_api.efs_collector import EFSCollector
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
from aws_lifecycle_inventory.inventory.direct_api.route53_collector import (
    Route53Collector,
)
from aws_lifecycle_inventory.inventory.direct_api.sns_collector import SNSCollector
from aws_lifecycle_inventory.inventory.direct_api.sqs_collector import SQSCollector
from aws_lifecycle_inventory.inventory.direct_api.vpc_collector import VPCCollector


def default_collectors() -> list:
    """The baseline set of direct-API collectors.

    Version-bearing collectors (Changes 01-02) plus non-version-bearing general
    inventory collectors (add-general-resource-inventory).
    """
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
        # add-general-resource-inventory: non-version-bearing resources
        EC2InstanceCollector(),
        VPCCollector(),
        DynamoDBCollector(),
        SNSCollector(),
        SQSCollector(),
        EFSCollector(),
        CloudFormationCollector(),
        Route53Collector(),
    ]


__all__ = [
    "AmazonMQCollector",
    "CloudFormationCollector",
    "DynamoDBCollector",
    "EC2InstanceCollector",
    "EFSCollector",
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
    "Route53Collector",
    "SNSCollector",
    "SQSCollector",
    "VPCCollector",
    "default_collectors",
]
