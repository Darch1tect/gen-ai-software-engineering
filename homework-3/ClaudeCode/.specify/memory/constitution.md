<!--
Sync Impact Report
==================
Version change: (unset template) → 1.0.0
Rationale for MAJOR: initial ratification of a previously unfilled template — treated as
the baseline version rather than a bump, per semantic versioning conventions for first release.

Modified principles: none (initial creation)
Added sections:
  - Core Principles (I–VI): Sensitive Data Protection & Least Privilege; Auditability &
    Regulatory Traceability; Reliability, Idempotency & Concurrency Safety; Observability
    Without Data Exposure; Measurable Non-Functional Targets; Specification-Driven Traceability
  - Regulatory Scope & Data Governance (Section 2)
  - Specification Workflow & Quality Gates (Section 3)
  - Governance
Removed sections: none

Templates requiring updates:
  - .specify/templates/plan-template.md — ✅ no change needed (Constitution Check gate is
    already generic/dynamic: "[Gates determined based on constitution file]")
  - .specify/templates/spec-template.md — ✅ no change needed (Edge Cases, Success Criteria,
    Assumptions sections already align with Principles I–VI)
  - .specify/templates/tasks-template.md — ✅ no change needed (task/story traceability format
    already supports Principle VI; no CLAUDE-only or agent-specific language found)
  - .claude/skills/speckit-*/SKILL.md — ✅ reviewed, no outdated agent-specific references found
  - README.md — ⚠ pending (not yet created; must reference this constitution's principles
    per Homework 3 deliverable requirements when authored)
  - agents.md — ⚠ pending (not yet created; must operationalize Principles I–VI as concrete
    agent rules when authored)

Follow-up TODOs:
  - TODO(RATIFICATION_DATE): none — ratification date set to the date this constitution was
    first adopted for this project (see below); no deferred placeholder remains.
-->

# Neobank Virtual Card Constitution

## Core Principles

### I. Sensitive Data Protection & Least Privilege (NON-NEGOTIABLE)

Full Primary Account Number (PAN), CVV, and other Tier-1 cardholder secrets MUST NOT appear
in plaintext in logs, specifications, error messages, support tooling descriptions, or any
artifact outside an explicitly designated vault/tokenization boundary defined in the data
model. Specifications and implementations MUST reference cardholder data only via masked
form (e.g., last 4 digits) or an opaque token/reference ID. Every actor role (end-user,
support, fraud, ops, compliance, finance) MUST be assigned an explicit least-privilege access
scope — the spec MUST state what each role can see and do, not leave it implied. Data in
transit and at rest MUST be described with concrete protection expectations (e.g., TLS 1.2+,
strong at-rest encryption) wherever the spec crosses a trust boundary.

**Rationale**: PAN/PII exposure is a severe, largely irreversible harm in a regulated
FinTech context (PCI DSS-class obligations). Specifying the vault boundary and access scopes
before any implementation exists prevents an AI agent or engineer from "guessing" a design
that leaks sensitive data by default.

### II. Auditability & Regulatory Traceability (NON-NEGOTIABLE)

Every state-changing action on a virtual card (creation, freeze, unfreeze, limit change,
replacement, transaction posting/reversal) MUST produce an immutable, timestamped audit
record capturing actor identity, action, prior state, new state, and reason/source. Audit
records MUST be treated as append-only within the spec's data model — no update or delete
path may be specified for them. In addition, every requirement MUST be traceable end-to-end:
high-level objective → mid-level objective → low-level task → acceptance criterion, so a
compliance reviewer or auditor can walk from a control back to the business objective it
satisfies.

**Rationale**: Regulated card programs require demonstrable control lineage for audits,
dispute handling, and regulator inquiries; unclear traceability is the most common cause of
findings in compliance reviews.

### III. Reliability, Idempotency & Concurrency Safety

Every write operation (create, freeze/unfreeze, limit update, transaction dispute intake)
MUST be specified as idempotent under client retry using an explicit idempotency key or
equivalent mechanism, and MUST define the expected outcome when the same request is repeated.
Every flow where two actions can race (e.g., a freeze and a limit change submitted near-
simultaneously, or two limit updates in flight) MUST document the resolution rule (e.g.,
last-write-wins with audit trail, optimistic-lock rejection, or explicit conflict error) —
"undefined behavior" is not an acceptable spec outcome for a money-adjacent flow.

**Rationale**: Retries, double-taps, and concurrent requests are routine in card UX and
degraded-network conditions; unspecified idempotency or concurrency behavior risks duplicate
holds, inconsistent card states, or silent data loss — all costly and hard to reverse once
implemented against real money movement.

### IV. Observability Without Data Exposure

Every operation MUST define structured, machine-parseable log/event expectations at minimum
containing a correlation ID, actor role, action name, outcome (success/failure/error code),
and latency — sufficient for ops, fraud, and support to diagnose an incident without
re-deriving it from the audit trail. These same log/event definitions MUST explicitly
exclude PAN, CVV, full account numbers, and other Tier-1 data (per Principle I); this
exclusion MUST be stated next to the logging requirement, not assumed.

**Rationale**: Operational visibility and data minimization are frequently in tension;
stating both requirements together in the same place prevents the common failure mode where
someone re-adds full PAN to a log line "just for debugging."

### V. Measurable Non-Functional Targets as First-Class Requirements

