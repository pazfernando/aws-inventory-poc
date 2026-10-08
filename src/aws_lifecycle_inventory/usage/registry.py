"""Metric registry: maps a resource_type to the CloudWatch metric(s) whose
activity signals usage. Resource types with no entry have no meaningful usage
metric and are reported NO_METRIC (never a false IDLE).

Each spec lists one or more (namespace, metric_name) pairs whose values are summed
into a single activity value, the statistic to request, and the dimension name
whose value is the record's ``resource_id``.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricSpec:
    namespace: str
    metric_names: tuple[str, ...]
    statistic: str  # Sum | Average | Maximum
    dimension_name: str
    # Human-readable source label stored on the record.
    source: str


# resource_type -> MetricSpec. Everything not listed -> NO_METRIC.
METRIC_REGISTRY: dict[str, MetricSpec] = {
    "AWS::Lambda::Function": MetricSpec(
        namespace="AWS/Lambda",
        metric_names=("Invocations",),
        statistic="Sum",
        dimension_name="FunctionName",
        source="cloudwatch:AWS/Lambda/Invocations",
    ),
    "AWS::DynamoDB::Table": MetricSpec(
        namespace="AWS/DynamoDB",
        metric_names=("ConsumedReadCapacityUnits", "ConsumedWriteCapacityUnits"),
        statistic="Sum",
        dimension_name="TableName",
        source="cloudwatch:AWS/DynamoDB/ConsumedCapacity",
    ),
    "AWS::RDS::DBInstance": MetricSpec(
        namespace="AWS/RDS",
        metric_names=("DatabaseConnections",),
        statistic="Sum",
        dimension_name="DBInstanceIdentifier",
        source="cloudwatch:AWS/RDS/DatabaseConnections",
    ),
    "AWS::RDS::DBCluster": MetricSpec(
        namespace="AWS/RDS",
        metric_names=("DatabaseConnections",),
        statistic="Sum",
        dimension_name="DBClusterIdentifier",
        source="cloudwatch:AWS/RDS/DatabaseConnections",
    ),
    "AWS::SQS::Queue": MetricSpec(
        namespace="AWS/SQS",
        metric_names=("NumberOfMessagesSent",),
        statistic="Sum",
        dimension_name="QueueName",
        source="cloudwatch:AWS/SQS/NumberOfMessagesSent",
    ),
    "AWS::SNS::Topic": MetricSpec(
        namespace="AWS/SNS",
        metric_names=("NumberOfMessagesPublished",),
        statistic="Sum",
        dimension_name="TopicName",
        source="cloudwatch:AWS/SNS/NumberOfMessagesPublished",
    ),
}


def metric_spec_for(resource_type: str) -> MetricSpec | None:
    """Return the MetricSpec for a resource type, or None (-> NO_METRIC)."""
    return METRIC_REGISTRY.get(resource_type)
