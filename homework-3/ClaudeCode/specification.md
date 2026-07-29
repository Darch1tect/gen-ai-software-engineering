# Virtual Card Lifecycle Management — Specification

> Ingest this specification, its companion `agents.md` and editor/AI rules, and generate an
> implementation that satisfies the High-Level and Mid-Level Objectives below — but **not
> yet**: this document, per the project constitution (`.specify/memory/constitution.md`),
> governs a **documentation-only phase**. No code, API, or UI exists or is authored against
> this spec today. Every "System MUST" statement below describes required behavior for a
> **future implementation phase**.
>
> This document is the standalone, self-contained specification for the feature. It was
> produced through a structured Spec-Driven Development process (constitution → specify →
> clarify → plan → tasks → analyze, twice) whose full working artifacts — deeper architectural
> rationale, the entity-relationship data model, per-operation contracts, and a validation
> script — live under `specs/001-virtual-card-lifecycle/` and are cited by name throughout for
> traceability, but are not required reading to understand or execute this spec.

## High-Level Objective

Give end-users of a regulated neobank full self-service control over a virtual card's
lifecycle — create it, freeze/unfreeze it, bound its spending, and review its transaction
history — while giving internal ops/compliance/fraud staff masked, permission-scoped
visibility and a complete, tamper-proof audit trail of every action taken on that card, so
that the feature is safe to operate in a regulated financial environment from day one.

**Scope boundary in one sentence**: this feature covers virtual card creation, freeze/unfreeze,
per-transaction and monthly spending caps, transaction-history visibility, and internal
masked/audited access plus a bounded freeze-and-flag fraud response — it explicitly excludes
KYC/onboarding decisioning, PAN/CVV vaulting internals, payment-network authorization protocol
details, customer notifications, and the full external dispute-case lifecycle, all of which are
modeled only as out-of-scope dependencies with a defined boundary (see Context, Assumptions).

## Mid-Level Objectives

Each objective below is **observable**: a reviewer can point to a concrete before/after change
in the world (or a reliably reproducible negative outcome) to confirm it is met.

- **MLO-1 — Self-service card issuance**: An eligible end-user can request a virtual card and
  see it appear, `Active` and masked, in their own view — with every attempt (successful,
  ineligible, over-limit, or duplicate) fully audited. *(Serves User Story 1; FR-001–FR-003,
  FR-026, FR-031, FR-032)*
- **MLO-2 — Instant, safe freeze/unfreeze**: An end-user can freeze a card to immediately stop
  new authorizations and unfreeze it to immediately resume them, with no duplicate audit noise
  from repeated taps and no undefined behavior when a freeze races a transaction or another
  write. *(Serves User Story 2; FR-004–FR-008)*
- **MLO-3 — Self-bounded spending**: An end-user can set and update both a per-transaction cap
  and a monthly aggregate cap; an authorization that would exceed either is declined with the
  specific binding reason, and a lowered cap never retroactively voids an already-authorized
  hold. *(Serves User Story 3; FR-009–FR-015)*
- **MLO-4 — Trustworthy transaction visibility**: An end-user can retrieve their card's
  transaction history, correctly paginated and ordered, with an honest empty state and honest
  labeling of not-yet-settled activity. *(Serves User Story 4; FR-016–FR-018)*
- **MLO-5 — Scoped internal visibility with full audit trail**: An authorized ops/compliance
  user can view a customer's masked card/transaction data and the complete, gap-free,
  chronologically-ordered audit trail strictly within their assigned permission scope; an
  out-of-scope attempt is denied and that denial is itself audited. *(Serves User Story 5;
  FR-019–FR-021)*
- **MLO-6 — Bounded fraud response**: An authorized fraud/ops user can freeze a card and flag
  its transaction for review in response to a fraud/dispute signal, with the action surface
  strictly limited to freeze-plus-flag — no dispute-case lifecycle is modeled here. *(Serves
  User Story 6; FR-022–FR-025)*
- **MLO-7 — Provable auditability and observability**: Every state-changing action in scope
  produces an immutable audit record, and every operation (state-changing or not) produces a
  structured, PAN/CVV-free log/event carrying a correlation ID — the two are deliberately
  separate signals serving compliance and operations respectively. *(Cross-cutting;
  FR-026–FR-030; Constitution Principles I, II, IV)*
- **MLO-8 — Self-enforcing guardrails**: The system enforces both per-action-type and aggregate
  cross-action-type rate limits, and fails closed (rather than open) on any external-dependency
  unavailability *or* integrity failure, without relying on an operator to notice and
  intervene. *(Cross-cutting; FR-031–FR-034; Constitution Principle III)*
- **MLO-9 — Strong assurance on high-risk actions**: Baseline caller authentication is an
  out-of-scope system boundary, but freeze, unfreeze, limit-update, and fraud-flag actions each
  additionally require a step-up/re-authentication signal no older than 5 minutes — a stale or
  missing signal rejects the action before any state change. *(Cross-cutting; FR-035, FR-036;
  Constitution Principle I; added via the security-focused requirements checklist)*

