# Design

## Context

Change 01 established the `Collector` protocol, the scan engine, and the
normalized record + CSV contract. See `proposal.md` for motivation. This change
only adds more collectors; it introduces no new architecture.

## Goals / Non-Goals

**Goals:**
- Seven additional isolated collectors reusing the existing `Collector` protocol.
- A coverage matrix document that doubles as the input to the Change 03 Config
  spike (the "does Config expose this?" column).

**Non-Goals:**
- Any change to the record model, CSV writer, or scan engine.
- Lifecycle evaluation, Config querying, or multi-region/account scope.

## Decisions

- **One module per service** under `inventory/direct_api/` mirroring Change 01, so
  each is independently testable with moto and can fail in isolation.
- **Version field chosen per service and documented in the matrix**: e.g. EMR uses
  the release label verbatim as the version; Redshift records version only where
  the API exposes it, otherwise empty. This keeps "no invented versions" auditable.
- **Coverage matrix as a committed markdown/CSV artifact** in the change folder so
  Change 03 can consume the Config-equivalence column directly.

## Risks / Trade-offs

- [Service APIs differ in how/if they expose version] → document the exact field
  per service in the matrix; leave empty when absent instead of normalizing guesses.
- [moto coverage gaps for newer services (MSK/MWAA/OpenSearch)] → where moto lacks
  support, test the normalization logic against captured API-shape fixtures.
- [Matrix drift from code] → generate/verify the matrix rows against the actual
  collectors in tests where feasible.
