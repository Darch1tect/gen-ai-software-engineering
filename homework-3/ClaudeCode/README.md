# Homework 3: Specification-Driven Design — Virtual Card Lifecycle Management

## Student & Task Summary

**Student**: Vitalii Roditieliev

**Summary**: This submission is a documentation-only specification package for a virtual card
lifecycle feature (create, freeze/unfreeze, per-transaction + monthly spending caps, transaction
history) for a regulated neobank, including an internal ops/compliance/fraud view with masked
data, permission scoping, and a bounded freeze-and-flag fraud response. No code, API, or UI was
implemented, per the homework's requirements. The package was produced using GitHub's Spec Kit
workflow inside Claude Code (`constitution → specify → clarify → plan → tasks → analyze`, with
two clarify rounds and two analyze passes), which gave the specification a level of layering,
traceability, and cross-artifact consistency checking that would have been hard to sustain by
hand across 36 functional requirements, 13 success criteria, 18 edge cases, and 71 low-level
tasks.

**Deliverables in this directory**:

| File | Purpose |
|---|---|
| `specification.md` | The required layered specification (High-Level Objective → Mid-Level Objectives → Non-Functional/Policy → Implementation Notes → Context → Low-Level Tasks), self-contained |
| `agents.md` | AI agent operating guidelines: tech stack assumptions, domain rules, testing/verification expectations, security/compliance constraints, edge-case handling |
| `CLAUDE.md` | Editor/AI rules: naming conventions, patterns to follow, what to avoid, FinTech-sensitive defaults |
| `README.md` | This file |
| `.specify/memory/constitution.md` | The project constitution: 6 non-negotiable principles governing the whole package |
| `specs/001-virtual-card-lifecycle/` | Full Spec Kit working-artifact trail: `spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`, `checklists/` — the detailed source material `specification.md` was synthesized from |

## Rationale

### Why a constitution-first, layered approach

The homework asks for traceability "from goals to tasks" and for compliance/security concerns to
appear as first-class spec content, not an afterthought. I addressed this by writing the
**constitution first** (`.specify/memory/constitution.md`), before a single line of the feature
spec existed. Six principles — Sensitive Data Protection & Least Privilege, Auditability &
Regulatory Traceability, Reliability/Idempotency/Concurrency Safety, Observability Without Data
Exposure, Measurable Non-Functional Targets, and Specification-Driven Traceability — became the
**gate** every later document had to pass, not a checklist applied retroactively. `plan.md`'s
Constitution Check table (re-evaluated before *and* after design) is the artifact that proves
this: it caught a real gap (no distinct observability requirement) mid-plan and the fix was to
amend the spec, not to accept the gap as "complexity debt."

I then let `specification.md`'s structure follow directly from the homework's own table (High-Level
Objective → Mid-Level Objectives → Non-Functional & Policy → Implementation Notes → Context →
Low-Level Tasks), but populated every section from the much more detailed Spec Kit artifacts
(`spec.md`'s 6 user stories and 32 FRs, `research.md`'s 8 architecture decisions,
`data-model.md`'s 7 entities, `tasks.md`'s 71 tasks) rather than writing `specification.md` from
scratch as a shallower summary. The two documents share IDs (`FR-###`, `SC-###`, `T###`) on
purpose, so a reader can cross-reference either one and never find a discrepancy.

### How I chose performance targets

Every numbered target in `specification.md` § Performance & Latency (and `spec.md`'s
SC-001–SC-012) is labeled either an **assumed target** (a reasonable, stated guess, not a real
SLA) or a **non-negotiable target** (one that operationalizes a constitution principle directly:
SC-006/audit completeness → Principle II, SC-007/no PAN exposure → Principle I,
SC-011/log correlation → Principle IV, SC-012/audit durability → Principle II). I derived the
assumed numbers by ranking flows by **fraud/loss exposure**, not by arbitrary round numbers:
freeze/unfreeze got the tightest latency budget (p99 ≤ 2s) because it's explicitly a
security-control flow where slow propagation directly extends an attacker's window, while card
creation and transaction-history visibility — which don't themselves gate loss — got looser
budgets (p95 ≤ 5s / ≤ 10s). This ranking logic is written out in `specification.md` right under
the targets table, so a reader doesn't have to take the numbers on faith.

### How I chose verification depth

