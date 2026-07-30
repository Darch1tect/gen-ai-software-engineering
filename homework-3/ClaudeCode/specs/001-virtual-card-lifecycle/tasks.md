---
description: "Task list for Virtual Card Lifecycle Management"
---

# Tasks: Virtual Card Lifecycle Management

**Input**: Design documents from `/specs/001-virtual-card-lifecycle/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Status note**: Per the project constitution, this homework phase is documentation-only — no
code is written or executed. Every task below describes work for a **future implementation
phase** and uses the hypothetical single-backend-service layout named in `plan.md`'s Project
Structure section (`src/models/`, `src/services/`, `src/api/`, `src/lib/`, `tests/`). File paths
are illustrative targets for that future phase, not files created by this homework.

**Tests**: Included as documentation of required test coverage (contract + integration), per
the project's Specification Workflow & Quality Gates (constitution.md) and the homework's
verification requirement. These are task *specifications* for the future implementation phase,
not tests run now.

**Organization**: Tasks are grouped by user story (spec.md) to enable independent
implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US6, per spec.md)
- Every task cites the Functional Requirement(s), edge case(s), and/or contract operation it
  serves, and ends with an acceptance criterion — per Constitution Principle VI
  (Specification-Driven Traceability).

## Path Conventions

Hypothetical single-backend-service layout (plan.md → Project Structure):
`src/{models,services,api,lib}/`, `tests/{contract,integration,unit,performance}/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the hypothetical project scaffold and cross-cutting conventions every
story depends on.

- [ ] T001 Document the project structure per plan.md (`src/models/`, `src/services/`,
      `src/api/`, `src/lib/`, `tests/contract/`, `tests/integration/`, `tests/unit/`,
      `tests/performance/`) as the target layout for the implementation phase.
      **Acceptance criteria**: layout matches plan.md's Project Structure section exactly; no
      directory introduced that plan.md doesn't name.
- [ ] T002 [P] Define money/ID formatting conventions (integer minor units + ISO 4217 currency
      code; opaque UUIDv4/ULID entity IDs) in `src/lib/formatting.md` (design note) per the
      constitution's money/ID formatting rule.
      **Acceptance criteria**: every entity field in data-model.md that holds an amount or ID
      is traceable to one of these two conventions with no exceptions.
