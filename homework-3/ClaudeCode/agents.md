# Agent Guidelines: Virtual Card Lifecycle Management

These are binding operating instructions for any AI coding agent (Claude Code, Copilot, Cursor,
or otherwise) working in this repository — both during the current documentation-only phase
and during any future implementation phase this specification package authorizes. They
operationalize `.specify/memory/constitution.md` and `specification.md` into concrete
day-to-day rules. Where this file and the constitution conflict, **the constitution wins**;
raise the conflict rather than silently picking one.

## 0. Phase awareness (read this first)

This repository is currently in a **documentation-only phase**. Do not write application code,
APIs, database migrations, or UI against this spec unless a human explicitly opens a new,
separate implementation phase and says so. If asked to "implement" something from
`specification.md` or `specs/001-virtual-card-lifecycle/tasks.md` without that explicit
authorization, stop and ask for confirmation instead of guessing that it's now in scope.

Everything below this section applies to **both** the current phase (writing/maintaining specs)
and the future implementation phase (writing code against them).

## 1. Tech stack assumptions

No tech stack is committed. `specification.md` and `plan.md` describe a **hypothetical**
single-backend-service architecture (`src/{models,services,api,lib}/`,
`tests/{contract,integration,unit,performance}/`) with:

- An OLTP-style transactional store for card/limit/transaction state.
- A **physically separate, append-only** store for audit records — do not colocate this with
  mutable operational data, and do not implement it as "mutable table + restricted
  permissions." The guarantee comes from the store having no update/delete code path, full
  stop.
- A structured logging pipeline distinct from the audit store (see §4).

If/when a real stack is chosen, update `plan.md`'s Technical Context first and treat that as the
source of truth — do not let code and `plan.md` diverge silently.

## 2. Domain rules (regulated FinTech / banking)

- **Money**: always an integer in minor units (cents) + an ISO 4217 currency code. Never a
  float, never a `Decimal` used as a float substitute without minor-unit discipline.
- **IDs**: always an opaque, non-guessable identifier (UUIDv4 or ULID). Never a sequential
  integer, never derived from PII.
- **PAN/CVV**: never modeled, stored, logged, or returned by this feature's own code beyond a
  masked `masked_pan` (last 4 digits) and an opaque `vault_reference` token into the external
  vault provider. If you find yourself adding a field that could hold a full card number,
  stop — that's almost certainly a Principle I violation.
- **Data tiers**: classify every new field as Tier-1 (PAN/CVV/full gov-ID — never persisted
  here), Tier-2 (masked/derived cardholder data — access-controlled, auditable), or Tier-3
  (aggregated/anonymized). When in doubt, treat it as Tier-1 and ask.
- **Regulatory framing**: PCI DSS-style card-data handling, SOC 2-style access/audit controls,
  and GDPR-style data-subject rights are all acknowledged design pressures — but audit records
  specifically are an explicit, documented **exemption** from erasure/correction requests
  (legal-obligation grounds; see `specification.md` § Audit & Logging). Do not "fix" this by
  quietly making audit records mutable or deletable.

## 3. Code style & structure

- Follow the file layout named in `specification.md` § Implementation Notes and `plan.md` §
  Project Structure exactly; do not invent parallel structures.
- One responsibility per service module (`card_service`, `limit_service`,
  `transaction_service`, `authorization_service`, `fraud_service`, `ops_view_service`,
  `authz_service`, `audit_service`, `reconciliation_service`) — do not merge unrelated concerns
  into one file for convenience.
- Cross-cutting helpers (`idempotency`, `concurrency`, `rate_limiter`, `dependency_guard`,
  `pagination`, `observability`, `formatting`) live in `src/lib/` and are consumed by services,
  not reimplemented per-service.
- Every entity field's type must be traceable to `data-model.md`; do not add, rename, or drop a
  field there without updating both `data-model.md` and any `contracts/*.md` that reference it.

## 4. Testing & verification expectations

- Every low-level task in `specification.md` / `tasks.md` ends with an acceptance criterion.
  Treat that criterion as the definition of done — do not mark a task complete without it.
- Test categories, by task type:
  - **Contract tests** (one per operation) assert the request/output shape documented in
    `contracts/*.md`, including every documented error code.
  - **Integration tests** cover every acceptance scenario and every edge case (E1–E16) named in
    `specification.md`.
  - **Performance tests** map 1:1 to every numbered Success Criterion (SC-001–SC-012); do not
    leave a Success Criterion without a named test case.
  - **Reconciliation checks** independently verify SC-006 (audit-vs-action-log gap) — this is
    not satisfiable by unit tests on individual write paths alone.
