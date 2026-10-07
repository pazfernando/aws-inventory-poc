# Spec Delta

## ADDED Requirements

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
