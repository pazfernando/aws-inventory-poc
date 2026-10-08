"""Resource types that carry no software version to evaluate for lifecycle.

These are discovered for presence (general inventory) only. The lifecycle
evaluator assigns ``NOT_APPLICABLE`` to records of these types without consulting
any provider, keeping ``NOT_APPLICABLE`` distinct from ``UNKNOWN`` (absence of
evidence) and from ``SUPPORTED``.
"""

from __future__ import annotations

NON_VERSION_BEARING_RESOURCE_TYPES: frozenset[str] = frozenset(
    {
        "AWS::EC2::Instance",
        "AWS::EC2::VPC",
        "AWS::DynamoDB::Table",
        "AWS::SNS::Topic",
        "AWS::SQS::Queue",
        "AWS::EFS::FileSystem",
        "AWS::CloudFormation::Stack",
        "AWS::CloudFormation::StackSet",
        "AWS::Route53::HostedZone",
    }
)
