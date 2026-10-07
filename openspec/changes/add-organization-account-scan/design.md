# Design

## Context

Change 06 added multi-region scanning around the shared engine. See `proposal.md`
for motivation. This change wraps that in account iteration via STS AssumeRole and
applies the Change 03 source-strategy decision at org scale.

## Goals / Non-Goals

**Goals:**
- Assume-role-based per-account sessions feeding the existing multi-region engine.
- Account isolation, account provenance, and an account-aware execution summary.
- Apply the recorded Config decision to choose fan-out vs aggregator.

**Non-Goals:**
- Implementing a Config Aggregator unless Change 03 selected `HYBRID`/
  `CONFIG_PRIMARY`; otherwise only direct-API fan-out is built.
- Lambda packaging (Change 09).

## Decisions

- **Session factory per account**: assume role → build a session → pass to the
  existing region loop. Rationale: reuses Changes 01/06 unchanged; account access
  is just a different session source.
- **Account iteration isolates failures like regions do**: an un-assumable role is
  a reported account status, never an abort.
- **Source strategy read from the Change 03 decision artifact**, not hard-coded, so
  the org-wide path matches the measured conclusion.
- **Org-level Health vs per-account Health evaluated**, defaulting to per-account
  Health access to stay within the non-fatal provider model from Change 05.

## Risks / Trade-offs

- [AssumeRole misconfiguration across many accounts] → clear per-account
  inaccessible status; scan proceeds and reports which accounts were skipped.
- [Aggregator vs fan-out cost/complexity] → governed by the Change 03 decision;
  this change does not re-litigate it, only applies it.
- [Credential/session sprawl] → short-lived assumed sessions scoped per account.

## Open Questions

- Account list source (static config vs AWS Organizations `ListAccounts`) — can be
  decided at implementation without changing specs; both feed the same iterator.
