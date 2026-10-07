# Coverage Matrix — Direct-API Collectors

One row per supported version-bearing managed service. The "AWS Config
equivalence" column is the input to Change 03 (`evaluate-aws-config-inventory-source`).

The `collector` column is the registered collector `name`; a test
(`test_coverage_matrix.py`) asserts this list matches `default_collectors()` so
the matrix cannot silently drift from the code.

| collector | resource_type | AWS API (read-only) | Required IAM | Version field used | Example normalized output (software_name / version) | Known gaps | AWS Config equivalence (to measure in Change 03) |
|-----------|---------------|---------------------|--------------|--------------------|------------------------------------------------------|------------|--------------------------------------------------|
| lambda | AWS::Lambda::Function | `ListFunctions` | `lambda:ListFunctions` | `Runtime` (split name/version) | `python` / `3.12` | Container-image functions expose no `Runtime` → version empty | `AWS::Lambda::Function` recorded; runtime in config item |
| rds | AWS::RDS::DBInstance / DBCluster | `DescribeDBInstances`, `DescribeDBClusters` | `rds:DescribeDBInstances`, `rds:DescribeDBClusters` | `Engine` + `EngineVersion` | `postgres` / `15.4` | — | `AWS::RDS::DBInstance` / `DBCluster` recorded |
| elasticache | AWS::ElastiCache::CacheCluster | `DescribeCacheClusters` | `elasticache:DescribeCacheClusters` | `Engine` + `EngineVersion` | `redis` / `7.1` | Replication-group-only topologies may need `DescribeReplicationGroups` (deferred) | `AWS::ElastiCache::CacheCluster` recorded |
| eks | AWS::EKS::Cluster | `ListClusters`, `DescribeCluster` | `eks:ListClusters`, `eks:DescribeCluster` | `version` | `kubernetes` / `1.30` | — | `AWS::EKS::Cluster` recorded; version in config item |
| msk | AWS::MSK::Cluster | `ListClustersV2` | `kafka:ListClustersV2` | `Provisioned.CurrentBrokerSoftwareInfo.KafkaVersion` | `kafka` / `3.6.0` | Serverless clusters expose no Kafka version → empty | `AWS::MSK::Cluster` recorded (coverage to verify) |
| opensearch | AWS::OpenSearchService::Domain | `ListDomainNames`, `DescribeDomains` | `es:ListDomainNames`, `es:DescribeDomains` | `EngineVersion` (split name/version) | `opensearch` / `2.13` | — | `AWS::OpenSearch::Domain` recorded (naming differs) |
| emr | AWS::EMR::Cluster | `ListClusters`, `DescribeCluster` | `elasticmapreduce:ListClusters`, `elasticmapreduce:DescribeCluster` | `ReleaseLabel` | `emr` / `emr-7.1.0` | Release label is composite, not a bare semver | Partial — EMR config coverage to verify |
| glue | AWS::Glue::Job | `GetJobs` | `glue:GetJobs` | `GlueVersion` | `glue` / `4.0` | Jobs without `GlueVersion` set → empty | `AWS::Glue::Job` recorded (coverage to verify) |
| redshift | AWS::Redshift::Cluster | `DescribeClusters` | `redshift:DescribeClusters` | `ClusterVersion` (where exposed) | `redshift` / `1.0` | Version not always exposed → stays empty | `AWS::Redshift::Cluster` recorded |
| mq | AWS::AmazonMQ::Broker | `ListBrokers`, `DescribeBroker` | `mq:ListBrokers`, `mq:DescribeBroker` | `EngineType` + `EngineVersion` | `activemq` / `5.18` | — | `AWS::AmazonMQ::Broker` recorded (coverage to verify) |
| mwaa | AWS::MWAA::Environment | `ListEnvironments`, `GetEnvironment` | `airflow:ListEnvironments`, `airflow:GetEnvironment` | `AirflowVersion` | `airflow` / `2.9.2` | Not supported by moto → normalization tested via stub | Config support uncertain — to verify in Change 03 |

## Notes

- Every collector emits the same normalized `ResourceVersionRecord`; version fields
  that the AWS API does not expose stay explicitly empty (no invented versions).
- A failure in any single collector is isolated by the scan engine and reported as
  collector status without aborting the scan.
- The "AWS Config equivalence" column is a hypothesis to be measured, not an
  assumption; Change 03 validates it against these direct-API results.
