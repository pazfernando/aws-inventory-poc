# Design

## Context

Change 04 defined the `LifecycleProvider` abstraction and curated provider. See
`proposal.md` for motivation. Health is an additional provider; discovery is
untouched. The AWS Health API requires Business/Enterprise Support and is
region-specific in its endpoint behavior.

## Goals / Non-Goals

**Goals:**
- An `aws_health.py` provider implementing `match(record)` using Planned Lifecycle
  Events and ARN-based matching.
- Preserved, auditable Health evidence and graceful degradation when Health is
  unavailable.

**Non-Goals:**
- Replacing curated data; both coexist with explicit provenance.
- Organization-level Health visibility (noted as a Change 07 interaction).

## Decisions

- **Prefetch events once per scan, then match in-memory** via an ARN index, rather
  than calling Health per record. Rationale: Health list calls are coarse-grained;
  per-record calls would be slow and rate-limited.
- **Precedence vs curated provider**: when both Health and curated match a record,
  Health (AWS-authoritative) supplies the conclusion while curated provenance is
  preserved, never silently discarded. Alternative (curated wins) rejected because
  Health is account-specific and authoritative.
- **Availability detection is best-effort**: an access-denied/unsupported response
  degrades the provider to "unavailable" and the scan proceeds. This enforces the
  non-fatal rule.
- **Matching only on reliable identifiers** (ARN/identifier equality). Fuzzy
  matching is excluded to avoid false lifecycle conclusions.

## Risks / Trade-offs

- [Health API access denied in many accounts] → non-fatal path is first-class and
  tested with an unavailable-Health scenario.
- [Affected-entity ARNs not always matching inventory ARNs] → match only on
  reliable equality; unmatched events annotate nothing rather than guess.
- [Absence misread as supported] → explicit spec + test that no-event never yields
  SUPPORTED.
