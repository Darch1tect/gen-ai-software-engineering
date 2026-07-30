# Research: Virtual Card Lifecycle Management

**Purpose**: Resolve the architectural/pattern decisions implied by spec.md's Technical
Context, so `data-model.md`, `contracts/`, and the eventual `tasks.md` can be written without
guessing. Every decision below is **hypothetical** per the project constitution
(documentation-only phase) — it constrains a future implementation without being one.

## 1. Audit trail storage pattern

- **Decision**: Model the audit trail as a separate, physically append-only event store
  (write-once, no update/delete API surface at all), distinct from the mutable operational
  store holding current card/limit/transaction state.
- **Rationale**: Principle II (Auditability & Regulatory Traceability) and FR-028 require that
  no update/delete path exist for audit records. Enforcing this by *not building* the
  update/delete capability (rather than building it and restricting it with permissions) is a
  stronger, simpler guarantee — there is nothing to misconfigure or bypass under privileged
  access, which regulators and auditors specifically test for.
- **Alternatives considered**: (a) Same table as operational state with a `deleted_at`/soft-delete
  convention — rejected because soft-delete still exposes an update/delete code path that could
  be misused or buggy. (b) Database triggers blocking UPDATE/DELETE on an audit table in the
  same store as operational data — rejected as a fallback-only option; simpler to keep the
  stores physically separate so a single connection/credential compromise can't touch both.

## 2. Idempotency key mechanism

- **Decision**: Every state-changing request (create, freeze, unfreeze, limit update, fraud
  flag) carries a client-supplied idempotency key; the system persists a dedupe record
  (key → resulting entity reference + outcome) and short-circuits repeats of the same key to
  return the original outcome rather than re-executing the operation.
- **Rationale**: FR-003/FR-006/FR-023 and edge cases E1/E9 require repeat-safe writes.
  Client-supplied keys (vs. server-inferred natural-key dedup) handle the general case cleanly,
  including operations like "freeze" that don't have a natural unique business key to dedupe
  on beyond "current state is already Frozen" (which FR-006 also covers as a *separate*,
  state-based idempotency rule for convergent operations).
- **Alternatives considered**: Natural-key dedup only (e.g., treat "freeze this card" as
  inherently idempotent by state) — rejected as the sole mechanism because it doesn't protect
  card *creation*, which has no pre-existing natural key to compare against; the two mechanisms
  are complementary, not substitutes.

## 3. Concurrency conflict resolution for card state

- **Decision**: Optimistic concurrency control — every card record carries a version token;
  a write must supply the version it read, and a write against a stale version is rejected
  with an explicit conflict response (not silently applied, not silently dropped) per FR-008.
  The caller is expected to re-read and retry.
- **Rationale**: Freeze/unfreeze and limit-update requests are infrequent per card relative to
  read traffic, so optimistic concurrency avoids the throughput cost of pessimistic locking
  while still giving the deterministic, explicit-conflict outcome Principle III requires (edge
  case E2).