- Prefer writing the contract/integration test for a task before its implementation where the
  task list marks tests first; if you implement first, still write the test before marking the
  task done.
- Never claim a Success Criterion is met without describing (or running, once code exists) the
  specific test that verifies it.

## 5. Security & compliance constraints (non-negotiable)

- **Never** log, print, serialize, or otherwise emit a full PAN or CVV, in any environment,
  including debug/dev logs. This applies to both the audit trail (FR-027) and the structured
  observability log (FR-029) — both must exclude Tier-1 data, independently.
- **Always** write an Audit Record for every state-changing action and every denied
  access/action attempt — including ones that "obviously" don't need it. If an action changes
  state and has no matching Audit Record, that's a bug, not an optimization.
- **Always** prefer idempotent writes: every state-changing operation must accept a
  client-supplied idempotency key and short-circuit a repeat rather than re-executing.
- **Always** use optimistic concurrency (a `version` token) on mutable entities; a stale-version
  write must get an explicit conflict response, never a silent overwrite and never
  last-write-wins with no signal.
- **Always** check capability and scope-boundary permissions as two independent gates for
  internal (ops/compliance/fraud) actions; a failure of either must be independently
  deniable and independently audited.
- **Always** fail closed on external-dependency (KYC/vault/processor) unavailability **or
  integrity failure** (a response that arrives successfully but is malformed/inconsistent) —
  never fail open, never proceed with a cached/default value in place of a required dependency
  response, and never treat "the call succeeded" as equivalent to "the response is valid."
- **Always** enforce rate limits per-action-type, independently per customer — never a single
  combined counter across unrelated actions — **and** enforce a second, aggregate
  cross-action-type limit on top, so an attacker can't evade throttling by spreading requests
  across action types.
- **Always** require a fresh (≤5 minute) step-up/re-authentication signal before freeze,
  unfreeze, limit-update, or fraud-flag actions proceed; treat baseline authentication as an
  out-of-scope system boundary (like KYC/vault/processor), but never skip the step-up check for
  these four high-risk actions specifically.

## 6. How to treat edge cases and ambiguity

- The 16 documented edge cases (E1–E16 in `specification.md`) are not exhaustive by
  construction — if you find a plausible new one while implementing (e.g., a race condition the
  spec didn't anticipate), do not silently resolve it in code. Document it, propose an expected
  behavior, and flag it for a spec update (or run `/speckit-clarify` if working within Spec Kit).
- Never guess at a genuinely ambiguous requirement and proceed. If the spec doesn't say, that's
  a spec gap — say so explicitly rather than picking a plausible interpretation silently.
- When a spec change is needed, update `specs/001-virtual-card-lifecycle/spec.md` (or the
  relevant companion doc) **and** `specification.md` together — they must never diverge. Treat
  any discovered divergence as a bug to fix immediately, not a stylistic difference to leave.

## 7. Spec-Kit workflow expectations

This project was built using Spec Kit (`constitution → specify → clarify → plan → tasks →
analyze`). If you are continuing this work:

- Treat `.specify/memory/constitution.md` as supreme within this repo; a proposed change that
  conflicts with a principle needs an explicit constitution amendment (`/speckit-constitution`),
  not a workaround.
- Before treating any spec/plan/tasks change as final, re-run `/speckit-analyze` (or the
  equivalent manual cross-check) and confirm zero CRITICAL/HIGH findings remain.
- Keep `specs/001-virtual-card-lifecycle/tasks.md` and `specification.md`'s Low-Level Tasks
  section in sync — they share task IDs (T001–T065) on purpose so a reviewer can cross-reference
  either document.

## 8. Prohibited actions

- Do not write or scaffold application code, infrastructure, or a database schema during the
  current documentation-only phase.
- Do not weaken a non-negotiable target (SC-006, SC-007, SC-011, SC-012) to make an
  implementation easier — if a target seems unreasonable, raise it as a spec discussion, don't
  quietly relax it in code or in a task's acceptance criteria.
- Do not merge the audit trail and the structured observability log into one stream, even though
  they overlap in content — they have different retention, exemption, and access rules.
- Do not model the external dispute-case lifecycle (open/investigate/resolve/close) inside this
  feature — FR-025 bounds the internal fraud action surface to freeze + flag only, by design.
- Do not use `git push --force`, skip test suites, or bypass review gates without explicit human
  authorization, regardless of how confident the change seems.
