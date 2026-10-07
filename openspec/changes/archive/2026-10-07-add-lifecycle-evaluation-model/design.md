# Design

## Context

Inventory (Changes 01-02) produces normalized records. See `proposal.md` for
motivation. This change adds a separate evaluation layer so discovery and
deprecation policy never mix.

## Goals / Non-Goals

**Goals:**
- A `LifecycleProvider` protocol and an `evaluator.py` that runs records through
  ordered providers and derives status + evidence.
- A curated provider as the first evidence source.
- Lifecycle fields on the record and CSV.

**Non-Goals:**
- AWS Health as a provider (Change 05).
- Vulnerability/CVE semantics (Change 10) — lifecycle fields are not security
  fields.

## Decisions

- **Status derived from EOL date + provider assertion**: the evaluator maps
  days-to-EOL into the `EOL_*` buckets; a provider may also assert `UNSUPPORTED`
  directly. Rationale: keeps bucket thresholds in one place while letting
  providers override with authoritative statements.
- **Provider order with provenance, no silent override**: the first provider that
  matches supplies evidence; multiple matches preserve provenance for Change 05's
  Health-vs-curated precedence. Alternative (merge/average) rejected — it would
  fabricate conclusions.
- **`UNKNOWN` is the default, not an error**: a record with no match is a valid
  result and must be visibly distinct from `SUPPORTED` in the CSV.
- **Curated data as versioned local file** (e.g. YAML/JSON) keyed by
  software_name + version range, each entry carrying an `evidence_id`.

## Risks / Trade-offs

- [Curated data goes stale] → every entry carries source/evidence id and an EOL
  date; staleness is auditable and Change 05 adds an AWS-authoritative source.
- [Version matching ambiguity (e.g. `3.11` vs `3.11.4`)] → match on normalized
  version semantics defined per software_name; cover with fixtures.
- [Confusing UNKNOWN with SUPPORTED] → explicit CSV serialization scenario and a
  test asserting the two are distinguishable.