- **Alternatives considered**: Pessimistic row locking — rejected as unnecessary overhead for a
  low-write-contention entity; a well-suited alternative for something like the monthly
  aggregate running total instead (see #4), where contention is higher. Last-write-wins with no
  conflict signal — rejected outright because it fails Principle III's explicit requirement
  that a losing request MUST receive an explicit conflict/outcome response.

## 4. Monthly aggregate limit tracking and reset

- **Decision**: Track the monthly aggregate running total as an incrementally-maintained
  counter scoped to `(card_id, calendar_month)`, updated atomically at authorization time
  (not recomputed from the full transaction ledger on every read). A new counter row is
  implicitly "created" the first time a given calendar month is touched, which is how the
  FR-015 reset is achieved — there is no explicit "reset job" to run or fail.
- **Rationale**: Recomputing the sum from the transaction ledger on every authorization would
  not scale to the SC-002/SC-003 latency budgets under concurrent load, and a scheduled
  "reset job" is an extra moving part that can itself fail or run late, becoming a compliance
  and reliability risk. Scoping the counter key by calendar month sidesteps that entirely.
- **Alternatives considered**: A scheduled batch job that zeroes counters at month boundary —
  rejected because a missed/delayed run would silently misstate available limit, and per edge
  case E14 the reset must never require an explicit action or be able to "not happen."

## 5. Structured logging and correlation ID propagation

- **Decision**: A correlation ID is generated (or accepted, if propagated from an upstream
  client/gateway) at the start of every request and threaded through every log/event emitted
  for that request, per FR-029. Log/events are structured (field-based, not free-text) so
  correlation ID, actor role, action, outcome, and latency are independently queryable.
- **Rationale**: SC-011 requires reconstructing a full request lifecycle from the correlation
  ID alone; free-text logs would make that unreliable. This is an operational concern
  deliberately kept separate from the audit trail (#1) per Principle IV, so ops/support tooling
  doesn't need audit-trail-level access just to debug a request.
- **Alternatives considered**: Deriving observability entirely from the audit trail — rejected
  because the audit trail intentionally excludes non-state-changing operations (e.g., a
  successful read), which support/ops still need visibility into for debugging.

## 6. PAN/CVV masking and vault boundary

- **Decision**: Full PAN/CVV are held only by an external, out-of-scope vault/tokenization
  provider (per spec.md Assumptions); every entity and view inside this feature's boundary
  references a card by an opaque, non-guessable card ID and, where a human-readable hint is
  needed, a masked PAN (last 4 digits only).
- **Rationale**: Directly implements Principle I and FR-026; keeping the vault entirely outside
  this feature's data model is the simplest way to guarantee Tier-1 data can never leak through
  a code path this feature owns, because this feature's model never holds it in the first
  place.
- **Alternatives considered**: Storing an encrypted full PAN within this feature's own data
  store with access-controlled decryption — rejected as strictly higher risk and higher PCI
  DSS scope than delegating custody to a dedicated vault provider.

## 7. Permission scope model for ops/compliance/fraud users

- **Decision**: Role-based access with an explicit per-user scope boundary (e.g., assigned
  customer segment/case list), not a single global "internal user" role. A role determines
  *capability class* (view-only vs. fraud-action-capable per FR-024/FR-025); the scope boundary
  determines *which customers* that capability may be exercised against.
- **Rationale**: FR-019/FR-020 require both a capability check and a scope check to be denied
  independently and auditably (E8); collapsing these into one flag would make it impossible to
  express "can raise fraud flags, but only for customers in my assigned queue."
- **Alternatives considered**: Attribute-based access control (ABAC) with a general policy
  engine — noted as a reasonable future evolution but rejected as the baseline model here,
  since the spec's access rules (view-scope + fraud-action-capable) are simple enough that a
  general policy engine would be premature complexity for this feature's stated scope.

## 8. Transaction history pagination

- **Decision**: Cursor-based pagination (opaque cursor referencing a timestamp+ID position),
  not offset-based, bounded at 50 items/page per SC-005.
- **Rationale**: FR-018 requires pagination to remain stable under concurrent new-transaction
  arrivals; offset-based pagination shifts under insert-heavy conditions (a new transaction
  arriving can shift every subsequent page's offset), which cursor-based pagination avoids by
  anchoring to a stable position marker instead of a row count.
- **Alternatives considered**: Offset/limit pagination — rejected specifically because
  reverse-chronological transaction lists are insert-heavy at the head, making offset drift the
  common case rather than an edge case.

## 9. Aggregate cross-action-type rate limiting (added round 3, security checklist CHK032)

- **Decision**: Layer a second, aggregate rate-limit counter (`scope = aggregate` in the Rate
  Limit Counter entity) on top of the per-action-type counters from decision #10 below, summing
  create + freeze/unfreeze + limit-update requests per customer per window.
- **Rationale**: Independent per-action-type limits (FR-031) can be evaded by an attacker who
  spreads requests across action types to stay under each individual ceiling. An aggregate
  ceiling closes that gap cheaply — one more counter, no architectural change.
- **Alternatives considered**: A single combined limit replacing the per-action-type limits —
  rejected because it would re-introduce the original problem FR-031 was designed to solve
  (e.g., a legitimate freeze burst competing with a customer's own limit-update budget).

## 10. Step-up/re-authentication for high-risk actions (added round 3, security checklist CHK002)

- **Decision**: Treat baseline authentication as an out-of-scope system boundary (same pattern
  as KYC/vault/processor), but require a request-time `step_up_timestamp` for high-risk actions
  (freeze, unfreeze, limit update, fraud flag) that this feature validates is no older than 5
  minutes (SC-013) — not a persisted entity, a per-request check (data-model.md § Step-Up
  Authentication Signal).
- **Rationale**: The spec had no authentication requirement at all prior to this round — a real
  gap for a feature whose whole purpose is controlling money movement. A full authentication
  architecture would be scope creep for a virtual-card-lifecycle spec; requiring a freshness
  signal on high-risk actions specifically closes the highest-risk gap without that creep.
- **Alternatives considered**: Requiring step-up on every action including reads — rejected as
  unnecessary friction for `CreateCard`/`ListTransactions`, which don't themselves move money or
  change card state in a way that benefits from re-authentication.

## 11. Dependency integrity fail-closed (added round 3, security checklist CHK022)

- **Decision**: Extend the dependency-guard pattern (decision #6... see vault boundary above) so
  that a *successful-but-invalid* response (e.g., a malformed `vault_reference`) is treated
  identically to a timeout — same fail-closed outcome, same error code family.
- **Rationale**: FR-032 (now FR-033/FR-034 after the round-3 renumber) originally only covered
  availability; an integrity failure is arguably worse, since it fails silently unless
  explicitly checked. Uniform treatment across all three dependencies avoids a special-cased
  carve-out that would be harder to reason about.
- **Alternatives considered**: Integrity checking only for the vault provider (highest-risk
  dependency) — rejected in favor of uniform treatment across all three dependencies, per the
  clarify-session decision.

## Summary

All architectural unknowns implied by the Technical Context are resolved above. No
`NEEDS CLARIFICATION` markers remain going into Phase 1.
