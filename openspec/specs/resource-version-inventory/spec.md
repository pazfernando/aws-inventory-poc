# resource-version-inventory Specification

## Purpose
Defines read-only discovery of version-bearing AWS managed resources via direct
AWS service APIs, emitting normalized version records for one account and region.

## Requirements

### Requirement: Read-only discovery
The system SHALL discover resources using only read-only AWS API calls and SHALL
NOT perform any create, update, or delete operation against scanned workloads.

#### Scenario: Only read APIs are invoked
- **WHEN** a scan runs against an account and region
- **THEN** every AWS API call issued is a read/describe/list operation
- **AND** no mutating API call is issued against any scanned resource

### Requirement: Baseline collector coverage
The system SHALL provide isolated collectors for AWS Lambda runtime, Amazon RDS
and Aurora engine/version, Amazon ElastiCache engine/version, and Amazon EKS
Kubernetes version, each emitting normalized records.

#### Scenario: Lambda runtime discovered
- **WHEN** the account contains a Lambda function with runtime `python3.12`
- **THEN** a record is produced with `resource_type=AWS::Lambda::Function`,
  `software_name=python`, and `version=3.12`

#### Scenario: RDS engine and version discovered
- **WHEN** the account contains an RDS instance running `postgres` `15.4`
- **THEN** a record is produced with `software_name=postgres` and `version=15.4`

#### Scenario: EKS Kubernetes version discovered
- **WHEN** the account contains an EKS cluster at Kubernetes `1.30`
- **THEN** a record is produced with `software_name=kubernetes` and `version=1.30`

### Requirement: No invented versions
A collector SHALL NOT infer or fabricate a version the AWS API does not expose;
when a version is unavailable the record SHALL leave `version` explicitly empty.

#### Scenario: Missing version stays empty
- **WHEN** a discovered resource exposes no version field from its AWS API
- **THEN** the emitted record has an empty `version` value
- **AND** no guessed or defaulted version is substituted

### Requirement: Collector isolation and partial failure tolerance
A failure in one collector SHALL NOT abort the overall scan; the system SHALL
continue other collectors and surface the failure as collector status.

#### Scenario: One collector fails, scan continues
- **WHEN** the RDS collector raises an error during a scan
- **THEN** the Lambda, ElastiCache, and EKS collectors still run and emit records
- **AND** the RDS failure is reported as a failed collector status
- **AND** the process exits without discarding successfully collected records

### Requirement: CSV output
The system SHALL write discovered records to a CSV file whose columns match the
normalized record schema.

#### Scenario: CSV written with baseline columns
- **WHEN** a scan completes with at least one discovered record
- **THEN** a CSV file is produced containing a header row and one row per record
  using the normalized baseline columns

### Requirement: Extended managed-service collector coverage
The system SHALL provide isolated direct-API collectors for Amazon MSK, Amazon
OpenSearch Service, Amazon EMR, AWS Glue Jobs, Amazon Redshift, Amazon MQ, and
Amazon MWAA, each emitting the normalized record schema.

#### Scenario: MSK Kafka version discovered
- **WHEN** the account contains an MSK cluster running Kafka `3.6.0`
- **THEN** a record is produced with `software_name=kafka` and `version=3.6.0`

#### Scenario: OpenSearch engine/version discovered
- **WHEN** the account contains an OpenSearch domain at engine version `OpenSearch_2.13`
- **THEN** a record is produced capturing the engine and `version=2.13`

#### Scenario: EMR release label discovered
- **WHEN** the account contains an EMR cluster with release label `emr-7.1.0`
- **THEN** a record is produced capturing the release label as the version

#### Scenario: Glue job version discovered
- **WHEN** the account contains a Glue job with Glue version `4.0`
- **THEN** a record is produced with `software_name=glue` and `version=4.0`

#### Scenario: MQ broker engine/version discovered
- **WHEN** the account contains an Amazon MQ broker running `ActiveMQ` `5.18`
- **THEN** a record is produced capturing the broker engine and `version=5.18`

#### Scenario: MWAA Airflow version discovered
- **WHEN** the account contains an MWAA environment running Airflow `2.9.2`
- **THEN** a record is produced with `software_name=airflow` and `version=2.9.2`

### Requirement: Extended collectors preserve the inventory contract
Each extended collector SHALL emit the same normalized schema, SHALL NOT invent a
version the AWS API does not expose, and a failure in any extended collector SHALL
NOT abort the overall scan.

#### Scenario: Redshift version absent stays explicit
- **WHEN** a Redshift cluster exposes no release/version metadata via its API
- **THEN** the emitted record leaves `version` empty rather than guessing

#### Scenario: Extended collector failure is isolated
- **WHEN** the MWAA collector raises an error during a scan
- **THEN** all other collectors still run and the MWAA failure is reported as
  collector status

### Requirement: Coverage matrix
The change SHALL produce a coverage matrix documenting, per supported service, the
AWS API used, required IAM permissions, the version field used, an example
normalized output, known gaps, and whether AWS Config exposes equivalent data.

#### Scenario: Matrix covers every supported service
- **WHEN** the coverage matrix is produced
- **THEN** it contains one row per supported managed-service family
- **AND** each row records API, IAM permissions, version field, example output,
  known gaps, and AWS Config equivalence