Every mid-level objective that touches a user- or ops-facing flow MUST carry at least one
measurable, testable target: a latency percentile, a read-after-write consistency window, a
rate limit, a pagination/batch size limit, or a throughput figure for a background job. Where
a number is hypothetical rather than sourced from a real SLA, it MUST be labeled an **assumed
target** with a one-line justification of why it is reasonable for FinTech UX or ops load —
vague language ("should be fast," "reasonably quick") is not an acceptable substitute.

**Rationale**: Unmeasurable performance language cannot be verified, tested, or used to size
infrastructure; explicit targets let a reviewer or AI agent self-check whether an objective is
actually met.

### VI. Specification-Driven Traceability

Every mid-level objective MUST decompose into one or more low-level tasks, and every
low-level task MUST (a) name the mid-level objective it serves and (b) end with an acceptance
criterion or definition-of-done phrased so an implementer or AI agent can check it off without
asking a clarifying question. Edge cases and failure modes MUST be enumerated as an explicit
list or table tied to the specific flow they affect (e.g., "freeze card while a transaction is
mid-authorization") rather than folded into generic prose.

**Rationale**: The graded/reviewable artifact for this project **is** the specification's
clarity and decomposition; a broken or implicit objective→task→criterion chain is the
single biggest source of ambiguity an implementing agent would otherwise have to guess past.

## Regulatory Scope & Data Governance

This phase of the project (Homework 3) is **documentation-only**: the only deliverables are
`specification.md`, `agents.md`, editor/AI rules (e.g. `.claude/`, `.cursor/rules/*.md`, or
`.github/copilot-instructions.md`), and `README.md`. No code, API, or UI implementation is in
scope; any code-like snippets appearing in these documents are illustrative pseudocode and
MUST be labeled as non-executable.

**Data classification** (MUST be used consistently across all deliverables):
- **Tier-1 (Sensitive/Regulated)**: full PAN, CVV, full government ID numbers. Never logged,
  never stored outside a designated vault/tokenization boundary described in the data model.
- **Tier-2 (Access-Controlled)**: masked PAN (last 4), cardholder name, spend limits, card
  status, transaction metadata (amount, merchant, timestamp). Access-controlled per role and
  auditable per Principle II.
- **Tier-3 (Low-Sensitivity)**: aggregated/anonymized analytics, non-identifying usage counts.

**Reference frameworks** (assumed applicable, not claimed as certified compliance): PCI
DSS-style card-data handling principles, SOC 2-style access and audit control expectations,
and GDPR-style data-subject rights (access, correction, deletion) MUST be acknowledged
wherever a deliverable touches cardholder PII.

**Money and identifier formatting**: all monetary values MUST be specified in integer minor
units (e.g., cents) paired with an ISO 4217 currency code — never floating point. All entity
IDs (card ID, transaction ID, audit record ID) MUST be specified as a stated ID scheme (e.g.,
UUIDv4 or ULID) so no implementer guesses precision, rounding, or collision behavior.

## Specification Workflow & Quality Gates

This feature follows the Spec Kit phase sequence: **constitution → specify → clarify → plan
→ tasks** (implementation is explicitly deferred beyond this homework's scope). Each phase's
output MUST be internally consistent with this constitution before the next phase begins.

`specification.md` is not considered complete until it contains, at minimum: a high-level
objective with an explicit scope boundary; several observable mid-level objectives;
a non-functional & policy section with measurable targets (Principle V); implementation
notes covering data handling, idempotency, and error semantics (Principle III); an explicit
beginning/ending context; and a low-level task list where each task cites the objective it
serves and carries acceptance criteria (Principle VI).

Every review pass (self-review or AI-agent-assisted) over any deliverable MUST check for:
(a) no remaining vague or unmeasurable claims where Principle V requires a number;
(b) no Tier-1 data referenced outside the vault boundary (Principle I);
(c) every low-level task traceable to a mid-level objective (Principle VI);
(d) edge cases, failure modes, and a verification approach present for each mid-level
objective (Principles II, VI).

Any change to a deliverable that touches security, audit, or data-handling behavior MUST be
flagged for a compliance-style review pass before being treated as final, even though this
project produces documentation rather than running code.

## Governance

This constitution supersedes ad hoc conventions for the `neobank-virtual-card` specification
package. Any deliverable (`specification.md`, `agents.md`, editor/AI rules, `README.md`) that
conflicts with a principle in this document MUST be revised, or the conflict MUST be recorded
as an explicit, justified exception rather than silently left unresolved.

**Amendment procedure**: proposed changes are made directly to this file, MUST include an
updated Sync Impact Report (prepended as an HTML comment, as above), and MUST bump the
version according to semantic versioning:
- **MAJOR**: removal or backward-incompatible redefinition of a principle that weakens a
  prior compliance, security, or traceability guarantee.
- **MINOR**: a new principle is added, or existing guidance is materially expanded.
- **PATCH**: wording clarifications, typo fixes, or non-semantic refinements.

**Compliance review**: before any deliverable is treated as final for submission, it MUST be
checked against every principle in this constitution; unresolved conflicts MUST be recorded
as an open TODO in that deliverable rather than dropped silently.

Runtime guidance for AI agents working in this repository lives in `agents.md` (domain and
tech rules) and the editor/AI rules files (naming, patterns, FinTech-sensitive defaults).
Where those documents conflict with this constitution, this constitution takes precedence.

**Version**: 1.0.0 | **Ratified**: 2026-07-29 | **Last Amended**: 2026-07-29
