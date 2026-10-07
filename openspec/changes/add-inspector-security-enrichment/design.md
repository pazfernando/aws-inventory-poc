# Design

## Context

Lifecycle/deprecation and vulnerability/CVE management are separate concerns. See
`proposal.md` for motivation. This change is optional and only built if CVE
management becomes a requirement; it must not leak into lifecycle fields.

## Goals / Non-Goals

**Goals:**
- An optional, default-off enrichment step that maps Inspector findings onto
  discovered records via resource identity.
- Additive security columns with a clean separation from lifecycle fields.

**Non-Goals:**
- Using Inspector as an inventory source (inventory stays with direct APIs/Config/
  SSM).
- Any modification of lifecycle status or EOL fields.

## Decisions

- **Separate enrichment pass after lifecycle evaluation**: it reads records and
  writes only security_* fields. Rationale: structurally guarantees lifecycle
  fields are not touched. Alternative (merging into lifecycle evaluation) rejected
  as it risks conflating the two concerns.
- **Default disabled, explicit opt-in flag**: keeps the baseline tool free of an
  Inspector dependency.
- **Match findings to records by resource ARN/identity**, aggregating counts by
  severity. Unmatched findings do not alter any record.
- **`security_source` records provenance** just as lifecycle/inventory sources do.

## Risks / Trade-offs

- [Concern creep: security bleeding into lifecycle] → enforced by a separate pass
  and a test asserting lifecycle fields are unchanged by enrichment.
- [Inspector not enabled/available] → enrichment is optional and degrades to no
  security fields, never failing the scan.
- [Finding-to-resource mapping gaps] → match only on reliable identity; leave
  security fields empty when unmatched rather than guessing.
