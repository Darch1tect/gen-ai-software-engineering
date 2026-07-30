# Quickstart: Validating the Virtual Card Lifecycle Specification

**Status**: This is a documentation-only feature (Constitution § "Regulatory Scope & Data
Governance"). There is no running system to start. This guide has two parts: (A) how to
validate the **specification package itself**, right now, with no implementation required; and
(B) the scenario script a future implementation MUST be able to pass, written against the
contracts in `contracts/` so nothing is guessed when that phase begins.

## Part A — Validating the specification package (do this now)

**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/*.md`, and
`.specify/memory/constitution.md` all present in this feature directory.

1. **Traceability pass**: For each Functional Requirement (FR-001…FR-030) in `spec.md`, confirm
   it is referenced by at least one operation in `contracts/*.md` or explicitly marked
   cross-cutting (Data Protection, Observability). *Expected outcome*: zero orphaned FRs.
2. **Constitution alignment pass**: Walk `plan.md`'s Constitution Check table; confirm every
   principle status is `PASS` and every `PASS` cites concrete evidence (an FR, SC, or entity),
   not just an assertion. *Expected outcome*: no principle without cited evidence.
3. **Data-tier pass**: Grep `data-model.md` and `contracts/*.md` for any field that could hold
   full PAN/CVV. *Expected outcome*: the only sensitive-data-adjacent field is
   `Virtual Card.vault_reference`, an opaque token — confirm no entity has a raw PAN/CVV field.
4. **Edge-case coverage pass**: For each edge case E1–E14 in `spec.md`, confirm the corresponding
   contract operation's "Output" list has a matching branch. *Expected outcome*: all 14 map to
   at least one documented output/error branch.
5. **Checklist pass**: Confirm `checklists/requirements.md` has all items checked and its Notes
   section reflects the final, resolved state (no open `[NEEDS CLARIFICATION]` markers).

## Part B — Scenario script for a future implementation

*The steps below describe **what to run once code exists**; they are not executable today.
Each step cites the spec/contract requirement it validates.*

### Setup (hypothetical)

- Provision an eligible test customer (`KYC = complete`, `account_status = active`) via the
  out-of-scope onboarding system's test fixtures.
- Provision an internal ops user with `Permission Scope{capability=view_only}` scoped to that
  customer, and a second internal user with `capability=fraud_action_capable` scoped to the
  same customer.

### Scenario 1 — Create, freeze, unfreeze (validates US1, US2 / FR-001–FR-008)

1. Call `CreateCard` for the test customer with a fresh `idempotency_key`. **Expect**: `Card`
   with `status=Active`, masked PAN only.
2. Repeat the identical `CreateCard` call with the *same* `idempotency_key`. **Expect**: same
   `card_id` returned, no second card created (FR-003, E1).
3. Call `FreezeCard`. **Expect**: `status=Frozen`; a subsequent simulated authorization attempt
   is declined with reason `CARD_FROZEN`.
4. Call `FreezeCard` again (duplicate). **Expect**: no-op, current state returned, no duplicate
   Audit Record (FR-006).
5. Call `UnfreezeCard`. **Expect**: `status=Active`; a subsequent simulated authorization is no
   longer declined for that reason.
6. **Verify**: exactly one `CARD_CREATED`, one `CARD_FROZEN`, one `CARD_UNFROZEN` Audit Record
   exist for this card (FR-027) — reconciliation check per SC-006.

### Scenario 2 — Spending limits, including monthly aggregate (validates US3 / FR-009–FR-015)

1. Set `per_transaction_cap` to a valid value. **Expect**: success, prior/new value in Audit
   Record.
2. Attempt to set a limit to `0`. **Expect**: `INVALID_LIMIT_VALUE`, previous value unchanged
   (FR-010, E3).
3. Simulate approved authorizations that bring the monthly aggregate running total within $1 of
   the `monthly_aggregate_cap`, then attempt one more authorization within the
   `per_transaction_cap` but that would exceed the remaining monthly aggregate. **Expect**:
   decline with reason `MONTHLY_AGGREGATE_CAP_EXCEEDED`, not `PER_TRANSACTION_CAP_EXCEEDED`
   (FR-014, E13).
4. Advance the simulated clock to the next calendar month. **Expect**: a new authorization at
   the same amount that would previously have declined now succeeds, with no explicit "reset"
   action having been taken (FR-015, E14).

### Scenario 3 — Transaction history pagination (validates US4 / FR-016–FR-018)

1. Call `ListTransactions` for a brand-new card. **Expect**: empty list, not an error (FR-017,
   E6).
2. Generate 120 transactions; call `ListTransactions` repeatedly following `next_cursor`.
   **Expect**: exactly 3 pages of ≤50 items each, no duplicates, no omissions, even if a new
   (121st) transaction is inserted between page requests (FR-018).

### Scenario 4 — Ops visibility and permission boundaries (validates US5 / FR-019–FR-021)

1. As the `view_only` ops user, call `GetCustomerCardView` for the test customer. **Expect**:
   masked card data + complete audit trail, including entries from Scenarios 1–3.
2. As the same ops user, call `GetCustomerCardView` for a *different* customer outside their
   scope. **Expect**: `ACCESS_DENIED`, no data in the response, and a new `ACCESS_DENIED` Audit
   Record targeting the attempted customer (FR-020, E8).

### Scenario 5 — Fraud flag (validates US6 / FR-022–FR-025)

1. As the `fraud_action_capable` user, call `RaiseFraudFlag` on a known transaction. **Expect**:
   transaction `status=Under Review`, associated card `status=Frozen`, both changes audited.
2. Call `RaiseFraudFlag` again on the same transaction (as a different authorized user).
   **Expect**: no-op, no duplicate Audit Record (FR-023, E9).
3. As the `view_only` ops user, attempt `RaiseFraudFlag`. **Expect**: `INSUFFICIENT_PERMISSION`,
   denial audited (FR-024).

### Scenario 6 — Rate limiting and external-dependency fail-closed behavior (validates FR-031, FR-032, E15, E16)

1. Rapidly repeat `FreezeCard` beyond its configured per-action-type rate limit. **Expect**:
   requests beyond the limit return `RATE_LIMIT_EXCEEDED`; the card's actual status is
   unaffected by the throttled attempts; no duplicate `CARD_FROZEN` Audit Record is written for
   a throttled request (FR-031, E15).
2. Repeat the same check independently for `CreateCard` and `SetSpendingLimit`. **Expect**: each
   action type's limit is enforced independently — exhausting the freeze/unfreeze limit does
   not affect the create or limit-update limits for the same customer.
3. Simulate the external vault/tokenization provider timing out mid-`CreateCard`. **Expect**:
   `DEPENDENCY_UNAVAILABLE`, no card record created, no partial state committed (FR-033, E16).
4. Simulate the payment-processor integration timing out mid-authorization. **Expect**:
   `DEPENDENCY_UNAVAILABLE` (or the processor's own fail-closed decline), no transaction left in
   an ambiguous state — it is either cleanly absent or clearly `Declined`, never stuck `Pending`
   indefinitely.

### Scenario 7 — Authentication boundary and dependency-integrity fail-closed (validates FR-032, FR-034, FR-035, FR-036, SC-013, E17, E18)

1. Attempt `FreezeCard` with no step-up/re-authentication signal present. **Expect**:
   `STEP_UP_REQUIRED`, no state change (FR-036).
2. Attempt `FreezeCard` with a step-up signal older than 5 minutes. **Expect**:
   `STEP_UP_REQUIRED` (SC-013's freshness boundary).
3. Repeat steps 1–2 for `SetSpendingLimit` and `RaiseFraudFlag`. **Expect**: same
   `STEP_UP_REQUIRED` behavior; `CreateCard` and `ListTransactions` remain unaffected (they rely
   on baseline authentication only, per FR-036).
4. Simulate the vault/tokenization provider returning a malformed/inconsistent
   `vault_reference` (not a timeout — a "successful" but corrupt response) during `CreateCard`.
   **Expect**: `DEPENDENCY_UNAVAILABLE`-equivalent fail-closed rejection, no card created
   (FR-034, E17) — identical outcome to a timeout.
5. Rapidly alternate `CreateCard`, `FreezeCard`, and `SetSpendingLimit` requests for the same
   customer, each individually staying under its own per-action-type limit. **Expect**: once
   the combined request count crosses the aggregate cross-action-type ceiling,
   `RATE_LIMIT_EXCEEDED` is returned even though no single action type's own limit was exceeded
   (FR-032, E18).

### Pass/Fail

All seven scenarios' **Expect** outcomes MUST hold for this feature to be considered correctly
implemented against this specification. Any deviation is a spec-vs-implementation gap to
resolve — not a reason to silently reinterpret the spec.
