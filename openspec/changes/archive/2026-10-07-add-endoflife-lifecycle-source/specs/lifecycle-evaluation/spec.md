# Spec Delta

## ADDED Requirements

### Requirement: Provider precedence order
When multiple lifecycle providers can match a record, evaluation SHALL consult
them in a fixed precedence order — AWS Health, then EndOfLife — and the first
match SHALL supply the conclusion while all other matches are preserved as
provenance.

#### Scenario: EndOfLife used when Health unavailable
- **WHEN** AWS Health returns no evidence for a record but EndOfLife does
- **THEN** the EndOfLife evidence supplies the lifecycle conclusion

#### Scenario: Health outranks EndOfLife
- **WHEN** both AWS Health and EndOfLife return evidence for the same record
- **THEN** AWS Health supplies the conclusion
- **AND** the EndOfLife match is preserved as provenance, not discarded

#### Scenario: No provider matches yields UNKNOWN
- **WHEN** neither AWS Health nor EndOfLife matches a record
- **THEN** the record's lifecycle status is UNKNOWN

## REMOVED Requirements

### Requirement: Curated provider
**Reason**: Replaced by the EndOfLife provider, which is broad and independently
verifiable (each entry cites an official source link). The hand-written curated
seed of a few entries was unverifiable and is retired.
**Migration**: Lifecycle contingency evidence now comes from the
`endoflife-lifecycle-source` capability. No action is required by consumers; the
curated provider and its `curated_data.yaml` are removed.