## Non-Functional & Policy Requirements

### Security & Privacy

- Full PAN, CVV, and other Tier-1 sensitive data are **never** represented in this feature's own
  data model, logs, or any end-user- or ops-facing view; only a masked PAN (last 4 digits) or an
  opaque `vault_reference` token into an external, out-of-scope vault/tokenization provider may
  appear (FR-026; Constitution Principle I). *Data classification*: Tier-1 (PAN/CVV/full
  government ID — vault-only), Tier-2 (masked PAN, cardholder name, limits, transaction
  metadata — access-controlled and auditable), Tier-3 (aggregated/anonymized analytics).
- Every internal actor (ops/compliance/fraud/support) is bound by a **Permission Scope** with
  two independent, separately-deniable dimensions: a **capability** (`view_only` vs.
  `fraud_action_capable`) and a **scope boundary** (which customers/cases). Both checks must
  fail independently and both failures must be auditable (FR-019, FR-020, FR-024).
- Data in transit and at rest is protected with industry-standard mechanisms (e.g., TLS 1.2+,
  strong at-rest encryption) at every trust boundary this feature crosses (Constitution
  Principle I).
- **Authentication boundary**: baseline caller authentication (proving identity, distinct from
  Permission Scope's authorization checks) is provided by an out-of-scope authentication
  system — the same boundary pattern as KYC/vault/processor. High-risk actions (freeze,
  unfreeze, limit update, fraud flag) additionally require a step-up/re-authentication signal
  from that system, no older than **5 minutes** (SC-013); a missing or stale signal rejects the
  action with `STEP_UP_REQUIRED` before any state change (FR-035, FR-036).

### Audit & Logging

- Every state-changing action in scope (create, freeze, unfreeze, limit change, fraud flag, and
  every **denied** access/action attempt) produces an immutable, append-only Audit Record
  capturing actor identity + role, action type, prior state, new state, reason/source, and
  timestamp — with **no update or delete code path at all**, not merely a restricted one
  (FR-027, FR-028).
- The audit trail is retained **indefinitely** (no defined deletion) at **≥99.9% read-availability**
  for compliance lookups, and is **explicitly exempt from data-subject erasure/correction
  requests** on legal-obligation/legitimate-interest grounds — this exemption is a deliberate,
  stated resolution of the tension with GDPR-style rights acknowledged for cardholder PII
  elsewhere, not a silent gap (SC-012).
- Every audit-relevant action MAY carry an optional `external_case_reference`, so a
  `FRAUD_FLAG_RAISED` entry (or any future action type) can be correlated with an out-of-scope
  external system's case record without this feature modeling that system's lifecycle.
- Independent of the audit trail, **every** operation (successful reads included) emits a
  structured, machine-parseable log/event with at minimum a correlation ID, actor role, action
  name, outcome, and latency — and this stream, too, must never contain Tier-1 data (FR-029,
  FR-030; Constitution Principle IV). The two signals are deliberately not merged: ops/support
  need operational visibility into successful reads that the audit trail intentionally omits.

### Reliability & Concurrency

- Every write operation (create, freeze/unfreeze, limit update, fraud flag) is **idempotent**
  under client retry via a client-supplied idempotency key scoped to `(actor, action_type)`; a
  repeated key returns the original outcome rather than re-executing the operation (FR-003,
  FR-006, FR-023).
- Every card carries an optimistic-concurrency `version` token; a write against a stale version
  is rejected with an **explicit conflict response**, never silently dropped or silently
  overwritten (FR-008).
- Every customer-initiated action type (create, freeze/unfreeze, limit-update) is bound by an
  **independent, per-action-type rate limit** — exhausting one action type's limit never
  affects another's — with a distinguishable rejection reason, logged but not audited (no state
  changed) (FR-031). A second, **aggregate cross-action-type rate limit** sits on top of these,
  closing the residual risk of an attacker spreading requests across action types to stay under
  each individual ceiling (FR-032).
- Any out-of-scope external dependency this feature calls (KYC/onboarding, vault/tokenization,
  payment processor) that is unavailable, times out, **or returns an integrity-check failure**
  (a valid-looking but corrupted/inconsistent response) causes the request to **fail closed**: a
  specific "temporarily unavailable / retry" outcome, no partial state committed, still logged —
  applied uniformly to both availability failures (FR-033) and integrity failures (FR-034).

### Performance & Latency (assumed targets unless marked non-negotiable)

