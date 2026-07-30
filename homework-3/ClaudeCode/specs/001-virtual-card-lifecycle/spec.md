# Feature Specification: Virtual Card Lifecycle Management

**Feature Branch**: `001-virtual-card-lifecycle`

**Created**: 2026-07-29

**Status**: Draft

**Input**: User description: "Virtual card lifecycle management for a regulated neobank: end-users can create a virtual card, freeze/unfreeze it instantly, set and update spending limits, and view their transaction history. Internal ops/compliance staff can view (masked) card and transaction data for a customer, see the full audit trail of card lifecycle actions, and act on fraud/dispute signals within their permission scope. The system must be suitable for a regulated FinTech environment: every state-changing action must be auditable, sensitive card data (PAN/CVV) must never be exposed in plaintext outside a vault boundary, writes must be idempotent, and non-functional targets (latency, consistency, rate limits) must be explicit. This is a documentation-only specification (per the project constitution) — no code, API, or UI is being built, only the layered specification."

## Clarifications

### Session 2026-07-29

- Q: What rate-limiting policy should apply to customer-initiated card actions? → A: Per-action-type limits (separate, tuned bounds for create vs. freeze/unfreeze vs. limit-update)
- Q: What triggers a card's transition into `Closed` state? → A: Out-of-scope — `Closed` is a terminal state this spec only reacts to (FR-007, E5); the transition into it is owned by an adjacent, out-of-scope feature (e.g., card replacement/account offboarding)
- Q: What should happen when an external dependency (vault, KYC, processor) is unavailable or times out mid-request? → A: Fail closed — reject with a specific "temporarily unavailable/retry" outcome, still logged, no partial state committed
- Q: What durability/availability target applies to the audit trail? → A: Retain indefinitely (no defined deletion), with a 99.9% read-availability target for compliance lookups
- Q: How does indefinite audit-trail retention (SC-012) reconcile with GDPR-style erasure rights acknowledged for cardholder PII? → A: Audit records are fully exempt from erasure/correction requests (legal-obligation/legitimate-interest grounds); the exemption is explicit, not implied
- Q: Should an Audit Record be able to correlate with the external dispute-management system's case record (FR-025)? → A: Yes — add a general, optional `external_case_reference` field on the Audit Record entity (not limited to fraud-flag entries)
- Q: Where does caller authentication (proving identity, as distinct from Permission Scope authorization) come from? → A: Baseline authentication is an out-of-scope system boundary, but high-risk actions (freeze, unfreeze, limit update, fraud flag) require a step-up/re-authentication signal from that system
- Q: Does the fail-closed guarantee (FR-032) extend to an external dependency returning a valid-looking but incorrect/corrupted response, not just unavailability/timeout? → A: Yes — extend fail-closed to integrity failures too, uniformly across KYC, vault, and processor dependencies
- Q: Should there be an aggregate safeguard against an attacker spreading requests across action types to stay under each individual per-action-type rate limit (FR-031)? → A: Yes — add an aggregate cross-action-type rate limit as a second layer on top of the existing per-action-type limits

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create a Virtual Card (Priority: P1)

An end-user with an eligible account requests a new virtual card so they can start spending
online or in an app without waiting for a physical card.

**Why this priority**: Card creation is the entry point for every other flow in this feature.
Nothing else can be exercised without it, and it is the first moment a customer forms an
impression of the product's speed and trustworthiness.

**Independent Test**: Can be fully tested by having an eligible customer request a new virtual
card and confirming that a usable card (masked number, expiry, status = Active) appears in
their account, is immediately available for viewing, and is captured in the audit trail —
independent of freeze, limits, or transaction-history behavior.

**Acceptance Scenarios**:

1. **Given** an eligible customer with no virtual card at their per-account card limit,
   **When** they request a new virtual card, **Then** a card is created in `Active` status,
   masked card details (last 4 digits, expiry, nickname) are returned, and an audit record is
   written capturing actor, action = `CARD_CREATED`, and timestamp.
2. **Given** a customer who is not eligible (e.g., account suspended or KYC incomplete),
   **When** they request a new virtual card, **Then** the request is rejected with a
   user-visible reason and no card, card record, or audit "success" entry is created; an audit
   record capturing the rejected attempt MUST still be written.
