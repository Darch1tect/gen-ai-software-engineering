# AI Agent Guidelines

## 1. Purpose

This file defines how an AI coding or documentation agent must work with the
Virtual Card Lifecycle Management specification.

The current homework is documentation-only. Do not create application code,
database migrations, infrastructure, API schemas, or executable tests unless a
later task explicitly authorizes implementation. References to such artifacts
in `specification.md` describe the hypothetical ending context.

## 2. Instruction Precedence

Apply instructions in this order:

1. The current user request.
2. `specification.md`, including its recorded decisions, policy requirements,
   acceptance criteria, and release gates.
3. This file.
4. `.github/copilot-instructions.md`.
5. Existing repository conventions.

If two requirements conflict, stop and identify the exact conflict. Do not
silently choose the less restrictive interpretation. Legal or regulatory
references are baselines, not legal advice or proof of current applicability.

## 3. Working Method

Before changing an artifact:

1. Read the relevant high-level and mid-level objectives.
2. Identify affected requirements, edge cases, acceptance criteria, and
   low-level tasks.
3. Check whether a value is a recorded decision, an assumed target, a
   configurable policy, or a final approval item.
4. Preserve traceability to the relevant MLO and specification section.
5. Make the smallest coherent change that satisfies the request.
6. Verify consistency across objectives, flows, edge cases, tests, tasks, and
   the traceability table.

An agent must not convert an assumption into permanent policy. New policy
values must be marked as assumptions or configuration candidates and assigned
an approval owner.

## 4. Hypothetical Implementation Stack

The specification is processor- and framework-independent. If implementation is
later authorized and no architecture decision supersedes this section, use this
starter stack:

- Python 3.12;
- FastAPI and Pydantic v2 for public and internal API boundaries;
- SQLAlchemy 2 and Alembic;
- PostgreSQL 16 for operational state, idempotency, and transactional outbox;
- a durable broker with at-least-once delivery;
- pytest, Hypothesis, and Testcontainers for verification;
- OpenTelemetry with allowlisted attributes;
- AWS `eu-central-1` as active production and `eu-west-1` as encrypted warm
  standby, subject to the regulated-entity controls in section 6.9.

Treat this stack as an agent default, not an approved production decision.
Preserve domain ports so the framework, database, broker, processor, identity
provider, and cloud services can be replaced without changing domain rules.

## 5. Architecture Rules

- Prefer a modular monolith until scale or regulatory isolation justifies
  extraction.
- Keep domain models independent of API, database, cloud, and processor models.
- Separate customer APIs, internal operations APIs, processor adapters,
  ingestion, reconciliation, audit, and privacy controls.
- Define external integrations as ports with explicit timeout, retry,
  idempotency, error-mapping, and reconciliation behavior.
- The processor is authoritative for processor/network status and events. The
  regulated entity's double-entry ledger is authoritative for booked money.
  Card and transaction stores are projections or workflow stores.
- Every customer, resource, event, queue, key, log, backup, support case, and
  processor programme must be bound to one regulated entity and data plane.
- Deny cross-entity and cross-region access by default. Never trust
  customer-supplied ownership, entity, tenant, or region identifiers.

## 6. Domain and Data Invariants

- Represent customer freeze and risk hold independently. A risk hold always
  wins, and releasing it must not erase an underlying customer freeze.
- `CLOSED` is terminal. Unknown or contradictory processor states fail closed
  and create reconciliation work.
- Use opaque public identifiers, UTC timestamps, timezone-aware internal types,
  and monotonic aggregate versions.
- Use integer minor units and an ISO 4217 currency code. Floating-point money is
  forbidden.
- Preserve the currency exponent used at calculation time.
- Ukraine purchase limits are customer-level across every card and wallet
  token. Apply the segment ceilings, calendar windows, rolling controls,
  pending/reversal/refund semantics, and approval tiers in section 4.
- Segment promotion must never increase a customer's configured limits
  automatically.
- Use stable processor transaction identifiers. Never deduplicate transactions
  by merchant name, amount, and time.
- Cursor pagination must use a stable snapshot boundary, authenticated opaque
  cursors, and deterministic ordering.
- Idempotency scope is `(actor, operation, resource, key)`. Store a request
  fingerprint and the original logical result. A changed payload must return
  `IDEMPOTENCY_CONFLICT`.
- Reconciliation and repair must be idempotent. Ambiguous repair must never make
  a card less restrictive.

## 7. Security, Privacy, and Compliance Rules

Never store, log, trace, export, place in analytics, or use in fixtures:

- full PAN, CVV, PIN, magnetic-stripe data, or authentication secrets;
- access tokens or raw strong-auth payloads;
- raw processor payloads;
- sanctions matches, AML investigation details, STR/SAR activity, or
  law-enforcement requests in customer-visible channels.

Additional mandatory controls:

- Perform server-side ownership authorization on every resource.
- Use least privilege, purpose limitation, reason codes, legal-entity scope,
  and separate authenticated identities for approvals.