| ID | Target | Rationale |
|---|---|---|
| SC-001 | Card creation completes in **≤5s (p95)** | Instant-issuance is baseline UX for digital-first card products |
| SC-002 | Freeze/unfreeze reaches the authorization path in **≤2s (p99)**, own status view in **≤5s (p99)** | Tightest budget in this spec — freeze is a security control; slow propagation extends fraud-exposure window |
| SC-003 | Limit change enforced against new authorizations in **≤5s (p99)** | Limit reduction is often also a loss-control action |
| SC-004 | Transaction visible in history within **≤10s (p95)** of posting | Balances near-real-time visibility against realistic settlement delay |
| SC-005 | Pagination: **≤50 items/page**, **≤2s (p95)** per page | Bounds response size and perceived load latency |
| SC-006 | **100%** of in-scope state changes produce a matching audit record (zero unexplained gaps) | **Non-negotiable** — Constitution Principle II |
| SC-007 | **0%** of views ever expose unmasked PAN/CVV | **Non-negotiable** — Constitution Principle I |
| SC-008 | Retried create/freeze/unfreeze/fraud-flag requests never duplicate state or audit entries | Idempotency guarantee, independently verified per action type |
| SC-009 | **≥90%** of simulated lost-card freeze attempts complete without contacting support | Proxy for self-service trust / support-cost reduction |
| SC-010 | System sustains **≥500 concurrent** freeze/unfreeze requests without breaching SC-002 | Sized for a plausible fraud-wave/outage spike |
| SC-011 | **100%** of operations produce a correlation-ID-bearing log/event, sufficient to reconstruct a request lifecycle without the audit trail | **Non-negotiable** — Constitution Principle IV |
| SC-012 | Audit trail: indefinite retention, **≥99.9%** read-availability | **Non-negotiable** — Constitution Principle II |
| SC-013 | High-risk actions (freeze/unfreeze, limit update, fraud flag) rejected **100%** of the time with a missing/stale (>5 min) step-up signal | **Assumed target** — 5 minutes is a common step-up-auth freshness window in banking UX, balancing hijacked-session risk against re-authentication friction |

All targets above are **assumed** unless labeled non-negotiable, and are reasonable for FinTech
UX/ops because: freeze/unfreeze and limit changes gate real fraud/loss exposure (hence the
tightest budgets); card creation and transaction visibility tolerate slightly looser budgets
because they are not themselves loss-control actions; and the non-negotiable targets are
non-negotiable specifically because they operationalize a constitution principle rather than a
UX preference.

## Implementation Notes

Guardrails a builder (human or AI agent) MUST NOT violate, regardless of the eventual tech
stack:

- **Money & currency**: every monetary amount is an **integer in minor units** (e.g., cents)
  paired with an **ISO 4217** currency code — never a floating-point type.
- **Identifiers**: every entity ID (card, transaction, audit record) is an **opaque,
  non-guessable** value (e.g., UUIDv4 or ULID) — never a sequential integer.