3. **Given** a customer submits the same card-creation request twice (e.g., due to a client
   retry after a network timeout) using the same idempotency key, **When** the second request
   arrives, **Then** exactly one card is created and both requests receive the same resulting
   card reference — no duplicate card is created.
4. **Given** a customer already at their maximum number of concurrent active virtual cards,
   **When** they request another card, **Then** the request is rejected with a clear
   "limit reached" reason and no new card or audit "success" entry is created.

---

### User Story 2 - Freeze and Unfreeze a Card (Priority: P1)

An end-user who has misplaced their device, suspects misuse, or simply wants to pause spending
temporarily can freeze their virtual card instantly, and unfreeze it just as quickly when ready
to resume spending.

**Why this priority**: Freeze/unfreeze is the primary fraud-mitigation and peace-of-mind
control end-users have; it must be trustworthy and effectively instantaneous to build
confidence, and its correctness/audit trail is heavily scrutinized by compliance.

**Independent Test**: Can be fully tested by taking an existing Active card, freezing it, and
confirming both (a) new transaction authorizations are declined while frozen, and (b)
unfreezing restores authorization capability — independent of how the card was created or
what its spending limit is.

**Acceptance Scenarios**:

1. **Given** an Active card, **When** the owning customer freezes it, **Then** the card status
   becomes `Frozen` within the defined consistency window (see Success Criteria), any new
   authorization attempt against it is declined, and an audit record (`CARD_FROZEN`) is
   written with actor and timestamp.
2. **Given** a Frozen card, **When** the owning customer unfreezes it, **Then** the card status
   returns to `Active` within the defined consistency window, new authorizations are accepted
   again, and an audit record (`CARD_UNFROZEN`) is written.
3. **Given** a card that is already Frozen, **When** the customer submits another freeze
   request (e.g., duplicate tap), **Then** the system returns the current `Frozen` state
   without error and without writing a duplicate `CARD_FROZEN` audit record for the
   already-applied state.
4. **Given** a card with a transaction authorization already in-flight (mid-authorization) at
   the moment a freeze request is submitted, **When** the freeze is processed, **Then** the
   in-flight authorization is allowed to complete per its own outcome (approve or decline based
   on pre-freeze rules) while all subsequent authorization attempts are declined; the race is
   never left in an undefined state.
5. **Given** a card that has been permanently closed/terminated, **When** an unfreeze is
   attempted, **Then** the request is rejected with a clear "card is closed" reason and no
   status change or misleading "success" audit entry is written.

---

### User Story 3 - Set and Update Spending Limits (Priority: P2)

An end-user sets or adjusts a spending limit on their virtual card to control how much can be
spent, for budgeting or risk-reduction purposes.

**Why this priority**: Limits are a core self-service control expected in modern card products,
but the feature is usable (with default limits) even before a customer ever touches this
control, so it ranks below create/freeze.

**Independent Test**: Can be fully tested by setting a limit on an existing card and confirming
that authorization attempts above the limit are declined while attempts at or below it are
accepted — independent of freeze state or transaction-history viewing.

**Acceptance Scenarios**:

1. **Given** an Active card with a default limit, **When** the customer sets a new valid
   limit, **Then** the new limit takes effect within the defined consistency window, prior
   limit and new limit are both recorded, and an audit record (`LIMIT_UPDATED`) captures the
   before/after values.
2. **Given** a customer submits a limit value that is zero, negative, or above the
   product-wide maximum, **When** the update is requested, **Then** the request is rejected
   with a specific validation reason and the previous limit remains unchanged.
3. **Given** two limit-update requests for the same card submitted concurrently (e.g., from two
   devices), **When** both are processed, **Then** exactly one final limit value results, the
   losing request receives an explicit conflict/outcome response (not a silent overwrite), and
   the audit trail reflects the actual order applied.
4. **Given** a card with a pending (not-yet-settled) authorization hold that exceeds a
   newly-requested lower limit, **When** the customer lowers the limit, **Then** the new limit
   is accepted and applies to future authorizations; the existing hold is left to settle or
   expire per its own terms rather than being silently voided.

---