- [ ] T003 [P] Define the structured logging/correlation-ID schema (FR-029, FR-030;
      research.md #5) in `src/lib/observability.md` (design note): required fields
      (`correlation_id`, `actor_role`, `action`, `outcome`, `latency_ms`) and the explicit
      PAN/CVV exclusion rule.
      **Acceptance criteria**: schema has no field capable of holding Tier-1 data (Principle I
      cross-check).

**Checkpoint**: Conventions established — user story implementation can now begin.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core entities and cross-cutting services every user story's tasks build on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Implement the Virtual Card model (data-model.md → Virtual Card) in
      `src/models/card.py`: `card_id`, `customer_id`, `nickname`, `masked_pan`,
      `vault_reference`, `expiry`, `status`, `per_transaction_cap`, `monthly_aggregate_cap`,
      `version`, `created_at`.
      **Acceptance criteria**: no field capable of holding full PAN/CVV exists on this model
      (only `vault_reference`, an opaque token) — verifies FR-026 at the model level.
- [ ] T005 [P] Implement the Audit Record model (data-model.md → Audit Record; FR-027, FR-028)
      in `src/models/audit_record.py`, with **no update/delete method or route defined at
      all** (not merely permission-restricted).
      **Acceptance criteria**: the model/module exposes create-and-read operations only; a
      code reviewer can confirm no update/delete code path exists by inspection.
- [ ] T006 [P] Implement the Idempotency Record model and request-deduplication helper
      (data-model.md → Idempotency Record; FR-003, FR-006, FR-023; research.md #2) in
      `src/lib/idempotency.py`, keyed on `(actor_id, action_type, idempotency_key)`.
      **Acceptance criteria**: replaying a key returns the original `result_reference` without
      re-invoking the wrapped operation; verified by a unit test that counts invocations.
- [ ] T007 Implement the optimistic-concurrency version-check helper (research.md #3; FR-008)
      in `src/lib/concurrency.py`: reject a write whose supplied `version` does not match the
      current stored `version`, returning an explicit conflict result.
      **Acceptance criteria**: a simulated concurrent-write test (two writes with the same
      starting version) always yields exactly one success and one explicit conflict, never two
      successes or a silent overwrite.
- [ ] T008 [P] Implement the Permission Scope model and an authorization-check helper
      (data-model.md → Permission Scope; FR-019, FR-020; research.md #7) in
      `src/models/permission_scope.py`, checking both `capability` and `scope_boundary`
      independently.
      **Acceptance criteria**: a caller with the right capability but wrong scope boundary is
      denied, and vice versa — both failure modes are independently testable.
- [ ] T009 Implement the audit-plus-domain-write transactional helper (data-model.md →
      Cross-Entity Invariants) in `src/services/audit_service.py`: every domain write this
      feature performs and its corresponding Audit Record write commit atomically together.
      **Acceptance criteria**: a simulated failure injected between the domain write and the
      audit write results in neither being committed (no domain state change without a
      matching audit entry) — verifies SC-006's "zero unexplained gaps" at the write path.
- [ ] T010 [P] Implement the per-customer, per-action-type rate limiter (FR-031) in
      `src/lib/rate_limiter.py`: independent bounds for card creation, freeze/unfreeze, and
      limit-update actions.
      **Acceptance criteria**: exceeding one action type's limit returns a distinct
      rate-limit rejection without affecting other action types' counters for the same
      customer.
- [ ] T011 [P] Integration test: rate-limit rejection in
      `tests/integration/test_rate_limit.py` (FR-031, edge case E15).
      **Acceptance criteria**: exceeding the limit is rejected with a specific reason, logged
      (FR-029), and does not write a misleading audit "success" entry.
- [ ] T012 [P] Implement the external-dependency fail-closed wrapper (FR-033) in
      `src/lib/dependency_guard.py`: KYC/onboarding, vault/tokenization, and processor calls
      all reject with a "temporarily unavailable / retry" outcome on timeout/unavailability,
      committing no partial state.
      **Acceptance criteria**: a simulated dependency timeout injected mid-request never
      leaves a domain write partially applied.
- [ ] T013 [P] Integration test: external-dependency fail-closed behavior in
      `tests/integration/test_dependency_failure.py` (FR-033, edge case E16).
      **Acceptance criteria**: a simulated vault/KYC/processor timeout during each of
      CreateCard, FreezeCard, and an authorization decision each yields the fail-closed
      outcome with no partial state committed.

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 - Create a Virtual Card (Priority: P1) 🎯 MVP

**Goal**: An eligible end-user can request a new virtual card and see it appear, fully
audited, with duplicate/ineligible/over-limit requests handled correctly.

**Independent Test**: Request a new card for an eligible test customer and confirm a card
appears with masked details and status `Active`, independent of freeze/limit/history behavior.

### Tests for User Story 1

- [ ] T014 [P] [US1] Contract test for `CreateCard` in `tests/contract/test_create_card.py`,
      asserting the request/output shape in `contracts/card-lifecycle.contract.md` (FR-001).
- [ ] T015 [P] [US1] Integration test: repeated `CreateCard` with the same idempotency key
      creates exactly one card in `tests/integration/test_create_card_idempotency.py`
      (FR-003, edge case E1).
- [ ] T016 [P] [US1] Integration test: ineligible customer is rejected with reason, and the
      rejection is audited, in `tests/integration/test_create_card_ineligible.py`
      (acceptance scenario 2).
- [ ] T017 [P] [US1] Integration test: request at the per-account card maximum is rejected in
      `tests/integration/test_create_card_limit.py` (FR-002, edge case E10).

### Implementation for User Story 1

- [ ] T018 [P] [US1] Extend the Card model (T004) with creation-time validation (eligibility
      flag input, per-account active/frozen card count check) in `src/models/card.py`.
      **Acceptance criteria**: constructing a card for a customer already at the configured
      maximum raises a typed `CardLimitReached` condition rather than succeeding silently.
- [ ] T019 [US1] Implement the `CreateCard` service (eligibility check via the out-of-scope
      KYC boundary, card-limit check, idempotency check via T006, audit+log write via T009) in
      `src/services/card_service.py`. *Depends on*: T004, T006, T009, T010, T012, T018.
      **Acceptance criteria**: all four acceptance scenarios in spec.md User Story 1 pass.
      Additionally: rate-limit (T010) and dependency-fail-closed (T012) checks run before any
      idempotency/audit write; a throttled or fail-closed request never reaches CreateCard's
      state-changing path.
- [ ] T020 [US1] Implement the `CreateCard` API operation per
      `contracts/card-lifecycle.contract.md` in `src/api/card_api.py`. *Depends on*: T019.
      **Acceptance criteria**: response body matches the contract's success/rejected shapes
      exactly, including error codes `CUSTOMER_NOT_ELIGIBLE` and `CARD_LIMIT_REACHED`.
- [ ] T021 [US1] Implement masked-PAN serialization for card responses in
      `src/api/serializers/card_serializer.py`, ensuring FR-026. *Depends on*: T020.
      **Acceptance criteria**: a serialized response never contains more than the last 4 PAN
      digits under any code path, verified by a serializer-level test with a mocked full PAN.

**Checkpoint**: User Story 1 is independently functional. SC-001 (p95 ≤ 5s creation latency)
is the target to validate once this phase is implemented for real.

---

## Phase 4: User Story 2 - Freeze and Unfreeze a Card (Priority: P1)

**Goal**: The owning end-user can freeze and unfreeze a card instantly and safely, including
under concurrency and mid-flight-authorization races.

**Independent Test**: Freeze an Active card and confirm new authorizations decline; unfreeze
and confirm they resume — independent of how the card was created or its limits.

### Tests for User Story 2

- [ ] T022 [P] [US2] Contract test for `FreezeCard`/`UnfreezeCard` in
      `tests/contract/test_freeze_unfreeze.py` against `contracts/card-lifecycle.contract.md`.
- [ ] T023 [P] [US2] Integration test: repeated freeze on an already-Frozen card is a no-op
      with no duplicate audit entry, in `tests/integration/test_freeze_idempotent.py`
      (FR-006, acceptance scenario 3).
- [ ] T024 [P] [US2] Integration test: an authorization already mid-flight at freeze time
      resolves per pre-freeze rules while later attempts decline, in
      `tests/integration/test_freeze_race.py` (edge case E4).
- [ ] T025 [P] [US2] Integration test: unfreeze on a `Closed` card is rejected with no state
      change, in `tests/integration/test_unfreeze_closed.py` (FR-007, edge case E5).
- [ ] T026 [P] [US2] Integration test: concurrent freeze + limit-update against the same card
      yields one success and one explicit `VERSION_CONFLICT`, in
      `tests/integration/test_concurrent_conflict.py` (FR-008, edge case E2).

### Implementation for User Story 2

- [ ] T027 [US2] Implement `FreezeCard`/`UnfreezeCard` in `src/services/card_service.py` using
      the concurrency helper (T007). *Depends on*: T007, T010, T012, T019, T070.
      **Acceptance criteria**: acceptance scenarios 1, 2, 3, 5 in spec.md User Story 2 pass.
      Additionally: rate-limit and dependency-fail-closed checks run before the
      concurrency-guarded state transition; a missing/stale step-up signal (T070) rejects the
      request with `STEP_UP_REQUIRED` before any state change.
- [ ] T028 [US2] Implement an authorization-decision hook that declines new authorizations
      against a `Frozen` card in `src/services/authorization_service.py`. *Depends on*: T027.
      **Acceptance criteria**: an authorization submitted after a freeze commits is declined
      with reason `CARD_FROZEN`; one submitted before the freeze commits resolves independently
      (edge case E4).
- [ ] T029 [US2] Implement the `FreezeCard`/`UnfreezeCard` API operations in
      `src/api/card_api.py`. *Depends on*: T027.
      **Acceptance criteria**: response shapes match `contracts/card-lifecycle.contract.md`
      exactly, including `CARD_CLOSED` and `VERSION_CONFLICT` error codes.
- [ ] T030 [US2] Wire `CARD_FROZEN`/`CARD_UNFROZEN` audit and structured-log emission into
      T027 via T009 and the schema from T003. *Depends on*: T009, T027.
      **Acceptance criteria**: every freeze/unfreeze outcome (including rejections) produces
      exactly one Audit Record and one structured log event with a shared `correlation_id`.

**Checkpoint**: User Stories 1 AND 2 both independently functional. SC-002 (p99 ≤ 2s
authorization-path propagation) is the target to validate once implemented.

---

## Phase 5: User Story 3 - Set and Update Spending Limits (Priority: P2)

**Goal**: The owning end-user can set/update a per-transaction cap and a monthly aggregate
cap, with correct validation, concurrency handling, and monthly reset behavior.

**Independent Test**: Set a limit on an existing card and confirm authorizations above it
decline while ones at/below it succeed — independent of freeze state or history viewing.

### Tests for User Story 3

- [ ] T031 [P] [US3] Contract test for `SetSpendingLimit` in
      `tests/contract/test_set_limit.py` against `contracts/card-lifecycle.contract.md`.
- [ ] T032 [P] [US3] Integration test: zero/negative/above-ceiling limit values are rejected
      with the previous value unchanged, in `tests/integration/test_limit_validation.py`
      (FR-010, edge case E3).
- [ ] T033 [P] [US3] Integration test: an authorization within the per-transaction cap but
      over the remaining monthly aggregate cap declines with reason
      `MONTHLY_AGGREGATE_CAP_EXCEEDED`, in `tests/integration/test_monthly_cap.py`
      (FR-014, edge case E13).
- [ ] T034 [P] [US3] Integration test: the monthly aggregate running total resets at the
      calendar-month boundary with no explicit action required, in
      `tests/integration/test_monthly_reset.py` (FR-015, edge case E14).
- [ ] T035 [P] [US3] Integration test: lowering a limit does not void an existing pending
      hold above the new value, in `tests/integration/test_limit_lower_pending_hold.py`
      (FR-012, acceptance scenario 4).

### Implementation for User Story 3

- [ ] T036 [US3] Implement the Monthly Aggregate Counter model (data-model.md) in
      `src/models/monthly_aggregate_counter.py`, keyed `(card_id, calendar_month)`.
      **Acceptance criteria**: incrementing the counter for a new `(card_id, calendar_month)`
      pair implicitly creates the row — no separate "reset" code path exists (research.md #4).
- [ ] T037 [US3] Implement the `SetSpendingLimit` service (validation, versioning via T007,
      audit via T009) in `src/services/limit_service.py`. *Depends on*: T007, T009, T010, T012,
      T018, T070.
      **Acceptance criteria**: acceptance scenarios 1–4 in spec.md User Story 3 pass.
      Additionally: rate-limit and dependency-fail-closed checks run before any limit value is
      persisted; a missing/stale step-up signal (T070) rejects the request with
      `STEP_UP_REQUIRED` before any value is persisted.
- [ ] T038 [US3] Extend the authorization-decision hook (T028) with per-transaction-cap and
      monthly-aggregate-cap checks, recording which limit bound in `decline_reason`, in
      `src/services/authorization_service.py`. *Depends on*: T028, T036, T037.
      **Acceptance criteria**: a decline always names exactly one binding limit type
      (FR-014); never both, never neither.
- [ ] T039 [US3] Implement the `SetSpendingLimit` API operation in `src/api/card_api.py`.
      *Depends on*: T037.
      **Acceptance criteria**: response shape matches contract, including
      `INVALID_LIMIT_VALUE` and `VERSION_CONFLICT` error codes.

**Checkpoint**: User Stories 1–3 independently functional. SC-003 (p99 ≤ 5s limit enforcement)
is the target to validate once implemented.

---

## Phase 6: User Story 4 - View Transaction History (Priority: P2)

**Goal**: The owning end-user can view a correctly paginated, correctly ordered transaction
history, including empty and just-posted states.

**Independent Test**: Generate known transactions and confirm the history view returns
exactly those, correctly paginated — independent of any other lifecycle action.

### Tests for User Story 4

- [ ] T040 [P] [US4] Contract test for `ListTransactions` in
      `tests/contract/test_list_transactions.py` against
      `contracts/transactions.contract.md`.
- [ ] T041 [P] [US4] Integration test: a card with zero transactions returns an explicit
      empty result, not an error, in `tests/integration/test_transactions_empty.py`
      (FR-017, edge case E6).
- [ ] T042 [P] [US4] Integration test: cursor pagination remains stable (no duplicates, no
      omissions) when a new transaction is inserted between page requests, in
      `tests/integration/test_transactions_pagination.py` (FR-018).
- [ ] T043 [P] [US4] Integration test: a just-posted transaction is visible within the
      consistency window and correctly labeled `Pending` if not yet settled, in
      `tests/integration/test_transactions_recency.py` (edge case E7).

### Implementation for User Story 4

- [ ] T044 [P] [US4] Implement the Transaction model (data-model.md) in
      `src/models/transaction.py`: `transaction_id`, `card_id`, `amount`, `currency`,
      `status`, `decline_reason`, `masked_merchant`, `occurred_at`.
      **Acceptance criteria**: `status = Declined` always requires a non-null
      `decline_reason` at the model-validation level.
- [ ] T045 [US4] Implement the cursor-based pagination helper (research.md #8) in
      `src/lib/pagination.py`, bounded at 50 items/page (SC-005).
      **Acceptance criteria**: a simulated insert-during-pagination test never shifts or
      duplicates an already-returned item across pages.
- [ ] T046 [US4] Implement the `ListTransactions` service in
      `src/services/transaction_service.py`. *Depends on*: T010, T012, T044, T045.
      **Acceptance criteria**: acceptance scenarios 1–4 in spec.md User Story 4 pass.
      Additionally: rate-limit and dependency-fail-closed checks apply to this read path too,
      consistent with transactions.contract.md.
- [ ] T047 [US4] Implement the `ListTransactions` API operation in
      `src/api/transaction_api.py`. *Depends on*: T046.
      **Acceptance criteria**: response shape matches
      `contracts/transactions.contract.md` exactly, including the empty-state shape.

**Checkpoint**: User Stories 1–4 independently functional. SC-004 (p95 ≤ 10s visibility) and
SC-005 (page size/latency) are the targets to validate once implemented.

---

## Phase 7: User Story 5 - Ops/Compliance Masked View and Audit Trail (Priority: P2)

**Goal**: An authorized ops/compliance user can view masked card/transaction data and the
complete audit trail strictly within their permission scope; out-of-scope access is denied
and audited.

**Independent Test**: Look up a known customer's card as an authorized ops user and confirm
masked data + complete audit trail; confirm an out-of-scope user is denied.

### Tests for User Story 5

- [ ] T048 [P] [US5] Contract test for `GetCustomerCardView` in
      `tests/contract/test_ops_card_view.py` against `contracts/ops-compliance.contract.md`.
- [ ] T049 [P] [US5] Integration test: an authorized ops user receives masked card data, the
      transaction history, and a complete, gap-free, chronologically-ordered audit trail
      (including entries from other staff), in
      `tests/integration/test_ops_view_authorized.py` (acceptance scenarios 1, 3).
- [ ] T050 [P] [US5] Integration test: an out-of-scope ops user is denied with no data in the
      response, and the denial is itself audited, in
      `tests/integration/test_ops_view_denied.py` (FR-020, edge case E8).

### Implementation for User Story 5

- [ ] T051 [US5] Implement the Permission Scope enforcement middleware (capability +
      scope-boundary check, T008) in `src/services/authz_service.py`. *Depends on*: T008.
      **Acceptance criteria**: capability-only and scope-only failure modes are both
      independently triggerable and both denied.
- [ ] T052 [US5] Implement the `GetCustomerCardView` service (masked aggregation across card,
      transaction, and audit data) in `src/services/ops_view_service.py`. *Depends on*: T010,
      T012, T051, T018, T044, T005.
      **Acceptance criteria**: acceptance scenarios 1–3 in spec.md User Story 5 pass; no
      response path can bypass the T051 check. Additionally: rate-limit and
      dependency-fail-closed checks run before the masked aggregation query executes.
- [ ] T053 [US5] Implement the `GetCustomerCardView` API operation in `src/api/ops_api.py`.
      *Depends on*: T052.
      **Acceptance criteria**: a denied request's response body matches
      `contracts/ops-compliance.contract.md`'s `ACCESS_DENIED` shape exactly (no partial data
      leakage).

**Checkpoint**: User Stories 1–5 independently functional.

---

## Phase 8: User Story 6 - Ops Acts on a Fraud/Dispute Signal (Priority: P3)

**Goal**: An authorized fraud/ops user can flag a transaction as suspected fraud, freezing
the card and marking the transaction, strictly within the freeze-plus-flag scope boundary
(FR-025).

**Independent Test**: Flag a known transaction as fraud and confirm the linked card freezes,
the transaction is marked `Under Review`, and the action is fully audited.

### Tests for User Story 6

- [ ] T054 [P] [US6] Contract test for `RaiseFraudFlag` in
      `tests/contract/test_fraud_flag.py` against `contracts/ops-compliance.contract.md`.
- [ ] T055 [P] [US6] Integration test: a successful flag freezes the card, marks the
      transaction `Under Review`, and writes both `FRAUD_FLAG_RAISED` and `CARD_FROZEN` audit
      records, in `tests/integration/test_fraud_flag_success.py` (acceptance scenario 1).
- [ ] T056 [P] [US6] Integration test: a duplicate flag on an already-`Under Review`
      transaction is a no-op with no duplicate audit entry, in
      `tests/integration/test_fraud_flag_duplicate.py` (FR-023, edge case E9).
- [ ] T057 [P] [US6] Integration test: a user lacking `fraud_action_capable` is denied and
      the denial is audited, in `tests/integration/test_fraud_flag_denied.py`
      (FR-024, acceptance scenario 3).

### Implementation for User Story 6

- [ ] T058 [US6] Implement the `RaiseFraudFlag` service, reusing the freeze path (T027) and
      permission check (T051), strictly bounded to freeze+flag per FR-025 (no dispute-case
      state introduced), in `src/services/fraud_service.py`. *Depends on*: T010, T012, T027,
      T051, T070.
      **Acceptance criteria**: acceptance scenarios 1–3 in spec.md User Story 6 pass, and a
      code review confirms no dispute-case lifecycle state (open/investigate/resolve/close)
      was introduced anywhere in this task. Additionally: rate-limit and dependency-fail-closed
      checks run before the freeze+flag action is applied; a missing/stale step-up signal
      (T070) rejects the request with `STEP_UP_REQUIRED` before the freeze+flag is applied.
- [ ] T059 [US6] Implement the `RaiseFraudFlag` API operation in `src/api/ops_api.py`.
      *Depends on*: T058.
      **Acceptance criteria**: response shape matches
      `contracts/ops-compliance.contract.md` exactly, including `INSUFFICIENT_PERMISSION`.

**Checkpoint**: All six user stories independently functional.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements and verification that span multiple user stories.

- [ ] T060 [P] Finalize structured logging/correlation-ID propagation (FR-029, FR-030) across
      every service implemented above in `src/lib/observability.py`.
      **Acceptance criteria**: every service module from Phases 2–8 emits a log/event
      carrying a `correlation_id`; a static scan finds zero log statements referencing a full
      PAN/CVV field.
- [ ] T061 [P] Implement the audit-trail-vs-action-log reconciliation check (SC-006) in
      `src/services/reconciliation_service.py`.
      **Acceptance criteria**: running the check against a populated test dataset reports
      zero unexplained gaps between state-changing actions and audit records.
- [ ] T062 [P] Define the load/performance test plan validating SC-001, SC-002, SC-003,
      SC-004, SC-005, and SC-010 in `tests/performance/plan.md`.
      **Acceptance criteria**: every numbered Success Criterion in spec.md has a
      corresponding named performance test case in this plan.
- [ ] T063 Reconcile `data-model.md` and `contracts/*.md` against the as-implemented model,
      recording any deviation as an amendment (per constitution governance rules for
      deliverables that touch data-handling behavior).
      **Acceptance criteria**: zero undocumented deviations between contracts and
      implementation.
- [ ] T064 Execute the `quickstart.md` Part B scenario script end-to-end and record pass/fail
      per scenario.
      **Acceptance criteria**: all 7 scenarios in `quickstart.md` pass without deviation.
- [ ] T065 [P] Define the audit-store durability/availability plan (replication and/or
      backup strategy for the append-only store, SC-012) in
      `tests/performance/audit_availability_plan.md`.
      **Acceptance criteria**: plan states a concrete mechanism achieving ≥99.9%
      read-availability and "no defined deletion" retention, verifiable by review.

---

## Phase 10: Security Hardening (added by /speckit-clarify round 3)

**Purpose**: Close the three gaps the `checklists/security.md` review surfaced (CHK002,
CHK022, CHK032) after the original Foundational phase (T004–T013) and Polish phase (T060–T065)
were written. These extend, rather than replace, T010 (rate limiter) and T012 (dependency
guard).

- [ ] T066 [P] Extend the rate limiter (T010) with an aggregate, cross-action-type counter
      (FR-032) in `src/lib/rate_limiter.py`.
      **Acceptance criteria**: a request sequence that spreads across create/freeze/limit-update
      to stay under each individual per-action-type limit is still rejected once the combined
      aggregate ceiling is reached.
- [ ] T067 [P] Integration test: aggregate cross-action-type rate-limit rejection (FR-032, edge
      case E18) in `tests/integration/test_aggregate_rate_limit.py`.
- [ ] T068 [P] Extend the dependency guard (T012) with response-integrity validation (FR-034)
      in `src/lib/dependency_guard.py`.
      **Acceptance criteria**: a simulated malformed/inconsistent `vault_reference` (or
      equivalent KYC/processor response) is rejected identically to a timeout — same
      fail-closed outcome, no partial state committed.
- [ ] T069 [P] Integration test: dependency integrity-failure fail-closed behavior (FR-034, edge
      case E17) in `tests/integration/test_dependency_integrity.py`.
- [ ] T070 Implement the step-up/re-authentication freshness check (FR-035, FR-036) in
      `src/services/authn_service.py`: verifies a step-up signal from the out-of-scope
      authentication system is present and no older than 5 minutes (SC-013) before a high-risk
      action (freeze, unfreeze, limit update, fraud flag) proceeds.
      **Acceptance criteria**: a missing or stale (>5 min) step-up signal rejects the action
      with `STEP_UP_REQUIRED`; a signal exactly at the 5-minute boundary is handled
      deterministically (documented as inclusive or exclusive, not left ambiguous).
- [ ] T071 [P] Integration test: step-up re-authentication required for freeze, limit-update, and
      fraud-flag actions, and NOT required for card creation or transaction-history reads
      (FR-036, SC-013) in `tests/integration/test_step_up_auth.py`.

**Checkpoint**: All three security-checklist gaps (CHK002, CHK022, CHK032) have corresponding
implementation + test tasks.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories.
- **User Stories (Phase 3–8)**: All depend on Foundational completion.
  - US1 (P1) and US2 (P1) have no dependency on each other and can proceed in parallel.
  - US3 (P2) depends on the Card model (T004/T018) from US1 but not on US2's freeze logic,
    aside from sharing the concurrency helper (T007) introduced in Foundational.
  - US4 (P2) depends only on Foundational (Transaction model is new in this phase).
  - US5 (P2) depends on Foundational (Permission Scope, T008) and reads data produced by
    US1/US3/US4 but does not modify it — safe to build in parallel once those exist.
  - US6 (P3) depends on the freeze logic from US2 (T027) and the permission-check from US5
    (T051) — it is the one story with a real cross-story dependency, consistent with its
    lower priority and later phase placement.
- **Polish (Phase 9)**: Depends on all desired user stories being complete.
- **Security Hardening (Phase 10)**: T066/T067 extend T010; T068/T069 extend T012 — both can
  proceed any time after Foundational. T070/T071 (step-up auth) can also proceed any time after
  Foundational, but US2 (T027), US3 (T037), and US6 (T058) each additionally depend on T070
  before they can be considered complete.

### Within Each User Story

- Tests are written before implementation tasks in the same phase.
- Models before services; services before API operations.
- Story complete before moving to the next priority tier.

### Parallel Opportunities

- All Setup tasks (T002, T003) marked [P] run in parallel.
- Foundational tasks T005, T006, T008, T010, T011, T012, T013 marked [P] run in parallel
  (T004, T007, T009 have narrower ordering needs relative to them).
- Once Foundational completes, US1 and US2 can be staffed and built in parallel; US4 can also
  start in parallel with either, since it only needs the Foundational phase.
- All contract/integration tests within a story phase marked [P] run in parallel.
- Phase 10 tasks T066, T067, T068, T069, T071 (all `[P]`) can run in parallel with each other
  and alongside US1/US2/US4 once Foundational completes; T070 is not `[P]` since US2/US3/US6
  depend on it directly (see Implementation Strategy).

---

## Parallel Example: User Story 1

```text
# Launch all tests for User Story 1 together:
Task: "Contract test for CreateCard in tests/contract/test_create_card.py"
Task: "Integration test: idempotent replay in tests/integration/test_create_card_idempotency.py"
Task: "Integration test: ineligible customer rejected in tests/integration/test_create_card_ineligible.py"
Task: "Integration test: card-limit rejection in tests/integration/test_create_card_limit.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 — both P1)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational (blocks everything).
3. Complete Phase 3 (US1) and Phase 4 (US2) — these two together are the MVP: a customer can
   create a card and control it via freeze/unfreeze, fully audited.
4. **STOP and VALIDATE**: run the relevant `quickstart.md` Part B scenarios (1) independently.

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. US1 + US2 → **not yet MVP-complete without T070**: US2's own acceptance criteria (T027)
   require the step-up-auth freshness check from Phase 10, so T070 must land before US2 (and
   later US3, US6) can be considered done — either pull T070 forward to run alongside
   Foundational, or treat it as a hard blocker checked at each of those stories' checkpoints.
3. US3 → spending limits (per-transaction + monthly aggregate); also blocked on T070 (T037).
4. US4 → transaction visibility.
5. US5 → internal ops/compliance read access.
6. US6 → fraud/dispute flagging (depends on US2 + US5 groundwork, and on T070 via T058).
7. Phase 10 (Security Hardening) → T066–T071; T070 specifically must land no later than
   alongside US2, not deferred to the end, despite its position later in this file.
8. Polish → observability, reconciliation, performance validation, audit durability plan,
   quickstart sign-off (now validating all 7 `quickstart.md` scenarios, including Scenario 7).

---

## Notes

- [P] tasks touch different files with no unmet dependencies.
- [Story] labels map every implementation task to exactly one of the 6 user stories in
  spec.md, satisfying Constitution Principle VI (Specification-Driven Traceability).
- Every implementation task above ends with an explicit acceptance criterion, per the
  homework's verification requirement and constitution.md's Specification Workflow section.
- This entire file describes work for a **future implementation phase**; no task here is
  executed as part of the current documentation-only homework deliverable.