- Require action-, session-, user-, challenge-, resource-, and parameter-bound
  SCA according to section 5.1.
- Keep internal reason codes separate from localized customer message codes.
- Use allowlists for API responses, logs, traces, exports, and support views.
- Audit successful, failed, and denied sensitive actions. A sensitive mutation
  must not proceed without its durable audit guarantee.
- Retention is selected by data category and issuing legal entity. Never apply
  the longest group period to all data.
- Legal holds must be scoped, reviewable, and issued or released only by the
  authorized roles in section 5.1.2.
- EEA customer data remains in the EEA. Restricted third-country access needs
  the applicable transfer mechanism, TIA, just-in-time grant, masking, MFA,
  session recording, EEA-controlled keys, and expiry.
- Identifiable regulated data must never enter a global analytics or control
  plane. Treat pseudonymized data as personal data unless an approved
  anonymization assessment establishes otherwise.
- Do not name a processor or vendor as approved until the qualification and
  subprocessor evidence required by sections 6.9 and 6.10 exists.
- Do not present the platform as the deposit taker, funds holder, ledger owner,
  or card issuer where the regulated sponsor or EMI holds that role.

## 8. Error and Customer-Communication Rules

- Return stable machine-readable codes and safe localized messages.
- Never return stack traces, policy rules, processor secrets, raw provider
  errors, card tokens, or confidential decision data.
- Conceal cross-customer resource probing using the same result as an unknown
  resource.
- Do not accuse a customer of fraud or promise an investigation completion time.
- Use the disclosure mapping and localized messages in section 6.7.
- Customer communication must distinguish a confirmed result from
  `PROCESSING`, degraded service, or an unconfirmed upstream outcome.

## 9. Code and Schema Conventions

These rules apply only if implementation is later authorized:

- Use explicit types at module boundaries and small domain-focused functions.
- Prefer immutable value objects for money, IDs, decision records, and
  normalized provider events.
- Keep domain exceptions separate from transport and provider exceptions.
- Use repositories and a unit of work at transaction boundaries; do not place
  domain logic in route handlers or ORM models.
- Use database constraints for uniqueness, version checks, entity binding, and
  append-only records in addition to application validation.
- Schema and event changes must be backward compatible for at least one
  deployed consumer version.
- Unknown enum values must map to safe behavior and emit metrics; they must not
  crash a consumer.
- Configuration and secrets must not be committed to source control.
- Comments explain regulatory or domain intent, not obvious syntax.

## 10. Testing and Verification Expectations

Every material change must identify the relevant verification layer:

- unit tests for domain transitions, validation, redaction, cursor handling, and
  error mapping;
- property tests for state-machine invariants, exact money, arbitrary event
  order, and duplicate delivery;
- integration tests for transactions, audit durability, idempotency, outbox,
  authorization, and entity isolation;
- processor contract tests for success, decline, timeout before/after
  acceptance, partial update, unknown enum, malformed webhook, and replay;
- end-to-end tests for the happy path and major failure paths using synthetic
  processor data only;
- security and privacy tests for object-level authorization, role/scope
  escalation, replay, injection, redaction, export access, transfer controls,
  retention, deletion, and backup restore;
- resilience tests for processor, database, broker, audit, notification, zone,
  and worker failures;
- performance tests against the assumed p95/p99, throughput, quota, burst, and
  backlog targets;
- manual Legal, Compliance, Privacy, Security, Operations, and regulated-entity
  approvals where automation cannot establish applicability.

Tests must prove both the permitted path and the denial/failure path. Do not use
tests that mutate an in-memory store directly as evidence that API
authorization, persistence, audit, or concurrency works.

## 11. Edge-Case Policy

For every write or event flow, consider at minimum:

- empty, duplicate, stale, malformed, unauthorized, and cross-entity input;
- concurrent conflicting actions;
- upstream timeout before and after acceptance;
- partial upstream success followed by local failure;
- duplicate, out-of-order, changed-body, and unknown provider events;
- audit, broker, notification, database, and regional failure;
- restore, replay, and worker restart;
- a more restrictive risk or legal control arriving concurrently;
- data expiry, legal hold, erasure request, and deleted data reappearing from a
  backup.

State the customer-visible outcome, authoritative system, audit effect, retry
behavior, and reconciliation path. Never handle an uncertain outcome by
claiming ordinary success or issuing a blind non-idempotent retry.

## 12. Completion Checklist

Before declaring a documentation task complete:

- no requirement contradicts `specification.md`;
- every new decision is classified as approved, assumed, configurable, or
  release-blocking;
- MLO, acceptance-criteria, edge-case, verification, and low-level-task
  references remain consistent;
- sensitive data and internal decision details are absent;
- regulated-entity boundaries and authoritative-system ownership are explicit;
- measurable targets are labeled as assumptions where appropriate;
- official regulatory references are described as baselines requiring the
  launch-time verification in section 0.3.1;
- changed Markdown links, headings, tables, and code fences render correctly;
- no implementation was added during this documentation-only homework.
