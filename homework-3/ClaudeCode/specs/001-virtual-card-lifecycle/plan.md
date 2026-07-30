# Implementation Plan: Virtual Card Lifecycle Management

**Branch**: `001-virtual-card-lifecycle` | **Date**: 2026-07-29 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-virtual-card-lifecycle/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

End-users create, freeze/unfreeze, set spending limits (per-transaction + monthly aggregate)
on, and view transaction history for a virtual card; internal ops/compliance/fraud staff view
masked card data and the full audit trail within their permission scope, and can freeze a card
plus flag a transaction for review in response to a fraud/dispute signal. Per the project
constitution (`.specify/memory/constitution.md`), **this phase produces specification
artifacts only** — this plan, its research/data-model/contracts/quickstart outputs, and the
downstream `tasks.md` are all documentation; no code, API, or UI is implemented. The Technical
Context below therefore describes an **assumed/hypothetical target architecture** — specific
enough that a future implementing team would not have to guess, but explicitly not a
commitment made or code written in this phase.

## Technical Context

**Language/Version**: N/A this phase — documentation-only deliverable (Constitution §
"Regulatory Scope & Data Governance"). No source code is authored under this plan.

**Primary Dependencies**: N/A this phase (hypothetical, for future implementers): an external
card-vault/tokenization provider (PAN/CVV custody), an external payment processor/network
integration (authorization decisioning), an existing KYC/onboarding system, and an existing
authentication system (baseline caller identity + step-up/re-authentication signal, FR-035/036)
— all treated as out-of-scope integrations per spec.md Assumptions.

**Storage**: N/A this phase (hypothetical): an OLTP-style transactional store for card, limit,
and transaction state, plus a separate **append-only** store for audit records (Principle II
requires no update/delete path on audit data — a strong argument for physically, not just
logically, separating audit storage from mutable operational state). Exact engine choice is an
implementation decision deferred beyond this homework's scope.

**Testing**: N/A this phase — no automated tests are written. Verification for this phase is
performed via the specification quality checklist (`checklists/requirements.md`), the
acceptance scenarios embedded in spec.md, and the manual validation walkthrough in
`quickstart.md`. Test *categories* (unit/integration/e2e) are documented as expectations for a
future implementation phase, not executed here.

**Target Platform**: N/A this phase (hypothetical: backend service reachable by a mobile/web
banking client); no platform commitment is made in a documentation-only phase.

**Project Type**: Specification/documentation package — this repository produces no runnable
project during this phase.

**Performance Goals**: Derived directly from spec.md Success Criteria: card creation ≤5s (p95,
SC-001); freeze/unfreeze authorization-path propagation ≤2s (p99, SC-002); limit enforcement
≤5s (p99, SC-003); transaction visibility ≤10s (p95, SC-004); ≥500 concurrent freeze/unfreeze
requests without degradation (SC-010).