### User Story 4 - View Transaction History (Priority: P2)

An end-user reviews the list of transactions (approved, declined, pending) on their virtual
card to track spending and spot unrecognized activity.

**Why this priority**: Transaction visibility is essential for trust and self-service fraud
detection, but depends on the card already existing and having activity, so it is sequenced
after creation/freeze/limits.

**Independent Test**: Can be fully tested by generating known transactions against a card and
confirming the customer's transaction view returns exactly those transactions with correct
status, amount, and timestamp, correctly paginated — independent of any other lifecycle action.

**Acceptance Scenarios**:

1. **Given** a card with prior transactions, **When** the customer requests their transaction
   history, **Then** transactions are returned in reverse-chronological order with status
   (approved/declined/pending/reversed), masked merchant detail, amount, and timestamp.
2. **Given** a card with no transactions yet, **When** the customer requests their transaction
   history, **Then** an explicit empty-state result is returned (not an error).
3. **Given** a transaction history larger than one page, **When** the customer pages through
   results, **Then** each page is bounded by the defined page-size limit (see Success
   Criteria) and pagination is stable even if new transactions arrive between page requests.
4. **Given** a transaction that was just authorized, **When** the customer requests history
   immediately afterward, **Then** the transaction appears within the defined time-to-consistency
   window (it is acceptable, and must be explicitly labeled, if very recent transactions briefly
   show as "pending" before settling).

---

### User Story 5 - Ops/Compliance Views Masked Card Data and Audit Trail (Priority: P2)

An authorized ops or compliance staff member looks up a customer's virtual card(s), masked
card details, transaction history, and full lifecycle audit trail to support a customer
inquiry, investigation, or compliance review.

**Why this priority**: Internal visibility is required for support and regulatory readiness
from day one of a regulated product, but it is a read-only capability layered on top of the
customer-facing data created by Stories 1–4.

**Independent Test**: Can be fully tested by having an authorized ops user look up a known
customer's card and confirming masked data and a complete, correctly-ordered audit trail are
returned, and that an unauthorized or out-of-scope user is denied — independent of any
fraud/dispute action.

**Acceptance Scenarios**:

1. **Given** an ops/compliance user with an active, scoped permission to view a specific
   customer's data, **When** they look up that customer's card, **Then** they see masked card
   data (never full PAN/CVV), current status, limits, and the complete ordered audit trail of
   lifecycle actions.
2. **Given** an ops user without permission scope for a given customer, **When** they attempt
   to look up that customer's card, **Then** access is denied, and the denied attempt itself is
   written to the audit trail (actor, target, `ACCESS_DENIED`, timestamp).
3. **Given** an ops user viewing a customer's audit trail, **When** they request the full
   history, **Then** entries are immutable, complete (no gaps), and displayed in chronological
   order with actor identity for every entry, including actions taken by other internal staff.

---

### User Story 6 - Ops Acts on a Fraud/Dispute Signal (Priority: P3)

An authorized ops/fraud staff member responds to a suspected-fraud or customer-reported dispute
signal by freezing the affected card and/or flagging the related transaction for review, within
their permission scope.

**Why this priority**: Fraud/dispute response is critical for risk containment but is a
lower-frequency, escalation-path flow that builds on card/transaction visibility (Story 5) and
the freeze mechanism (Story 2) rather than being a foundational flow itself.

**Independent Test**: Can be fully tested by flagging a known transaction as disputed/fraud and
confirming the linked card is frozen (if policy dictates), the transaction is marked
under-review, and the action is fully audited — independent of how the underlying transaction
was created.

**Acceptance Scenarios**:

1. **Given** an authorized fraud/ops user with permission scope for a customer, **When** they
   flag a transaction as suspected fraud, **Then** the transaction status becomes
   `Under Review`, the associated card is frozen, and an audit record (`FRAUD_FLAG_RAISED`,
   `CARD_FROZEN`) captures actor, reason code, and timestamp.
2. **Given** a transaction already marked `Under Review`, **When** a second authorized user
   attempts to flag the same transaction again, **Then** the system returns the current state
   without creating a duplicate flag or duplicate audit entry.
