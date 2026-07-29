# Contract: Card Lifecycle Operations

**Status**: Hypothetical / illustrative only — no API is implemented in this phase (Constitution
§ "Regulatory Scope & Data Governance"). This document describes the operation-level contract a
future implementation MUST satisfy; any request/response shapes shown are non-executable
pseudocode, not a committed wire format.

Every operation below:
- Requires an `idempotency_key` (research.md #2) scoped to `(actor_id, action_type)`.
- Requires a `correlation_id` (generated if not supplied) threaded into the structured log/event
  (FR-029/FR-030) and, where applicable, the Audit Record (FR-027).
- Returns a `Card` representation containing only `masked_pan` — never full PAN/CVV (FR-026).
- May reject with `RATE_LIMIT_EXCEEDED` if the caller has exceeded that operation's
  per-action-type rate limit (FR-031, edge case E15) **or** the aggregate cross-action-type
  limit (FR-032, edge case E18); the underlying card/entity state is left unchanged and the
  attempt is logged (FR-029) but not audited, since no state changed.
- May reject with `DEPENDENCY_UNAVAILABLE` if a required external dependency (KYC/onboarding,
  vault/tokenization, payment processor) is unavailable, times out, or returns an
  integrity-check failure — a fail-closed outcome in all three cases (FR-033 availability,
  FR-034 integrity; edge cases E16, E17); no partial state is committed, and the attempt is
  logged (FR-029).

`FreezeCard`/`UnfreezeCard` and `SetSpendingLimit` additionally:

- May reject with `STEP_UP_REQUIRED` if the request's step-up/re-authentication signal is
  missing or older than 5 minutes (FR-035, FR-036, SC-013). `CreateCard` relies on baseline
  authentication only and never returns this code.

## `CreateCard`

**Serves**: User Story 1 (FR-001, FR-002, FR-003)

- **Actor**: end-user (owning customer)
- **Preconditions**: customer is eligible (KYC/account standing — out-of-scope system);
  customer's active+frozen card count < configured maximum (FR-002)
- **Input**: `customer_id`, `idempotency_key`, optional `nickname`
- **Output (success)**: `Card{card_id, masked_pan, nickname?, expiry, status=Active,
  per_transaction_cap (default), monthly_aggregate_cap (default), version, created_at}`
- **Output (rejected — ineligible)**: error `CUSTOMER_NOT_ELIGIBLE` + user-visible reason
  (FR-002 story acceptance scenario 2); Audit Record `CARD_CREATE_REJECTED` still written
- **Output (rejected — limit reached)**: error `CARD_LIMIT_REACHED` (FR-002, E10); Audit Record
  `CARD_CREATE_REJECTED` written
- **Idempotent replay**: same `idempotency_key` returns the original `Card` unchanged, no new
  Audit Record (E1)
- **Acceptance criteria / Definition of Done**:
  - [ ] A repeated request with the same idempotency key never results in two `Card` rows
  - [ ] Every outcome (success, ineligible, limit-reached) has a corresponding Audit Record
  - [ ] Response never contains full PAN or CVV, only `masked_pan`

## `FreezeCard` / `UnfreezeCard`

**Serves**: User Story 2 (FR-004–FR-008)

- **Actor**: end-user (owning customer)
- **Preconditions**: card exists, is not `Closed` (FR-007); caller supplies the `version` last
  read (optimistic concurrency, research.md #3); a step-up/re-authentication signal no older
  than 5 minutes is present (FR-036, SC-013)
- **Input**: `card_id`, `version`, `idempotency_key`
- **Output (success)**: `Card{status=Frozen|Active, version=version+1}`; Audit Record
  `CARD_FROZEN`/`CARD_UNFROZEN` with prior/new status
- **Output (no-op — already in target state)**: current `Card` returned unchanged, no duplicate
  Audit Record (FR-006, acceptance scenario 3)
- **Output (rejected — closed card)**: error `CARD_CLOSED` (FR-007, E5); Audit Record is NOT a
  misleading success entry
- **Output (rejected — version conflict)**: error `VERSION_CONFLICT` (FR-008, E2); caller must
  re-read current state and retry
- **In-flight authorization race (E4)**: a freeze request does not roll back or invalidate an
  authorization that was already mid-flight at submission time; that authorization resolves per
  its own pre-freeze rules, while every authorization *starting after* the freeze is committed
  is declined with reason `CARD_FROZEN`
- **Acceptance criteria / Definition of Done**:
  - [ ] Freeze/unfreeze against a `Closed` card always errors, never silently succeeds
  - [ ] Two concurrent conflicting requests against the same card never both "win" silently —
        exactly one succeeds, the other gets `VERSION_CONFLICT`
  - [ ] p99 latency from request acceptance to the authorization path reflecting the new status
        is ≤ 2s (SC-002)

## `SetSpendingLimit`

**Serves**: User Story 3 (FR-009–FR-015)

- **Actor**: end-user (owning customer)
- **Preconditions**: card exists, is not `Closed`; caller supplies current `version`; a
  step-up/re-authentication signal no older than 5 minutes is present (FR-036, SC-013)
- **Input**: `card_id`, `version`, `limit_type` (`per_transaction` | `monthly_aggregate`),
  `new_value` (integer minor units + currency), `idempotency_key`
- **Output (success)**: `Card{..., version=version+1}` with updated cap; Audit Record
  `LIMIT_UPDATED{limit_type, prior_value, new_value}`
- **Output (rejected — invalid value)**: error `INVALID_LIMIT_VALUE` (zero/negative/above
  ceiling, FR-010, E3); previous value unchanged; Audit Record `LIMIT_UPDATE_REJECTED`
- **Output (rejected — version conflict)**: error `VERSION_CONFLICT` (E2/acceptance scenario 3)
- **Note**: lowering a limit below an existing pending hold does not void the hold (FR-012,
  acceptance scenario 4) — the new value only governs future authorization decisions
- **Acceptance criteria / Definition of Done**:
  - [ ] Every rejected limit-update attempt is still audited (not silently dropped)
  - [ ] `per_transaction` and `monthly_aggregate` are independently validated and independently
        recorded — never conflated into a single "the limit" value
  - [ ] p99 enforcement latency against new authorizations ≤ 5s (SC-003)
