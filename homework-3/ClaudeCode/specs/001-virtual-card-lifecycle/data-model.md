# Data Model: Virtual Card Lifecycle Management

**Purpose**: Concretize the Key Entities from `spec.md` into fields, relationships, validation
rules, and state transitions, informed by the decisions in `research.md`. This is a
**hypothetical** data model for a future implementation phase — no database or code exists yet.

## Entity Overview

```text
Customer (external/out-of-scope) ──< Virtual Card >── Monthly Aggregate Counter
                                        │
                                        ├──< Transaction
                                        ├──< Audit Record
                                        └──< Idempotency Record

Permission Scope ── references ──> Customer (scope boundary)
```

## Virtual Card

Represents a single card issued to a customer (spec.md Key Entities).

| Field | Type | Notes |
|---|---|---|
| `card_id` | opaque ID (e.g., UUIDv4/ULID) | Non-guessable, per Constitution money/ID formatting rule |
| `customer_id` | reference | Points to an out-of-scope Customer/account record (KYC owned elsewhere) |
| `nickname` | string, optional | Customer-supplied label (e.g., "Groceries card"); display-only, never used as an identifier or lookup key |
| `masked_pan` | string, 4 digits | Last 4 digits only; full PAN never stored here (Principle I) |
| `vault_reference` | opaque token | Reference into the external vault/tokenization provider — not the PAN itself |
| `expiry` | month/year | Display-only; issuance/renewal mechanics are out of scope |
| `status` | enum: `Active`, `Frozen`, `Closed` | See State Transitions below |
| `per_transaction_cap` | integer minor units + ISO 4217 currency code | FR-013; must be > 0 and ≤ product-wide ceiling (FR-010) |
| `monthly_aggregate_cap` | integer minor units + ISO 4217 currency code | FR-013; must be > 0 and ≤ product-wide ceiling |
| `version` | integer, monotonically increasing | Optimistic concurrency token (research.md #3); required on every write |
| `created_at` | timestamp | Immutable once set |

**Validation rules**:
- `per_transaction_cap` and `monthly_aggregate_cap` MUST each independently satisfy FR-010
  (positive, not exceeding ceiling); one cap's value does not constrain the other's range.
- A write to `status`, `per_transaction_cap`, or `monthly_aggregate_cap` MUST supply the
  `version` it read; a stale `version` is rejected with an explicit conflict response (FR-008).
- Card count per `customer_id` with `status IN (Active, Frozen)` MUST NOT exceed the
  configured per-account maximum (FR-002) at creation time.

**State Transitions**:

```text
        create (FR-001)
              │
              ▼
          [Active] ───freeze (FR-004)───▶ [Frozen]
              │  ◀──unfreeze (FR-005)───────┘
              │
              │  close (out-of-scope trigger, e.g. replacement/
              │  offboarding — see note below)
              ▼
          [Closed]  (terminal; no transition out, FR-007)
```

*Modeling note*: this spec (Stories 1–6) defines how a card enters `Active`, and how it moves
between `Active`/`Frozen`. It does **not** define the action that transitions a card into
`Closed` — that trigger (e.g., a card-replacement or account-offboarding flow) is treated as an
out-of-scope adjacent feature, consistent with spec.md's Assumptions about out-of-scope
adjacent systems. `Closed` is modeled here only because edge case E5 and FR-007 require
well-defined behavior *given* a card is already in that state.

## Monthly Aggregate Counter

Supports FR-013/FR-014/FR-015; not directly named in spec.md's Key Entities but required to
implement the monthly aggregate cap without recomputing from the full transaction ledger on
every authorization (research.md #4).

| Field | Type | Notes |
|---|---|---|
| `card_id` | reference | Composite key with `calendar_month` |
| `calendar_month` | `YYYY-MM` (UTC) | Composite key with `card_id`; a new row is implicitly created the first time a month is touched (FR-015) |
| `running_total` | integer minor units | Incremented atomically at authorization time (approved transactions only) |
| `updated_at` | timestamp | Last increment time |

**Validation rules**: `running_total` MUST only ever increase for a given `(card_id,
calendar_month)` — it is never decremented (a `Reversed` transaction affects future
authorization decisions only insofar as it is a separate, explicitly-audited event; it does not
retroactively rewrite a past month's counter).

## Transaction

Represents an authorization attempt or posted transaction (spec.md Key Entities).

| Field | Type | Notes |
|---|---|---|
| `transaction_id` | opaque ID | Non-guessable |
| `card_id` | reference | |
| `amount` | integer minor units | Never floating point (Constitution money-formatting rule) |
| `currency` | ISO 4217 code | |
| `status` | enum: `Approved`, `Declined`, `Pending`, `Reversed`, `Under Review` | `Under Review` set via FR-022 |
| `decline_reason` | enum, nullable | e.g. `PER_TRANSACTION_CAP_EXCEEDED`, `MONTHLY_AGGREGATE_CAP_EXCEEDED`, `CARD_FROZEN`, `CARD_CLOSED` — required whenever `status = Declined` (FR-014) |
| `masked_merchant` | string | Never full raw merchant payment-network payload |
| `occurred_at` | timestamp | |

**Validation rules**: `status = Declined` MUST carry a non-null `decline_reason` identifying
exactly one binding constraint (FR-014); a transaction MUST NOT be both `Approved` and later
silently mutated to a different amount (amount is immutable once set — corrections happen via
a new `Reversed`-linked transaction, not an edit).

## Audit Record

Represents one immutable entry in a card's lifecycle history (spec.md Key Entities).

| Field | Type | Notes |
|---|---|---|
| `audit_id` | opaque ID | |
| `card_id` | reference, nullable | Nullable only for a denied-access attempt against a customer with no resolvable card in the actor's scope (FR-020/E8) |
| `actor_id` | reference | The end-user or internal staff member who performed the action |
| `actor_role` | enum: `end_user`, `ops`, `compliance`, `fraud`, `support` | |
| `action_type` | enum: `CARD_CREATED`, `CARD_CREATE_REJECTED`, `CARD_FROZEN`, `CARD_UNFROZEN`, `LIMIT_UPDATED`, `LIMIT_UPDATE_REJECTED`, `FRAUD_FLAG_RAISED`, `ACCESS_DENIED` | Extensible; every state-changing FR in spec.md maps to exactly one `action_type` |
| `prior_state` | structured snapshot, nullable | e.g., prior limit value, prior status |
| `new_state` | structured snapshot, nullable | e.g., new limit value, new status |
| `reason` | string, nullable | Validation failure reason, fraud reason code, etc. |
| `correlation_id` | reference | Links to the structured log/event for the same request (FR-029), without duplicating log content into the audit store |
| `external_case_reference` | opaque string, nullable | Correlates this entry with an external system's case record (e.g., the out-of-scope dispute-management system, FR-025) when applicable; null for entries with no external counterpart |
| `created_at` | timestamp | |

**Validation rules**: append-only — **no schema field or API surface for update/delete exists**
(FR-028; research.md #1). Every row, once written, is immutable and exempt from data-subject
erasure/correction requests (legal-obligation/legitimate-interest grounds).

## Idempotency Record

Supports FR-003/FR-006/FR-023 (research.md #2); not named in spec.md's Key Entities but
required to implement idempotent writes.

| Field | Type | Notes |
|---|---|---|
| `idempotency_key` | client-supplied string | Composite key with `actor_id` + `action_type` (a key is scoped to one actor performing one action type, so two different actions can't collide on a coincidentally-equal key) |
| `actor_id` | reference | |
| `action_type` | enum | Matches Audit Record `action_type` |
| `result_reference` | reference | The entity ID (e.g., `card_id`, `transaction_id`) produced by the original request |
| `created_at` | timestamp | |
| `retention_expires_at` | timestamp | *Assumed target*: keys retained 24h, matching typical client-retry windows; beyond this, a repeated key is treated as a new request rather than a dedupe hit |

## Rate Limit Counter

Supports FR-031 (per-action-type) and FR-032 (aggregate cross-action-type); not previously
named as a distinct entity even for FR-031, closed here for completeness alongside the FR-032
addition.

| Field | Type | Notes |
|---|---|---|
| `customer_id` | reference | Composite key with `scope` and `window_start` |
| `scope` | enum: `create`, `freeze_unfreeze`, `limit_update`, `aggregate` | `aggregate` is the FR-032 cross-action-type counter; the other three are FR-031's independent per-action-type counters |
| `window_start` | timestamp | Start of the current rate-limit window |
| `request_count` | integer | Incremented atomically per request; compared against the configured ceiling for `scope` |

**Validation rules**: a request MUST be checked against both its specific per-action-type
counter (`scope != aggregate`) AND the `aggregate` counter; exceeding either rejects with
`RATE_LIMIT_EXCEEDED` (FR-031, FR-032).

## Step-Up Authentication Signal (request-time input, not a persisted entity)

Supports FR-035/FR-036. This feature does **not** persist authentication signals — baseline
authentication and the step-up/re-authentication signal are both owned by the out-of-scope
authentication system (FR-035). A high-risk action's request carries a `step_up_timestamp`
(when the caller last completed step-up authentication); this feature only validates that
`now() - step_up_timestamp <= 5 minutes` (SC-013) before proceeding, and rejects with
`STEP_UP_REQUIRED` otherwise. No new persisted field exists on Virtual Card or any other entity
for this — it is a per-request check, not stored state.

## Permission Scope

Represents what an internal ops/compliance/fraud user may view or act upon (spec.md Key
Entities; research.md #7).

| Field | Type | Notes |
|---|---|---|
| `scope_id` | opaque ID | |
| `user_id` | reference | Internal staff identity |
| `capability` | enum: `view_only`, `fraud_action_capable` | Determines *what* actions are permitted (FR-024/FR-025) |
| `scope_boundary` | reference/list | Which customers this scope applies to (e.g., assigned segment or case list) — determines *who* it may be exercised against (FR-019/FR-020) |
| `granted_at` | timestamp | |
| `revoked_at` | timestamp, nullable | A revoked scope MUST behave identically to a scope that never existed for authorization purposes |

## Cross-Entity Invariants

- Every row written to **Virtual Card**, **Transaction** (status changes only, not every read),
  or **Permission Scope** as the result of an actor's request MUST have a corresponding
  **Audit Record** row in the same logical transaction (Principle II, FR-027) — never written
  asynchronously in a way that could succeed without the other.
- Every request handled by this feature MUST produce a structured log/event carrying a
  `correlation_id` (Principle IV, FR-029), independent of whether an Audit Record was also
  written (e.g., a successful read produces a log/event but no Audit Record).
- No entity in this data model stores full PAN or CVV; the only sensitive-data reference is
  `Virtual Card.vault_reference`, an opaque token resolvable only by the external vault
  provider (Principle I).