3. **Given** an ops user without fraud-action permission (e.g., a read-only support role),
   **When** they attempt to raise a fraud flag, **Then** the action is denied and the denied
   attempt is recorded in the audit trail.

---

### Edge Cases

| # | Scenario | Expected Behavior | Compliance/Audit Implication |
|---|----------|--------------------|-------------------------------|
| E1 | Customer requests card creation twice with the same idempotency key (network retry) | Exactly one card created; both responses return the same card reference | Only one `CARD_CREATED` audit entry; retry is not itself a distinct auditable event |
| E2 | Freeze and limit-update submitted concurrently for the same card | Both operations apply against a single consistent card version; conflicting writes are serialized with an explicit conflict outcome, never a silent lost update | Audit trail shows the true applied order with both actor identities |
| E3 | Limit set to zero, negative, non-numeric, or above the product-wide ceiling | Request rejected with a specific validation reason; previous limit unchanged | Rejected attempt is logged (not silently dropped) for support traceability |
| E4 | Card frozen while a transaction authorization is mid-flight | In-flight authorization resolves per pre-freeze rules; all subsequent attempts are declined | Both the authorization outcome and the freeze are independently audited with timestamps establishing order |
| E5 | Unfreeze attempted on a closed/terminated card | Rejected with "card is closed" reason; no state change | Rejected attempt logged; closed cards can never re-enter `Active` |
| E6 | Transaction history requested for a brand-new card with zero transactions | Explicit empty-state result, not an error or null | N/A |
| E7 | Transaction history requested immediately after a transaction posts | Transaction visible within the time-to-consistency budget; may show `Pending` before settling, explicitly labeled as such | N/A |
| E8 | Ops user queries a customer outside their permission scope | Access denied; no card/transaction data returned | Denied attempt is itself an audit event (actor, target, timestamp) |
| E9 | Same transaction flagged as fraud/dispute by two different ops users near-simultaneously | Second flag is a no-op returning current state; no duplicate flag/freeze | Only one `FRAUD_FLAG_RAISED` entry; both access attempts are traceable via correlation IDs |
| E10 | Customer requests a new card while already at the maximum concurrent active cards | Rejected with "limit reached" reason; no card created | Rejected attempt logged |
| E11 | Stale read: customer views card status immediately after freezing from another session/device | Status reflects the freeze within the defined consistency window; if a stale read is momentarily possible, it must never show `Active` as safe-to-spend when a decline would actually occur | No silent security gap: authorization decisions always use the latest committed state even if a read view is briefly stale |
| E12 | Card creation requested for an ineligible customer (suspended account, incomplete KYC) | Rejected with a user-visible, non-sensitive reason | Rejected attempt logged; no card materializes in any downstream view |
| E13 | Authorization request is within the per-transaction cap but would push the monthly aggregate total over its cap | Declined; decline reason explicitly identifies the monthly cap (not the per-transaction cap) as the binding constraint | Declined attempt logged with the specific limit type that triggered it, per FR-014 |
| E14 | Monthly aggregate cap resets at calendar-month boundary while a transaction is mid-authorization | The authorization is evaluated against whichever month's running total is in effect at the instant of the authorization decision (no partial/split evaluation) | Reset event itself generates no audit entry (FR-015); the authorization outcome is audited normally |
| E15 | Customer exceeds the per-action-type rate limit (e.g., rapid repeated freeze requests) | Request rejected with a specific rate-limit reason; underlying card state unchanged | Throttled attempt is logged (FR-029) but not written to the audit trail, since no state changed (FR-031) |
| E16 | An external dependency (vault, KYC, processor) is unavailable or times out mid-request | Request fails closed with a "temporarily unavailable / retry" outcome; no partial state committed | Failure is logged (FR-033); not an audit-trail event unless a state change had already committed before the dependency call |
| E17 | An external dependency returns a response that arrives successfully but fails an integrity check (e.g., a malformed/inconsistent `vault_reference`) | Treated identically to E16: fails closed, no partial state committed | Logged (FR-034); same audit-trail treatment as E16 |
| E18 | Customer spreads requests across create/freeze-unfreeze/limit-update to stay under each individual per-action-type rate limit | Aggregate cross-action-type limit still rejects once the combined ceiling is reached | Throttled attempt logged (FR-032), not audited (no state changed) |

