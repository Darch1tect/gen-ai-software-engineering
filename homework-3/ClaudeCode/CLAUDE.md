# CLAUDE.md — Editor/AI Rules for this Repository

Project-specific rules for Claude Code (and any other AI assistant) working in this repo. This
file is the quick-reference companion to `agents.md` (fuller rationale) and
`.specify/memory/constitution.md` (governing principles). Read `agents.md` §0 first if you're
unsure whether code should be written at all right now — short answer: **not yet**, this is a
documentation-only phase.

## Naming conventions

- Audit action types: `SCREAMING_SNAKE_CASE` verb-object pairs, e.g. `CARD_CREATED`,
  `CARD_FROZEN`, `LIMIT_UPDATED`, `FRAUD_FLAG_RAISED`, `ACCESS_DENIED`. New action types follow
  the same pattern — never introduce a differently-cased or differently-shaped action type.
  Note: `CARD_CREATE_REJECTED` / `LIMIT_UPDATE_REJECTED` name the *rejected-attempt* variant of
  an action explicitly — don't reuse the success action type for a failure with a status flag.
- Error/decline codes: `SCREAMING_SNAKE_CASE`, specific and distinguishable, e.g.
  `CUSTOMER_NOT_ELIGIBLE`, `CARD_LIMIT_REACHED`, `CARD_CLOSED`, `VERSION_CONFLICT`,
  `INVALID_LIMIT_VALUE`, `MONTHLY_AGGREGATE_CAP_EXCEEDED`, `RATE_LIMIT_EXCEEDED`,
  `DEPENDENCY_UNAVAILABLE`, `INSUFFICIENT_PERMISSION`, `STEP_UP_REQUIRED`. Never return a bare
  `"error": true` or a generic `"invalid request"` — every rejection names its specific cause.
  Note: `RATE_LIMIT_EXCEEDED` covers both the per-action-type and the aggregate cross-action
  limit; `DEPENDENCY_UNAVAILABLE` covers both availability and integrity failures — the
  underlying `reason` field distinguishes the cause, not a separate code per cause.
- Entities: singular nouns matching `data-model.md` exactly (`Virtual Card`, `Transaction`,
  `Audit Record`, `Monthly Aggregate Counter`, `Idempotency Record`, `Permission Scope`) — file
  and class names derive directly from these, e.g. `src/models/card.py`,
  `src/models/audit_record.py`.
- Task/requirement IDs: `T###` (tasks), `FR-###` (functional requirements), `SC-###` (success
  criteria), `E##` (edge cases) — always zero-padded to match existing width, never renumbered
  without a full-document sync pass (see "What to avoid" below).

## Patterns to follow

- **Idempotency-first**: every state-changing function signature should take an
  `idempotency_key` as a first-class parameter, not an optional afterthought.
- **Explicit conflict, never silent overwrite**: any function writing to a versioned entity
  takes the expected `version` and returns a typed conflict result on mismatch — never a bare
  boolean or a swallowed exception.
- **Two-gate permission checks**: internal-actor authorization is always `capability` check +
  `scope_boundary` check, evaluated and denied independently — never a single combined
  `has_permission()` boolean.
- **Fail closed on dependencies**: wrap every external call (KYC, vault, processor) in the
  `dependency_guard` pattern — a timeout, error, **or integrity-check failure** from the
  dependency must produce a specific "unavailable, retry" outcome, never a fallback to a
  default/cached value that lets the request proceed.
- **Step-up freshness check, not a stored flag**: high-risk actions (freeze, unfreeze,
  limit-update, fraud-flag) validate a request-time `step_up_timestamp` against a 5-minute
  freshness window — this is a per-request check, not a persisted "is authenticated" boolean on
  the user/session record.
- **Audit + domain write atomicity**: a domain state change and its Audit Record write are one
  transaction — never two separate writes that could partially succeed.
- **Cursor pagination only**: list endpoints use an opaque position-marker cursor, never
  offset/limit.

## What to avoid

- Do not add a field, endpoint, or log statement that could carry a full PAN or CVV — masked
  (`masked_pan`, last 4) or tokenized (`vault_reference`) only.
- Do not implement audit-record update/delete "just for admin cleanup" — the store must have no
  such code path, period.
- Do not collapse the structured observability log and the audit trail into one write — they
  have different retention/exemption rules and serve different audiences (ops vs. compliance).
- Do not renumber `FR-###`/`SC-###`/`T###` IDs without updating every file that references them
  (`specification.md`, `specs/001-virtual-card-lifecycle/{spec,plan,tasks,data-model}.md`,
  `contracts/*.md`) in the same change — a partial renumber is worse than not renumbering.
- Do not add a new limit type, permission model, or dispute-handling capability without first
  checking whether it re-opens a scope boundary this spec deliberately closed (e.g., FR-025's
  freeze-plus-flag-only fraud action surface, or the out-of-scope card-closure trigger).
- Do not invent a rate limit, timeout, or retention number without labeling it an **assumed
  target** and stating why — see `specification.md` § Performance & Latency for the existing
  pattern to follow.

## FinTech-sensitive defaults

- Money: integer minor units + ISO 4217 currency code. Never float.
- IDs: opaque UUIDv4/ULID. Never sequential/guessable.
- Every rejection is audited **except** rate-limit throttling and dependency-unavailable
  failures, which are logged (structured log) but not audited, since no domain state changed —
  this is the one deliberate exception to "every rejection is audited"; don't generalize it
  further without checking `specification.md` § Audit & Logging first.
- Default to the stricter reading of any ambiguous requirement (deny over allow, log over
  silence, explicit conflict over silent merge) and flag the ambiguity rather than resolving it
  unilaterally in the permissive direction.

## Verification before calling anything "done"

- Every task's acceptance criterion (see `specification.md` § Low-Level Tasks or
  `specs/001-virtual-card-lifecycle/tasks.md`) must be demonstrably true, not just plausible.
- Re-run `/speckit-analyze` (or an equivalent manual cross-check) after any change touching more
  than one of {spec.md, plan.md, tasks.md, data-model.md, contracts/} before considering the
  change complete.
