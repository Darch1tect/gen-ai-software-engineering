# Contract: Internal Ops/Compliance/Fraud Operations

**Status**: Hypothetical / illustrative only — no API is implemented in this phase. Describes
the operation-level contract for User Stories 5 and 6 (FR-019–FR-025).

Every operation below requires the caller to be an authenticated internal staff member with a
`Permission Scope` record (data-model.md); every outcome — including denials — MUST produce an
Audit Record (FR-020, FR-022) and a structured log/event (FR-029).

Both operations below may also reject with `RATE_LIMIT_EXCEEDED` (FR-031 per-action-type or
FR-032 aggregate, edge cases E15/E18) or `DEPENDENCY_UNAVAILABLE` (FR-033 availability or FR-034
integrity, edge cases E16/E17), consistent with `card-lifecycle.contract.md`; neither rejection
writes an Audit Record, since no state changed. `RaiseFraudFlag` additionally may reject with
`STEP_UP_REQUIRED` if its step-up/re-authentication signal is missing or older than 5 minutes
(FR-035, FR-036, SC-013); `GetCustomerCardView` is a read operation and never returns this code.

## `GetCustomerCardView`

**Serves**: User Story 5 (FR-019, FR-020, FR-021)

- **Actor**: ops/compliance user
- **Preconditions**: caller has a non-revoked `Permission Scope` covering the target customer
- **Input**: `customer_id`
- **Output (authorized)**: `{cards: [Card{..., masked_pan}], transactions: [...], audit_trail:
  [AuditRecord{...}]}` — masked data only, complete chronologically-ordered audit trail
  including entries written by other internal staff (acceptance scenario 1 & 3)
- **Output (out of scope)**: error `ACCESS_DENIED`; no card/transaction/audit data is returned
  in the response body (E8); an `ACCESS_DENIED` Audit Record IS still written, targeting the
  attempted `customer_id` and the denied `actor_id`
- **Acceptance criteria / Definition of Done**:
  - [ ] A denied request never leaks any customer data in its error response
  - [ ] A denied request is itself always audited (it is a security-relevant event, not a
        "nothing happened" no-op)
  - [ ] The returned audit trail contains zero gaps relative to the full set of state-changing
        actions recorded for that card

## `RaiseFraudFlag`

**Serves**: User Story 6 (FR-022, FR-023, FR-024, FR-025)

- **Actor**: fraud/ops user with `capability = fraud_action_capable`
- **Preconditions**: caller's `Permission Scope` covers the transaction's customer; transaction
  exists; a step-up/re-authentication signal no older than 5 minutes is present (FR-036,
  SC-013)
- **Input**: `transaction_id`, `reason_code`, `idempotency_key`
- **Output (success)**: `Transaction{status=Under Review}`, associated `Card{status=Frozen}`;
  Audit Records `FRAUD_FLAG_RAISED` and `CARD_FROZEN` both written (acceptance scenario 1)
- **Output (no-op — already under review)**: current transaction state returned, no duplicate
  flag/freeze/Audit Record (FR-023, E9)
- **Output (rejected — insufficient capability)**: error `INSUFFICIENT_PERMISSION`
  (`capability != fraud_action_capable`); Audit Record `ACCESS_DENIED` written (acceptance
  scenario 3)
- **Scope boundary (FR-025)**: this operation only freezes the card and marks the transaction
  `Under Review`. It does **not** open, progress, or close a dispute case — that lifecycle is
  owned by an out-of-scope external dispute-management process; this contract exposes no
  operation for it.
- **Acceptance criteria / Definition of Done**:
  - [ ] Two near-simultaneous flags on the same transaction by different users never produce
        two `FRAUD_FLAG_RAISED` Audit Records
  - [ ] A read-only ops user attempting this operation is always denied and always audited
  - [ ] No operation in this contract implements dispute-case state (open/investigate/
        resolve/close) — confirms FR-025 scope boundary is respected at the contract level