## Requirements *(mandatory)*

### Functional Requirements

**Card Lifecycle**

- **FR-001**: System MUST allow an eligible end-user to create a new virtual card, resulting in
  a card record with status `Active`, a masked identifier (last 4 digits), an expiry, and a
  system-generated unique card ID.
- **FR-002**: System MUST enforce a maximum number of concurrent active virtual cards per
  customer account and reject creation requests beyond that maximum with a clear reason.
- **FR-003**: System MUST treat card-creation requests as idempotent: a repeated request
  carrying the same client-supplied idempotency key MUST return the original card reference
  rather than creating a second card.
- **FR-004**: System MUST allow the owning end-user to freeze an Active card, transitioning it
  to `Frozen` and causing subsequent new authorization attempts to be declined.
- **FR-005**: System MUST allow the owning end-user to unfreeze a `Frozen` card, transitioning
  it back to `Active` and restoring authorization capability.
- **FR-006**: System MUST treat freeze and unfreeze requests as idempotent: repeating a freeze
  request against an already-Frozen card (or unfreeze against an already-Active card) MUST
  return the current state without creating a duplicate state-change audit entry.
- **FR-007**: System MUST reject freeze/unfreeze requests against a permanently closed or
  terminated card with a clear, specific reason.
- **FR-008**: System MUST define and enforce a single resolution rule for concurrent,
  conflicting state-changing requests against the same card (e.g., simultaneous freeze and
  limit update): one request MUST win deterministically and the other MUST receive an explicit
  conflict/outcome response — never a silently dropped or silently overwritten write.

**Spending Limits**

- **FR-009**: System MUST allow the owning end-user to set an initial spending limit and update
  it thereafter, subject to validation (limit MUST be a positive amount not exceeding the
  product-wide ceiling).
- **FR-010**: System MUST reject invalid limit values (zero, negative, non-numeric, or above
  ceiling) with a specific, actionable validation reason, leaving the previous limit
  unchanged.
- **FR-011**: System MUST record both the prior and new limit value on every successful limit
  change as part of the audit trail.
- **FR-012**: System MUST NOT retroactively void an already-authorized pending hold when a
  limit is subsequently lowered; the new limit applies only to future authorization decisions.
- **FR-013**: System MUST support two concurrent spending-limit controls per virtual card: (a)
  a **per-transaction cap** applied to each individual authorization, and (b) a **monthly
  aggregate cap** applied to the running total of approved transactions within the current
  calendar month. Both limits are independently settable and updatable per Story 3.
- **FR-014**: System MUST decline an authorization attempt that would exceed either the
  per-transaction cap or the remaining monthly aggregate cap, whichever binds first, and MUST
  record which limit caused the decline for support/audit traceability.
- **FR-015**: System MUST reset the monthly aggregate cap's running total at the start of each
  calendar month (UTC), independent of any change to the cap's configured value; the reset
  itself is a system event and MUST NOT require customer action or produce a customer-facing
  audit entry (it is not a lifecycle action taken by an actor).

**Transaction Visibility**

- **FR-016**: System MUST allow the owning end-user to view their card's transaction history,
  including status (`Approved`, `Declined`, `Pending`, `Reversed`), amount, masked merchant
  detail, and timestamp.
- **FR-017**: System MUST return an explicit empty-state result (not an error) when a card has
  no transactions.
- **FR-018**: System MUST paginate transaction history results, bounded by a defined maximum
  page size (see Success Criteria), and pagination MUST remain stable under concurrent new
  transaction arrivals.

**Internal Ops/Compliance Access**

- **FR-019**: System MUST allow an authorized ops/compliance user to view a customer's masked
  card data, current status, limits, and transaction history strictly within that user's
  assigned permission scope.
- **FR-020**: System MUST deny access to any ops/compliance user attempting to view a
  customer's data outside their assigned permission scope, and MUST record the denied attempt
  in the audit trail.
- **FR-021**: System MUST expose the complete, immutable, chronologically-ordered audit trail
  of lifecycle actions for a given card to authorized ops/compliance users, including the
  actor identity for every entry (including other internal staff actions).
