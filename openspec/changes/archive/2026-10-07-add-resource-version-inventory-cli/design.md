# Design

## Context

Greenfield. See `proposal.md` for motivation. This is the foundation change: it
establishes the normalized record model, the collector interface, and the scan
engine that every later change (Config, lifecycle, Health, multi-region,
multi-account, SSM, Lambda) builds on. Constraints come from the project
principles: read-only, no invented versions, partial-failure tolerance, one
shared record model, and a CLI engine reusable from Lambda.

## Goals / Non-Goals

**Goals:**
- A `ResourceVersionRecord` Pydantic model and a stable CSV writer.
- A `Collector` protocol so each service collector is isolated and independently
  testable with moto.
- An `orchestration.run_scan()` engine, called by `cli.py`, that aggregates
  records and per-collector status.

**Non-Goals:**
- Lifecycle/deprecation evaluation (Change 04).
- AWS Config as a source (Change 03).
- Multi-region (Change 06), multi-account (Change 07), Lambda handler (Change 09).
- Operational CSV columns beyond collector status minimum; full operational
  column set is formalized with lifecycle work.

## Decisions

- **Pydantic model over dataclass**: aligns with team convention and gives
  validation/serialization for free. Alternative (plain dataclass) rejected for
  weaker validation.
- **Collector protocol returning `(records, collector_status)`**: keeps isolation
  explicit and makes partial failure a first-class return value rather than an
  exception that could abort the scan. The engine wraps each collector call in a
  try/except as a backstop.
- **boto3 session/profile passed into the engine**: enables later reuse from
  Lambda (role-based session) without changing collectors. Region is a single
  value here; the engine signature anticipates a region list in Change 06.
- **CSV writer owns column order centrally**: one place defines the baseline
  columns so later changes append columns without touching collectors.
- **Version normalization lives in each collector**: e.g. Lambda `python3.12` →
  `software_name=python`, `version=3.12`. Collectors never invent a version;
  missing stays empty.

## Risks / Trade-offs

- [AWS API shape drift / pagination] → use boto3 paginators; cover with moto.
- [Inconsistent version formats across services] → normalize per collector and
  assert via fixtures; keep raw-to-normalized mapping documented in the collector.
- [Silent partial coverage looks like "no resources"] → always emit collector
  status so a failed/empty collector is distinguishable from an empty account.
