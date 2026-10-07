# Design

## Context

Since Change 01 the engine was designed to accept a session and scope so it could
run outside the CLI. See `proposal.md` for motivation. This change adds the Lambda
entrypoint and S3 sink only.

## Goals / Non-Goals

**Goals:**
- A thin Lambda handler that parses an event scope, calls `run_scan()`, and writes
  the CSV to S3 with a deterministic timestamped key.
- Demonstrated CLI/Lambda output equivalence.

**Non-Goals:**
- New collectors, providers, or record-model changes.
- Scheduling/infra (EventBridge, Terraform) beyond what verification needs —
  handled by deployment config, not this capability's logic.

## Decisions

- **Handler is an adapter, not logic**: event → scope → `run_scan()` → CSV bytes →
  S3. Rationale: enforces the single-engine principle and keeps semantics
  identical to the CLI. Alternative (Lambda-specific scan path) rejected outright.
- **CSV written to a buffer then `s3:PutObject`**, avoiding Lambda `/tmp` reliance
  and keeping the writer shared with the CLI.
- **Deterministic key**: `prefix/<timestamp>/<scope-hash>.csv` so reruns are
  traceable and non-colliding. Alternative (random key) rejected for poor
  traceability.
- **Reuse the CLI output writer** so column order/semantics cannot diverge.

## Risks / Trade-offs

- [Lambda time/memory limits on large org scans] → scope input allows chunking by
  account/region; long scans can be partitioned across invocations.
- [Dependency packaging size] → use a layer or slim packaging; verify cold-start
  import succeeds.
- [Divergence between CLI and Lambda] → an equivalence test over the same scope
  guards the single-engine guarantee.