- **FR-022**: System MUST allow an authorized fraud/ops user to flag a transaction as suspected
  fraud or dispute, which MUST mark the transaction `Under Review` and freeze the associated
  card.
- **FR-023**: System MUST treat fraud-flag actions as idempotent: a repeated flag on an
  already-`Under Review` transaction MUST be a no-op returning current state, not a duplicate
  audit entry.
- **FR-024**: System MUST deny fraud-flag actions to ops users lacking fraud-action permission
  and MUST record the denied attempt in the audit trail.
- **FR-025**: System MUST bound the internal ops/fraud action surface to freeze-card-plus-flag-
  transaction only: an authorized fraud/ops user may freeze the affected card and mark the
  transaction `Under Review`, but deeper investigation, chargeback processing, and fund
  reversal are handled by an out-of-scope external dispute-management process. This feature
  does not model a full dispute case lifecycle (open/investigate/resolve/close) as first-class
  entities.

**Data Protection & Audit (cross-cutting)**

- **FR-026**: System MUST NOT expose full PAN, CVV, or other Tier-1 sensitive card data in any
  end-user-facing or ops-facing view, log, or export; only masked/tokenized references may
  appear outside the designated vault boundary.
- **FR-027**: System MUST produce an immutable, timestamped audit record for every
  state-changing action defined in this spec (create, freeze, unfreeze, limit change, fraud
  flag, and denied access attempts), capturing actor, action, prior state, new state, and
  reason/source where applicable.
- **FR-028**: System MUST NOT provide any update or delete capability against existing audit
  records.

**Observability (cross-cutting)**

- **FR-029**: System MUST emit a structured, machine-parseable log/event for every operation
  defined in this spec (successful or failed), containing at minimum a correlation ID, actor
  role, action name, outcome (success/failure/decline reason), and latency — distinct from,
  and in addition to, the compliance audit trail (FR-027).
- **FR-030**: Structured log/events produced under FR-029 MUST NOT include PAN, CVV, or any
  other Tier-1 sensitive data (cross-reference FR-026); only masked/tokenized references may
  appear.

**Rate Limiting (cross-cutting)**

- **FR-031**: System MUST enforce a per-customer, per-action-type rate limit — independent
  bounds for card creation, freeze/unfreeze, and limit updates, not one combined limit
  (Clarification, Session 2026-07-29). A request exceeding its action type's limit MUST be
  rejected with a specific, distinguishable reason and logged (FR-029), without writing a
  misleading audit "success" entry.
- **FR-032**: In addition to FR-031's per-action-type limits, the system MUST enforce a second,
  **aggregate cross-action-type rate limit** per customer per time window, summing requests
  across card creation, freeze/unfreeze, and limit-update actions together (Clarification,
  Session 2026-07-29). This closes the residual risk of an attacker spreading requests across
  action types specifically to stay under each individual per-action-type limit; exceeding the
  aggregate limit MUST be rejected with a distinguishable reason and logged (FR-029), same as an
  individual-limit rejection.

**External Dependency Failure Handling (cross-cutting)**

- **FR-033**: When an out-of-scope external dependency this feature relies on (KYC/onboarding,
  card vault/tokenization, payment processor) is unavailable or times out mid-request, the
  system MUST fail closed: reject the request with a specific "temporarily unavailable / retry"
  outcome, commit no partial state, and still emit a structured log/event (FR-029)
  (Clarification, Session 2026-07-29).
- **FR-034**: The fail-closed guarantee in FR-033 MUST extend to **integrity failures**, not
  only availability failures: if any of the three dependencies (KYC/onboarding, vault/
  tokenization, payment processor) returns a response that fails an integrity check (e.g., a
  malformed, inconsistent, or unverifiable `vault_reference`), the system MUST treat it
  identically to an unavailable/timed-out response — reject, commit no partial state, log
  (Clarification, Session 2026-07-29). This is applied uniformly across all three dependencies,
  not only the vault provider.

**Authentication Boundary (cross-cutting)**