**Constraints**: No PAN/CVV outside the vault boundary (Principle I, FR-026); every
state-changing action MUST be idempotent (Principle III, FR-003/006/023) and produce an
immutable audit record (Principle II, FR-027/028); every operation MUST produce a structured,
PAN/CVV-free log/event (Principle IV, FR-029/030); per-action-type AND aggregate cross-action
rate limits (FR-031, FR-032); fail-closed external-dependency handling covering both
availability and integrity failures (FR-033, FR-034); an out-of-scope authentication boundary
with mandatory step-up re-authentication (freshness ≤5 min, SC-013) for high-risk actions
(FR-035, FR-036); no code/API/UI in this phase (Constitution § "Regulatory Scope & Data
Governance").

**Scale/Scope**: Hypothetical mid-size neobank active card base, sized so the architecture
implied by this plan can plausibly meet SC-010 (≥500 concurrent freeze/unfreeze requests) and
SC-011 (100% correlation-ID log coverage) without redesign.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|---|---|---|
| I. Sensitive Data Protection & Least Privilege | PASS | spec.md FR-026; Key Entities note PAN/CVV are vault-only references; Regulatory Scope § data tiers (Tier-1/2/3); FR-035/FR-036 (authentication boundary + step-up re-auth for high-risk actions) reinforce least-privilege enforcement |
| II. Auditability & Regulatory Traceability | PASS | spec.md FR-027, FR-028, Audit Record entity, SC-006, SC-012 (durability/availability target); append-only audit store called out explicitly in Storage above |
| III. Reliability, Idempotency & Concurrency Safety | PASS | spec.md FR-003, FR-006, FR-008, FR-023, FR-031 (per-action-type rate limiting), FR-032 (aggregate cross-action-type rate limiting), FR-033 (fail-closed on dependency unavailability), FR-034 (fail-closed on dependency integrity failure), FR-036 (step-up re-auth freshness), E2/E9/E15/E16/E17/E18 edge cases, SC-008, SC-013 |
| IV. Observability Without Data Exposure | PASS (gap closed during this plan) | spec.md initially lacked a distinct observability requirement separate from the audit trail; **FR-029/FR-030 and SC-011 were added to spec.md during this planning pass** to close that gap before proceeding — see Complexity Tracking note below for full disclosure |
| V. Measurable Non-Functional Targets | PASS | spec.md SC-001…SC-013, all labeled assumed/non-negotiable with rationale |
| VI. Specification-Driven Traceability | PASS | spec.md FRs grouped by section that map 1:1 to User Stories 1–6; low-level task→objective tracing is the responsibility of the downstream `tasks.md` (Principle VI, Section "Specification Workflow & Quality Gates") |

**Result**: No unresolved gate violations. One gap (Principle IV) was found and remediated by
amending spec.md rather than accepted as complexity debt — see Complexity Tracking.

*Re-checked after Phase 1 design*: data-model.md and contracts/ (below) do not introduce any
new entity, flow, or field that reintroduces exposure of Tier-1 data, breaks idempotency, or
omits an audit/log requirement. Gate re-confirmed PASS.

## Project Structure

### Documentation (this feature)

```text
specs/001-virtual-card-lifecycle/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md         # Phase 1 output (/speckit-plan command)
├── quickstart.md         # Phase 1 output (/speckit-plan command)
├── contracts/             # Phase 1 output (/speckit-plan command)
│   ├── card-lifecycle.contract.md
│   ├── transactions.contract.md
│   └── ops-compliance.contract.md
├── checklists/
│   ├── requirements.md   # Spec quality checklist (/speckit-specify command)
│   ├── compliance.md     # Compliance/audit requirements-quality checklist (/speckit-checklist command)
│   └── security.md       # Security requirements-quality checklist (/speckit-checklist command)
└── tasks.md              # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

Not applicable this phase. Per the project constitution, Homework 3 delivers a specification
package only — `specification.md`, `agents.md`, editor/AI rules, and `README.md` at the
repository root (outside `specs/`) — and no `src/`, `tests/`, `backend/`, or `frontend/`
directories are created. A future implementation phase would choose a concrete structure
(e.g., a single backend service with `models/`, `services/`, `api/`, `tests/`) at that time,
informed by — but not committed to — the hypothetical architecture in the Technical Context
above.

**Structure Decision**: Documentation-only structure as shown above under
`specs/001-virtual-card-lifecycle/`; no source code structure is selected or created in this
phase.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|---------------------------------------|
| N/A — no violation is being carried forward | The one gap found (Principle IV / Observability) was fixed by amending spec.md (adding FR-029, FR-030, SC-011) during this planning pass rather than justified as an accepted exception | Accepting the gap as "complexity debt" was rejected because Principle IV is NON-NEGOTIABLE-adjacent cross-cutting guidance tied directly to regulated-environment operability; fixing the spec is strictly simpler than maintaining a documented exception indefinitely |