The homework explicitly wants "test categories... as documentation" and "review checkpoints,"
not necessarily runnable tests (there's no code to test). I mapped this onto a **four-layer**
verification stack that mirrors how a real regulated-fintech team would gate a spec before
implementation, just applied to prose instead of code:

1. A **spec-quality checklist** (`checklists/requirements.md`, generic "is this spec
   well-formed" gate — 16 items).
2. **Two domain-specific checklists**, not one — I deliberately went beyond the generic gate
   and generated checklists scoped to the two highest-risk areas named in the homework's own
   constraints ("auditability... clear boundaries for sensitive data"):
   - `checklists/compliance.md` (33 items, audit/compliance focus) surfaced two real gaps (an
     unaddressed GDPR-erasure/audit-retention tension, and a missing external-dispute-system
     correlation field), resolved via a `/speckit-clarify` round.
   - `checklists/security.md` (34 items, technical security-control focus) surfaced three more
     gaps: no authentication requirement existed at all (only authorization/Permission Scope
     was specified), the fail-closed guarantee didn't cover dependency *integrity* failures
     (only availability), and the per-action-type rate limits had no aggregate safeguard
     against an attacker spreading requests across action types. All three were resolved via a
     second `/speckit-clarify` round.
   Both checklists did their job as "unit tests for requirements" — neither was a rubber-stamp.
3. **Cross-artifact static analysis** (`/speckit-analyze`, run three times, once after each
   clarify round) — a mechanical consistency pass across spec/plan/tasks/data-model/contracts
   that caught real defects a human proofreading pass likely would have missed: a
   requirement-ID scheme break (twice — I made the identical mistake again on the second
   clarify round before catching it), a foundational task built but never wired into its six
   consumers, and — after the security round specifically — six new companion-document drift
   points spanning `plan.md`, `tasks.md`, `data-model.md`, `contracts/`, `quickstart.md`, and
   `specification.md` itself.
4. **Per-task acceptance criteria + a scenario script** (`tasks.md`'s 71 tasks each end with a
   definition of done; `quickstart.md` Part B is now a 7-scenario end-to-end script) — this is
   the layer a future implementer would actually execute against.

I chose this depth (rather than a single pass) because the homework's grading criteria reward
"how well you anticipate failure modes, verification, and non-functional expectations" — a
single-pass spec would have shipped with the GDPR/audit tension, the missing authentication
requirement, and the unwired rate-limiter/dependency-guard tasks all still latent, and I think
finding and fixing those in the specification phase — including the cost of re-running the
consistency pass every time a clarify round changes requirement IDs — is exactly the point of
doing specification-driven design in the first place.

## Industry Best Practices Applied

| Practice | Where it appears | Why it matters here |
|---|---|---|
| PCI DSS-aligned data tiering & vault boundary (never store/log full PAN/CVV; only masked/tokenized references) | `specification.md` § Non-Functional & Policy → Security & Privacy; `.specify/memory/constitution.md` Principle I; `specs/.../data-model.md` Virtual Card entity | Card data is the single highest-liability asset in this domain; keeping it structurally out of this feature's own data model (not just access-restricted) is the standard PCI DSS scope-reduction pattern |
| Immutable, append-only audit trail (no update/delete code path, not just restricted permissions) | `specification.md` § Audit & Logging; FR-027/FR-028; `specs/.../data-model.md` Audit Record; `specs/.../research.md` #1 | Standard SOC 2 / financial audit control — evidentiary integrity depends on the write path itself, not on trusting that nobody misuses an update permission |
| Idempotency keys on every state-changing operation | `specification.md` § Implementation Notes; FR-003/006/023; `specs/.../research.md` #2 | Networks retry; without this, a client timeout-and-retry on card creation or a freeze could double-charge or double-act |
| Optimistic concurrency control (version tokens, explicit conflict responses) | `specification.md` § Implementation Notes; FR-008; `specs/.../research.md` #3 | Avoids both silent lost-updates and the throughput cost of pessimistic locking on a low-write-contention entity |
| Per-action-type rate limiting | `specification.md` § Reliability & Concurrency; FR-031; edge case E15 | Explicitly required by the homework's own cross-cutting ask ("rate limits" as a first-class NFR), and a standard abuse/enumeration defense |
| Fail-closed external-dependency handling (availability *and* integrity failures) | `specification.md` § Reliability & Concurrency; FR-033/FR-034; edge cases E16/E17 | In a money-adjacent flow, "fail open" on a vault/processor timeout or a corrupted response is a much worse failure mode than a safe decline-and-retry |
| Aggregate cross-action-type rate limiting on top of per-action-type limits | `specification.md` § Reliability & Concurrency; FR-031/FR-032; edge case E18 | Closes the residual risk of an attacker spreading requests across action types to evade any single limit — surfaced by the security checklist, not assumed upfront |
| Step-up/re-authentication for high-risk actions, with baseline auth as an out-of-scope boundary | `specification.md` § Security & Privacy; FR-035/FR-036; SC-013 | A regulated card feature had no authentication requirement at all until a dedicated security checklist caught the gap — closing it without dragging a full auth architecture into scope |
| Two-gate least-privilege authorization (capability × scope, independently deniable/auditable) | `specification.md` § Security & Privacy; FR-019/020; `specs/.../research.md` #7 | Lets "can this role do X" and "for which customers" be reasoned about and denied separately — a common gap in simpler single-flag RBAC |
| Structured, correlation-ID-based logging kept separate from the compliance audit trail | `specification.md` § Audit & Logging; FR-029/030; `specs/.../research.md` #5 | Operational debugging (ops/support) and compliance evidence (regulators/disputes) have different audiences, retention rules, and content needs — conflating them is a common anti-pattern this spec explicitly avoids |
| Money as integer minor units + ISO 4217 currency code | `specification.md` § Implementation Notes; `.specify/memory/constitution.md` money/ID formatting rule | Avoids the classic floating-point rounding-error class of financial bugs |
| Cursor-based pagination over offset/limit | `specification.md` § Implementation Notes; FR-018; `specs/.../research.md` #8 | Offset pagination drifts under concurrent inserts, which is the common case (not the edge case) for a reverse-chronological transaction feed |
| Explicit legal-basis reasoning for a GDPR-vs-retention tension, rather than silent interpretation | `specification.md` § Audit & Logging; SC-012 clarification, `spec.md` § Clarifications | Surfaced by the compliance checklist (CHK030) and resolved explicitly rather than left ambiguous — the kind of decision a real compliance review would insist on documenting |
| Assumed-target labeling for all non-authoritative SLA-style numbers | `specification.md` § Performance & Latency | Distinguishes "we picked this and here's why" from "this is a contractual SLA," so a future team knows which numbers are safe to renegotiate |
| Constitution-gated, multi-pass spec review (checklist → domain checklist → static cross-artifact analysis) before treating a spec as final | `specs/.../checklists/`, two `/speckit-analyze` reports (see conversation history / `specs/.../plan.md` Constitution Check) | Mirrors real pre-implementation design-review and security-review gates in a regulated engineering org, applied here to prose artifacts since no code exists yet |