- **FR-035**: System MUST treat baseline caller authentication (proving the caller is who they
  claim to be, as distinct from Permission Scope's authorization checks) as provided by an
  out-of-scope authentication system — the same boundary pattern used for KYC/onboarding,
  vault/tokenization, and the payment processor (Clarification, Session 2026-07-29).
- **FR-036**: For high-risk actions specifically — freeze, unfreeze, limit update, and fraud
  flag — the system MUST require a step-up/re-authentication signal from that out-of-scope
  authentication system, no older than a defined freshness window (see SC-013), and MUST
  reject the action (not merely warn) if that signal is missing or stale (Clarification,
  Session 2026-07-29). Card creation and transaction-history reads rely on baseline
  authentication only.

### Key Entities

- **Virtual Card**: Represents a single card issued to a customer. Key attributes: card ID
  (opaque, non-guessable), masked PAN (last 4 digits only), expiry, status
  (`Active`/`Frozen`/`Closed`), per-transaction spending cap, monthly aggregate spending cap,
  current monthly aggregate running total (resets each calendar month per FR-015), owning
  customer reference, creation timestamp. Full PAN/CVV are represented only as a reference
  into the vault boundary, never as an attribute of this entity as modeled here.
- **Transaction**: Represents an authorization attempt or posted transaction against a virtual
  card. Key attributes: transaction ID, card reference, amount, currency, status
  (`Approved`/`Declined`/`Pending`/`Reversed`/`Under Review`), masked merchant detail,
  timestamp.
- **Audit Record**: Represents one immutable entry in a card's lifecycle history. Key
  attributes: audit ID, card reference, actor identity + role, action type, prior state, new
  state, reason/source, timestamp, and an optional `external_case_reference` (Clarification,
  Session 2026-07-29) correlating an entry with an external system's case record (e.g., the
  out-of-scope dispute-management system referenced in FR-025) when applicable. Append-only;
  no update/delete path exists; exempt from data-subject erasure/correction requests
  (Clarification, Session 2026-07-29).
- **Permission Scope**: Represents the set of customers/cards an internal ops/compliance/fraud
  user is authorized to view or act upon. Key attributes: user/role identity, scope
  boundary (e.g., assigned customer segment or case), granted actions (view-only vs.
  fraud-action-capable). Distinct from — and layered on top of — the out-of-scope
  authentication system that establishes caller identity in the first place (FR-035); this
  entity governs *authorization* only, plus the step-up/re-authentication freshness check
  (FR-036) for high-risk actions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A customer can complete virtual card creation, end to end, in under 5 seconds
  from request to seeing the new card reflected in their own view, for at least 95% of
  requests (p95). *Assumed target* — instant-issuance is a baseline expectation for digital-first
  neobank card products.
- **SC-002**: A freeze or unfreeze action is reflected in authorization decisions within 2
  seconds for at least 99% of requests (p99), and reflected in the customer's own status view
  within 5 seconds for at least 99% of requests. *Assumed target* — freeze is a security control;
  slow propagation directly extends a fraud-exposure window, so it is held to the tightest
  budget in this spec.
- **SC-003**: A spending-limit change is enforced against new authorization attempts within 5
  seconds for at least 99% of requests (p99). *Assumed target* — matches freeze urgency since
  limit reduction is often also a loss-control action.
- **SC-004**: Transaction history reflects a newly-posted transaction within 10 seconds for at
  least 95% of requests (p95), with any transaction older than that window never shown as
  missing. *Assumed target* — balances near-real-time visibility against realistic settlement
  pipeline delays.
- **SC-005**: Transaction history pagination returns no more than 50 transactions per page and
  responds within 2 seconds (p95) per page. *Assumed target* — bounds both response size and
  perceived load latency for a scrolling list UI.
- **SC-006**: 100% of state-changing actions in scope (create, freeze, unfreeze, limit change,
  fraud flag, denied access attempts) produce a corresponding audit record — verified via
  reconciliation between the action log and the audit trail with zero unexplained gaps.
  *Non-negotiable target* — directly required by Principle II of the project constitution.
- **SC-007**: 0% of ops/end-user-facing views ever display a full, unmasked PAN or CVV —
  verified via review of every data-exposing flow in this spec against the
  Tier-1/Tier-2/Tier-3 classification. *Non-negotiable target* — directly required by
  Principle I of the project constitution.