- **Idempotency**: a client-supplied idempotency key is required on every state-changing
  request; the system persists a dedupe record (`key → result`) scoped to `(actor_id,
  action_type)` and short-circuits repeats rather than re-executing (research.md #2).
- **Concurrency**: optimistic concurrency via a `version` token on every mutable entity; never
  pessimistic locking as the default, and never last-write-wins without an explicit conflict
  signal (research.md #3).
- **Monthly aggregate cap tracking**: an incrementally-maintained counter keyed
  `(card_id, calendar_month)`, **not** a recomputation from the full transaction ledger on every
  read, and **not** a scheduled "reset job" — a new month's counter is implicitly created the
  first time that month is touched, so the reset can never "fail to run" (research.md #4).
- **Vault boundary**: full PAN/CVV are never modeled inside this feature's own entities; a card
  holds only a `masked_pan` (last 4) and an opaque `vault_reference` token (research.md #6).
- **Permission model**: capability (`view_only` / `fraud_action_capable`) and scope boundary are
  two independent checks, both independently deniable and auditable — never collapsed into a
  single flag (research.md #7).
- **Pagination**: cursor-based (opaque position marker), never offset/limit, because
  reverse-chronological transaction lists are insert-heavy at the head and offset-based
  pagination would drift under concurrent inserts (research.md #8).
- **Audit storage**: physically separate, append-only store from the mutable operational store
  — enforced by **not building** an update/delete code path at all, not by permission-restricting
  one that exists (research.md #1).
- **Error semantics**: every rejection (validation failure, permission denial, rate limit,
  dependency-unavailable, version conflict) returns a **specific, distinguishable reason** —
  never a generic failure — and, except for rate-limit/dependency-failure throttling (where no
  state changed), is captured in the audit trail.
- **Observability vs. audit**: structured logs (FR-029/030) and audit records (FR-027/028) are
  two deliberately separate signals with separate retention/exemption rules — do not conflate
  them or use one to satisfy the other's requirement.

## Context

### Beginning Context

- A ratified project constitution (`.specify/memory/constitution.md`, v1.0.0) defining 6
  non-negotiable principles: Sensitive Data Protection & Least Privilege; Auditability &
  Regulatory Traceability; Reliability, Idempotency & Concurrency Safety; Observability Without
  Data Exposure; Measurable Non-Functional Targets; Specification-Driven Traceability.
- A Spec-Kit scaffold (`.specify/`, `.claude/skills/`) with templates for spec/plan/tasks/
  checklists, but no feature content yet authored.
- No code, API, UI, database, or running service of any kind exists for this feature.
- The following systems are **assumed to exist, out-of-scope, and integrated only via the
  boundary this spec defines**: a KYC/onboarding system (card-creation eligibility), a card
  vault/tokenization provider (PAN/CVV custody), a payment processor/network integration
  (authorization decisioning), an authentication system (baseline caller identity plus a
  step-up/re-authentication signal for high-risk actions, FR-035/FR-036), and an external
  dispute-management system (post-freeze investigation/chargeback).

### Ending Context

- This `specification.md` (self-contained, at the repository root) plus its companion
  `agents.md`, editor/AI rules, and `README.md` — the four required Homework 3 deliverables.
- A full Spec-Kit working-artifact trail under `specs/001-virtual-card-lifecycle/`: `spec.md`
  (the layered feature spec these objectives were extracted from, with 6 user stories, 18 edge
  cases, 36 functional requirements, 13 success criteria), `plan.md` (hypothetical architecture
  + constitution gate evidence), `research.md` (11 architectural decisions with rejected
  alternatives), `data-model.md` (7 persisted entities plus 1 documented request-time signal),
  `contracts/` (3 operation-contract documents),
  `quickstart.md` (a spec-validation walkthrough plus a 7-scenario future-implementation
  script), and `checklists/` (a 16-item spec-quality checklist, a 33-item compliance/audit
  requirements-quality checklist, and a 34-item security requirements-quality checklist).
- Still **no running system** — a future, separately-authorized implementation phase would
  consume this package (starting from `tasks.md`'s 71 tasks) to build the hypothetical
  single-backend-service architecture implied by the Implementation Notes above.

### Assumptions

- A customer may hold multiple concurrent virtual cards up to a configurable ceiling (exact
  number is a product/risk-policy value, not pinned down here).
- Card-creation eligibility (KYC, account standing) is decided entirely by the out-of-scope
  onboarding system; this spec defines only the accept/reject behavior at that boundary.
- "Instant" freeze/unfreeze means the SC-002 latency budget, not literally zero-latency.
- The trigger that transitions a card into `Closed` (e.g., replacement, offboarding) is
  out-of-scope; this spec defines behavior only *given* a card is already `Closed`.
- Customer notifications (push/SMS on freeze or fraud flag) are out of scope.
- Baseline caller authentication and the step-up/re-authentication signal (FR-035, FR-036) are
  provided by an existing, out-of-scope authentication system; this spec defines only the
  freshness check at the boundary, not how that system authenticates a caller.
- This entire document describes a future implementation phase; it is not itself an
  implementation.

## Cross-Cutting Requirements

### Edge Cases & Failure Modes

| # | Scenario | Expected Behavior | Audit/Compliance Implication |
|---|---|---|---|
| E1 | Duplicate card-creation request (same idempotency key) | Exactly one card created; both responses match | One `CARD_CREATED` entry; retry is not itself auditable |
| E2 | Freeze and limit-update race on the same card | One wins deterministically; the other gets an explicit conflict, never silently lost | Audit trail shows true applied order, both actors |
| E3 | Invalid limit value (zero/negative/above ceiling) | Rejected, previous value unchanged | Rejected attempt logged, not silently dropped |
| E4 | Freeze submitted while an authorization is mid-flight | In-flight authorization resolves per pre-freeze rules; later attempts decline | Both events independently audited with ordering timestamps |
| E5 | Unfreeze attempted on a `Closed` card | Rejected, no state change | Rejected attempt logged; `Closed` never re-enters `Active` |
| E6 | Transaction history on a brand-new card | Explicit empty result, not an error | N/A |
| E7 | History requested right after a transaction posts | Visible within consistency window; may show `Pending`, explicitly labeled | N/A |
| E8 | Ops user queries outside permission scope | Access denied, no data returned | Denial itself is an audit event |
| E9 | Same transaction fraud-flagged twice, near-simultaneously | Second flag is a no-op | Only one `FRAUD_FLAG_RAISED` entry |
| E10 | Card creation at the per-account maximum | Rejected, no card created | Rejected attempt logged |
| E11 | Stale read of card status right after a remote freeze | View catches up within consistency window; authorization decisions never use stale state | No silent security gap |
| E12 | Card creation for an ineligible customer | Rejected with non-sensitive reason | Rejected attempt logged; no downstream trace of the card |
| E13 | Authorization within per-tx cap but over monthly cap | Declined, reason names the monthly cap specifically | Declined attempt logged with the binding limit type |
| E14 | Monthly cap resets mid-authorization at month boundary | Evaluated against whichever month is in effect at decision time, no split evaluation | Reset itself generates no audit entry |
| E15 | Customer exceeds a per-action-type rate limit | Rejected with a specific reason; card state unchanged | Logged, not audited (no state changed) |
| E16 | External dependency (vault/KYC/processor) unavailable/timeout | Fails closed: "temporarily unavailable/retry", no partial state | Logged; audited only if a state change had already committed |
| E17 | External dependency returns a valid-looking but corrupted/inconsistent response (integrity failure, not a timeout) | Treated identically to E16: fails closed, no partial state | Logged; same audit treatment as E16 |
| E18 | Customer spreads requests across create/freeze/limit-update to stay under each individual per-action-type rate limit | Aggregate cross-action-type limit still rejects once the combined ceiling is reached | Logged, not audited (no state changed) |

### Verification Strategy

- **Constitution gate**: every principle re-checked against the spec both before Phase 0
  research and after Phase 1 design (`plan.md` § Constitution Check) — all 6 PASS with cited
  evidence.
- **Spec-quality checklist** (`checklists/requirements.md`, 16 items): content quality,
  requirement completeness/testability, feature readiness — all passing.
- **Compliance/audit checklist** (`checklists/compliance.md`, 33 items): a formal
  pre-implementation gate specifically probing completeness, clarity, consistency, and
  traceability of audit/compliance-relevant requirements — used to surface and resolve two real
  gaps (GDPR-erasure exemption; external-case correlation).
- **Security checklist** (`checklists/security.md`, 34 items): a second formal
  pre-implementation gate scoped to technical security-control requirements (PAN/CVV handling,
  vault boundary, permission scoping, authN/authZ, rate limiting, fail-closed dependency
  handling) — used to surface and resolve three more gaps: a missing authentication boundary
  (FR-035/036), fail-closed not covering dependency integrity failures (FR-034), and no
  aggregate safeguard against multi-action-type rate-limit evasion (FR-032).
- **Cross-artifact analysis** (`/speckit-analyze`, run three times): mechanical consistency
  checks across spec/plan/tasks/data-model/contracts — findings found and remediated across all
  three passes (ID-scheme drift, missing task coverage, stale plan citations, an unwired
  foundational task, a stale field list, a stale file tree, and — after the security checklist's
  clarify round — a repeat of the ID-scheme drift plus 6 more coverage/consistency gaps spanning
  every companion document, including this one); zero open findings as of this document.
- **Test categories as documentation** (see Low-Level Tasks): contract tests (one per operation,
  asserting the shape in `contracts/*.md`), integration tests (one per acceptance scenario and
  per edge case E1–E16), and a performance/load test plan mapped 1:1 to every Success Criterion
  above.
- **Reconciliation check**: a dedicated audit-trail-vs-action-log reconciliation verifying
  SC-006's "zero unexplained gaps" claim.
- **Manual validation script** (`quickstart.md`): Part A is a spec-traceability walkthrough
  runnable today (no code required); Part B is a 7-scenario end-to-end script for the future
  implementation phase, covering the MVP flows plus rate-limiting and dependency fail-closed
  behavior.
- **Data fixtures**: an eligible and an ineligible test customer; a `view_only` and a
  `fraud_action_capable` internal test user, each with a defined permission scope.

## Low-Level Tasks

Every task below cites the Mid-Level Objective it serves and ends with an acceptance criterion.
Task IDs match `specs/001-virtual-card-lifecycle/tasks.md` exactly for cross-reference. File
paths are the hypothetical single-backend-service layout named in Implementation Notes
(`src/{models,services,api,lib}/`, `tests/{contract,integration,unit,performance}/`) — targets
for the future implementation phase, not files created by this homework.

### Setup (no single MLO — shared conventions)

- **T001** Document the project structure (`src/models/`, `src/services/`, `src/api/`,
  `src/lib/`, `tests/{contract,integration,unit,performance}/`).
  *DoD*: layout matches this spec's Implementation Notes exactly.
- **T002 [P]** Define money/ID formatting conventions (integer minor units + ISO 4217; opaque
  UUIDv4/ULID IDs) in `src/lib/formatting.md`.
  *DoD*: every amount/ID field in the data model traces to one of these two conventions, no
  exceptions.
- **T003 [P]** Define the structured logging/correlation-ID schema (FR-029/030) in
  `src/lib/observability.md`: `correlation_id`, `actor_role`, `action`, `outcome`,
  `latency_ms`, with an explicit PAN/CVV exclusion rule.
  *DoD*: schema has no field capable of holding Tier-1 data.

### Foundational (blocks all MLOs — MUST complete first)

- **T004** Implement the Virtual Card model in `src/models/card.py`: `card_id`, `customer_id`,
  `nickname`, `masked_pan`, `vault_reference`, `expiry`, `status`, `per_transaction_cap`,
  `monthly_aggregate_cap`, `version`, `created_at`.
  *DoD*: no field can hold full PAN/CVV (only `vault_reference`) — verifies FR-026 at the
  model level.
- **T005 [P]** Implement the Audit Record model in `src/models/audit_record.py` with **no
  update/delete method or route at all**.
  *DoD*: module exposes create+read only, confirmable by code inspection.
- **T006 [P]** Implement the Idempotency Record model + dedup helper in
  `src/lib/idempotency.py`, keyed `(actor_id, action_type, idempotency_key)`.
  *DoD*: replaying a key returns the original result without re-invoking the wrapped operation.
- **T007** Implement the optimistic-concurrency version-check helper in
  `src/lib/concurrency.py`.
  *DoD*: two concurrent writes from the same starting version always yield exactly one success
  and one explicit conflict.
- **T008 [P]** Implement the Permission Scope model + authorization-check helper in
  `src/models/permission_scope.py`, checking `capability` and `scope_boundary` independently.
  *DoD*: right-capability/wrong-scope and wrong-capability/right-scope are both independently
  deniable.
- **T009** Implement the audit-plus-domain-write transactional helper in
  `src/services/audit_service.py`: domain write + Audit Record write commit atomically.
  *DoD*: a fault injected between the two writes commits neither — verifies SC-006.
- **T010 [P]** *(Serves MLO-8)* Implement the per-customer, per-action-type rate limiter
  (FR-031) in `src/lib/rate_limiter.py`.
  *DoD*: exceeding one action type's limit doesn't affect another's counter for the same
  customer.
- **T011 [P]** *(Serves MLO-8)* Integration test: rate-limit rejection (FR-031, E15) in
  `tests/integration/test_rate_limit.py`.
- **T012 [P]** *(Serves MLO-8)* Implement the external-dependency fail-closed wrapper (FR-033)
  in `src/lib/dependency_guard.py` for KYC/vault/processor calls.
  *DoD*: a simulated timeout never leaves a domain write partially applied.
- **T013 [P]** *(Serves MLO-8)* Integration test: dependency fail-closed behavior (FR-033, E16)
  in `tests/integration/test_dependency_failure.py`.

### Serving MLO-1 — Self-service card issuance

- **T014 [P]** Contract test for `CreateCard` in `tests/contract/test_create_card.py` (FR-001).
- **T015 [P]** Integration test: idempotent replay (FR-003, E1) in
  `tests/integration/test_create_card_idempotency.py`.
- **T016 [P]** Integration test: ineligible customer rejected + audited (acceptance scenario 2)
  in `tests/integration/test_create_card_ineligible.py`.
- **T017 [P]** Integration test: card-limit rejection (FR-002, E10) in
  `tests/integration/test_create_card_limit.py`.
- **T018 [P]** Extend the Card model with creation-time validation (eligibility flag, per-account
  count check) in `src/models/card.py`.
  *DoD*: exceeding the configured max raises a typed `CardLimitReached` condition.
- **T019** Implement the `CreateCard` service in `src/services/card_service.py`. *Depends on*:
  T004, T006, T009, T010, T012, T018.
  *DoD*: all 4 acceptance scenarios pass; rate-limit/fail-closed checks run before any
  idempotency/audit write.
- **T020** Implement the `CreateCard` API operation in `src/api/card_api.py`. *Depends on*: T019.
  *DoD*: response matches contract exactly, including `CUSTOMER_NOT_ELIGIBLE`/`CARD_LIMIT_REACHED`.
- **T021** Implement masked-PAN serialization in `src/api/serializers/card_serializer.py`.
  *DoD*: never more than last-4 PAN digits under any code path (mocked-full-PAN test).

### Serving MLO-2 — Instant, safe freeze/unfreeze

- **T022 [P]** Contract test for `FreezeCard`/`UnfreezeCard` in
  `tests/contract/test_freeze_unfreeze.py`.
- **T023 [P]** Integration test: duplicate freeze is a no-op (FR-006, E-scenario 3) in
  `tests/integration/test_freeze_idempotent.py`.
- **T024 [P]** Integration test: freeze vs. in-flight authorization race (E4) in
  `tests/integration/test_freeze_race.py`.
- **T025 [P]** Integration test: unfreeze on `Closed` card rejected (FR-007, E5) in
  `tests/integration/test_unfreeze_closed.py`.
- **T026 [P]** Integration test: concurrent freeze + limit-update conflict (FR-008, E2) in
  `tests/integration/test_concurrent_conflict.py`.
- **T027** Implement `FreezeCard`/`UnfreezeCard` in `src/services/card_service.py`. *Depends on*:
  T007, T010, T012, T019, T070.
  *DoD*: acceptance scenarios 1/2/3/5 pass; rate-limit/fail-closed checks run before the
  concurrency-guarded transition; a missing/stale step-up signal (T070) rejects with
  `STEP_UP_REQUIRED` before any state change.
- **T028** Implement the authorization-decision hook declining new auths on a `Frozen` card in
  `src/services/authorization_service.py`. *Depends on*: T027.
  *DoD*: post-freeze attempts decline with `CARD_FROZEN`; pre-freeze in-flight ones resolve
  independently (E4).
- **T029** Implement the `FreezeCard`/`UnfreezeCard` API operations in `src/api/card_api.py`.
  *Depends on*: T027.
  *DoD*: response matches contract, including `CARD_CLOSED`/`VERSION_CONFLICT`.
- **T030** Wire `CARD_FROZEN`/`CARD_UNFROZEN` audit + log emission. *Depends on*: T009, T027.
  *DoD*: every outcome (including rejections) produces exactly one Audit Record + one log event
  sharing a `correlation_id`.

### Serving MLO-3 — Self-bounded spending

- **T031 [P]** Contract test for `SetSpendingLimit` in `tests/contract/test_set_limit.py`.
- **T032 [P]** Integration test: invalid limit values rejected (FR-010, E3) in
  `tests/integration/test_limit_validation.py`.
- **T033 [P]** Integration test: monthly-cap-binding decline (FR-014, E13) in
  `tests/integration/test_monthly_cap.py`.
- **T034 [P]** Integration test: monthly cap resets at month boundary with no explicit action
  (FR-015, E14) in `tests/integration/test_monthly_reset.py`.
- **T035 [P]** Integration test: lowering a limit doesn't void a pending hold (FR-012, scenario
  4) in `tests/integration/test_limit_lower_pending_hold.py`.
- **T036** Implement the Monthly Aggregate Counter model, keyed `(card_id, calendar_month)`, in
  `src/models/monthly_aggregate_counter.py`.
  *DoD*: a new month's row is implicitly created on first touch — no separate "reset" code path.
- **T037** Implement `SetSpendingLimit` in `src/services/limit_service.py`. *Depends on*: T007,
  T009, T010, T012, T018, T070.
  *DoD*: acceptance scenarios 1–4 pass; rate-limit/fail-closed checks run before any limit
  value is persisted; a missing/stale step-up signal (T070) rejects with `STEP_UP_REQUIRED`
  before any value is persisted.
- **T038** Extend the authorization hook with per-tx and monthly-cap checks, recording which
  limit bound in `decline_reason`, in `src/services/authorization_service.py`. *Depends on*:
  T028, T036, T037.
  *DoD*: a decline always names exactly one binding limit type.
- **T039** Implement the `SetSpendingLimit` API operation in `src/api/card_api.py`. *Depends
  on*: T037.
  *DoD*: response matches contract, including `INVALID_LIMIT_VALUE`/`VERSION_CONFLICT`.

### Serving MLO-4 — Trustworthy transaction visibility

- **T040 [P]** Contract test for `ListTransactions` in `tests/contract/test_list_transactions.py`.
- **T041 [P]** Integration test: empty state (FR-017, E6) in
  `tests/integration/test_transactions_empty.py`.
- **T042 [P]** Integration test: cursor-pagination stability under concurrent inserts (FR-018)
  in `tests/integration/test_transactions_pagination.py`.
- **T043 [P]** Integration test: just-posted transaction recency labeling (E7) in
  `tests/integration/test_transactions_recency.py`.
- **T044 [P]** Implement the Transaction model in `src/models/transaction.py`.
  *DoD*: `status = Declined` always requires a non-null `decline_reason` at the validation
  level.
- **T045** Implement cursor-based pagination in `src/lib/pagination.py`, bounded at 50 items/page
  (SC-005).
  *DoD*: a simulated insert-during-pagination test never shifts/duplicates an already-returned
  item.
- **T046** Implement `ListTransactions` in `src/services/transaction_service.py`. *Depends on*:
  T010, T012, T044, T045.
  *DoD*: acceptance scenarios 1–4 pass; rate-limit/fail-closed checks apply to this read path
  too.
- **T047** Implement the `ListTransactions` API operation in `src/api/transaction_api.py`.
  *Depends on*: T046.
  *DoD*: response matches contract exactly, including the empty-state shape.

### Serving MLO-5 — Scoped internal visibility with full audit trail

- **T048 [P]** Contract test for `GetCustomerCardView` in `tests/contract/test_ops_card_view.py`.
- **T049 [P]** Integration test: authorized view returns masked data + gap-free audit trail
  (scenarios 1, 3) in `tests/integration/test_ops_view_authorized.py`.
- **T050 [P]** Integration test: out-of-scope access denied + audited (FR-020, E8) in
  `tests/integration/test_ops_view_denied.py`.
- **T051** Implement the Permission Scope enforcement middleware in
  `src/services/authz_service.py`. *Depends on*: T008.
  *DoD*: capability-only and scope-only failure modes are both independently triggerable and
  denied.
- **T052** Implement `GetCustomerCardView` in `src/services/ops_view_service.py`. *Depends on*:
  T010, T012, T051, T018, T044, T005.
  *DoD*: scenarios 1–3 pass; no response path bypasses the T051 check; rate-limit/fail-closed
  checks run before the query executes.
- **T053** Implement the `GetCustomerCardView` API operation in `src/api/ops_api.py`. *Depends
  on*: T052.
  *DoD*: a denied request's body matches the contract's `ACCESS_DENIED` shape exactly (no
  partial leakage).

### Serving MLO-6 — Bounded fraud response

- **T054 [P]** Contract test for `RaiseFraudFlag` in `tests/contract/test_fraud_flag.py`.
- **T055 [P]** Integration test: successful flag freezes card + marks transaction (scenario 1)
  in `tests/integration/test_fraud_flag_success.py`.
- **T056 [P]** Integration test: duplicate flag is a no-op (FR-023, E9) in
  `tests/integration/test_fraud_flag_duplicate.py`.
- **T057 [P]** Integration test: insufficient permission denied + audited (FR-024, scenario 3)
  in `tests/integration/test_fraud_flag_denied.py`.
- **T058** Implement `RaiseFraudFlag` in `src/services/fraud_service.py`, reusing the freeze path
  (T027) and permission check (T051), strictly bounded to freeze+flag per FR-025. *Depends on*:
  T010, T012, T027, T051, T070.
  *DoD*: scenarios 1–3 pass; code review confirms no dispute-case lifecycle state was
  introduced; rate-limit/fail-closed checks run before the action applies; a missing/stale
  step-up signal (T070) rejects with `STEP_UP_REQUIRED` before the freeze+flag is applied.
- **T059** Implement the `RaiseFraudFlag` API operation in `src/api/ops_api.py`. *Depends on*:
  T058.
  *DoD*: response matches contract exactly, including `INSUFFICIENT_PERMISSION`.

### Serving MLO-7 & MLO-8 — Polish & cross-cutting verification

- **T060 [P]** Finalize structured logging/correlation-ID propagation (FR-029/030) across every
  service in `src/lib/observability.py`.
  *DoD*: every service module emits a correlation-ID-bearing log event; a static scan finds
  zero log statements referencing a full PAN/CVV field.
- **T061 [P]** Implement the audit-vs-action-log reconciliation check (SC-006) in
  `src/services/reconciliation_service.py`.
  *DoD*: running it against a populated test dataset reports zero unexplained gaps.
- **T062 [P]** Define the load/performance test plan validating SC-001–SC-005 and SC-010 in
  `tests/performance/plan.md`.
  *DoD*: every numbered Success Criterion has a corresponding named performance test case.
- **T063** Reconcile `data-model.md`/`contracts/*.md` against the as-implemented model, recording
  any deviation as an amendment.
  *DoD*: zero undocumented deviations.
- **T064** Execute `quickstart.md` Part B end-to-end and record pass/fail per scenario.
  *DoD*: all 7 scenarios pass without deviation.
- **T065 [P]** Define the audit-store durability/availability plan (SC-012) in
  `tests/performance/audit_availability_plan.md`.
  *DoD*: plan states a concrete mechanism achieving ≥99.9% read-availability and indefinite
  retention, verifiable by review.

### Security Hardening (serves MLO-8, MLO-9 — added after the security-focused requirements checklist)

- **T066 [P]** Extend the rate limiter (T010) with an aggregate cross-action-type counter
  (FR-032) in `src/lib/rate_limiter.py`.
  *DoD*: a request sequence spread across create/freeze/limit-update to stay under each
  individual limit is still rejected once the combined aggregate ceiling is reached.
- **T067 [P]** Integration test: aggregate cross-action-type rate-limit rejection (FR-032, E18)
  in `tests/integration/test_aggregate_rate_limit.py`.
- **T068 [P]** Extend the dependency guard (T012) with response-integrity validation (FR-034)
  in `src/lib/dependency_guard.py`.
  *DoD*: a simulated malformed/inconsistent `vault_reference` (or equivalent KYC/processor
  response) is rejected identically to a timeout.
- **T069 [P]** Integration test: dependency integrity-failure fail-closed behavior (FR-034, E17)
  in `tests/integration/test_dependency_integrity.py`.
- **T070** Implement the step-up/re-authentication freshness check (FR-035, FR-036) in
  `src/services/authn_service.py`: verifies a step-up signal is present and no older than 5
  minutes (SC-013) before a high-risk action (freeze, unfreeze, limit update, fraud flag)
  proceeds.
  *DoD*: a missing or stale (>5 min) signal rejects with `STEP_UP_REQUIRED`; the 5-minute
  boundary condition is handled deterministically, not left ambiguous.
- **T071 [P]** Integration test: step-up re-authentication required for freeze, limit-update,
  and fraud-flag, and NOT required for card creation or transaction-history reads (FR-036,
  SC-013) in `tests/integration/test_step_up_auth.py`.

## Traceability & Supporting Artifacts

For deeper rationale behind any decision above, see (all under
`specs/001-virtual-card-lifecycle/`): `spec.md` (full layered spec with all 6 user stories'
acceptance scenarios verbatim), `plan.md` (Constitution Check gate + hypothetical architecture),
`research.md` (11 decisions with rejected alternatives), `data-model.md` (full entity field
tables), `contracts/*.md` (per-operation request/output/error contracts), `quickstart.md`
(validation walkthrough + 7-scenario script), `checklists/requirements.md`,
`checklists/compliance.md`, and `checklists/security.md` (spec-quality, compliance-quality, and
security-quality gates respectively). This `specification.md` is the authoritative,
self-contained summary; where any wording differs, treat the discrepancy as a documentation bug
to reconcile, not an intentional divergence.