- **SC-008**: A repeated (retried) create, freeze, unfreeze, or fraud-flag request with the
  same idempotency key never produces a second card, a duplicate state transition, or a
  duplicate audit entry — verified by a dedicated retry-safety test category for each such
  action.
- **SC-009**: At least 90% of end-users who attempt to freeze a card during a simulated
  lost-card scenario complete the action without contacting support. *Assumed target* — proxy
  for self-service trust and support-cost reduction.
- **SC-010**: The system supports at least 500 concurrent freeze/unfreeze requests
  system-wide without degrading the latency budget in SC-002. *Assumed target* — sized for a
  plausible fraud-wave or outage-driven spike in a mid-size neobank's active card base.
- **SC-011**: 100% of operations produce a structured log/event carrying a correlation ID
  (FR-029), such that an ops/support engineer can reconstruct the full request lifecycle
  (request → decision → outcome) for any single customer-reported incident using that
  correlation ID alone, without needing to query the compliance audit trail. *Non-negotiable
  target* — directly required by Principle IV of the project constitution.
- **SC-012**: The audit trail is retained indefinitely (no defined deletion) and available for
  compliance lookup at ≥99.9% read-availability. *Non-negotiable target* (Clarification,
  Session 2026-07-29) — audit records are the primary evidence for disputes and regulatory
  inquiries that can surface years later, so treating them as an expiring operational dataset
  would undermine Principle II. Audit records are explicitly **exempt from any data-subject
  erasure or correction request** (Clarification, Session 2026-07-29): this exemption is a
  deliberate, stated resolution of the tension with GDPR-style rights acknowledged elsewhere for
  cardholder PII, not a silent gap — actor identity and event data on an audit entry are
  preserved even if the corresponding customer or staff member later exercises an erasure right
  over their other (non-audit) data.
- **SC-013**: A high-risk action (freeze, unfreeze, limit update, fraud flag) is rejected 100%
  of the time when its step-up/re-authentication signal is missing or older than **5 minutes**.
  *Assumed target* (Clarification, Session 2026-07-29) — 5 minutes is a common step-up-auth
  freshness window in banking UX: short enough to limit a hijacked-session attack window, long
  enough that a customer isn't asked to re-authenticate mid-task.

## Assumptions

- Each customer account may hold multiple concurrent virtual cards up to a fixed maximum (see
  FR-002); the exact maximum is a product/risk-policy configuration value outside this spec's
  scope to pin down further, and is treated as a configurable ceiling rather than a hard-coded
  single number.
- Card creation eligibility (KYC status, account standing) is determined by an existing,
  out-of-scope onboarding/KYC system; this spec only defines the accept/reject behavior at the
  boundary, not the eligibility rules themselves.
- "Instant" freeze/unfreeze in the feature description is interpreted as the latency budgets in
  SC-002, not literally zero-latency, since all distributed systems have some propagation delay.
- Full PAN/CVV storage, tokenization, and vaulting are provided by an existing, out-of-scope
  card-vault/tokenization service; this spec defines the boundary and access rules around it
  (Principle I) but not the vault's internal implementation.
- Transaction authorization/settlement (the payment-network side of approving or declining a
  swipe) is assumed to be handled by an existing, out-of-scope processor integration; this spec
  defines how virtual-card state (frozen/limit) influences that decision and how the result is
  surfaced to users and ops, not the processor protocol itself.
- Notification of customers (e.g., push/SMS on freeze or fraud flag) is out of scope for this
  spec; it is a plausible follow-on feature but is not required for the lifecycle flows defined
  here.
- Baseline caller authentication and the step-up/re-authentication signal (FR-035, FR-036) are
  provided by an existing, out-of-scope authentication system (Clarification, Session
  2026-07-29); this spec defines only the freshness check at the boundary, not how that system
  authenticates a caller.
- The trigger that transitions a card into `Closed` (e.g., card replacement, account
  offboarding) is out of scope for this spec (Clarification, Session 2026-07-29); this spec
  only defines behavior *given* a card is already `Closed` (FR-007, edge case E5).
- This is a documentation-only specification per the project constitution: no code, API, or UI
  is implied to exist yet; all "system MUST" language describes required behavior for a future
  implementation phase, not a current running system.
