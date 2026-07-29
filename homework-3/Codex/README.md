# Homework 3 — Specification-Driven Design

## Student and task summary

- **Student:** Vitalii Roditieliev
- **Assignment:** Homework 3 — Specification-Driven Design
- **Feature:** Regulated virtual card lifecycle management
- **Delivery model:** Documentation only; no application implementation

This submission defines an implementation-ready specification package for
creating and controlling tokenized virtual cards, managing customer-level
purchase limits, presenting privacy-safe transaction history, and supporting
operations, compliance, reconciliation, and audit workflows.

Ukraine is the starter market through a licensed Ukrainian sponsor bank. The
design also establishes a controlled expansion path to a Polish electronic-money
institution, Romanian passporting, and a separately regulated Moldovan market.

## Deliverables

| Artifact | Purpose |
|---|---|
| [`specification.md`](specification.md) | Layered product, domain, policy, architecture, failure-mode, verification, and low-level task specification |
| [`agents.md`](agents.md) | Full operating contract for AI agents, including domain invariants, assumed stack, security, compliance, edge-case, and verification rules |
| [`.github/copilot-instructions.md`](.github/copilot-instructions.md) | Concise editor/AI rules applied during day-to-day authoring |
| [`README.md`](README.md) | Submission overview, design rationale, and mapping of industry practices to the specification |

## How to review the package

1. Start with sections 0–1 of `specification.md` for scope, market model, and
   the high-level objective.
2. Review the observable outcomes in section 4.
3. Review the security, privacy, audit, reliability, and performance
   requirements in section 5.
4. Review builder guardrails and regulated operating controls in section 6.
5. Validate key flows and failure behavior in sections 7–8.
6. Check verification and release gates in section 9.
7. Confirm that the 16 low-level tasks in section 11 trace back to MLOs through
   section 12.
8. Read section 13 last to distinguish recorded decisions from remaining
   launch approvals.

## Rationale

### Why the specification is layered

The assignment is intended to be executable by both an engineering team and an
AI agent without relying on unstated context. The document therefore separates:

- the business and user outcome;
- observable mid-level objectives;
- non-functional and policy requirements;
- implementation guardrails;
- beginning and ending workspace context;
- executable low-level tasks with definitions of done.

This structure prevents architecture details from replacing product outcomes
and makes each implementation slice traceable to a measurable objective.

### Why the scope is a virtual card lifecycle

Virtual card controls are small enough to decompose within one homework but
still expose realistic financial-system problems:

- irreversible or uncertain external side effects;
- processor and local-state disagreement;
- concurrent lifecycle controls;
- exact monetary limits;
- transaction event normalization;
- privileged operations;
- immutable evidence;
- ownership, privacy, and regulated-entity boundaries.

Physical cards, onboarding/KYC implementation, money movement, chargebacks,
rewards, replacement, PIN management, and general ledger implementation remain
outside the delivery scope so the document stays deep rather than broad.

### Why the market and entity model is explicit

A generic claim that the product is “EU compliant” would hide who issues the
card, who holds funds, who owns the ledger, and which law and regulator apply.
Sections 0.2, 0.3, 5.1, and 6.9 therefore separate:

- the Ukrainian sponsor-bank launch;
- the proposed Polish EMI and Romanian passporting path;
- the separate Moldovan sponsor or licensed entity;
- the data, keys, processor programmes, support access, reporting, and audit
  evidence belonging to each regulated entity.

Regulatory citations are deliberately treated as baselines. Section 0.3.1
requires a staged, dated Legal/Compliance verification before each launch and
continuous monitoring afterward.

### Why the architecture uses projections and reconciliation

The selected feature spans systems with different authority. Section 6.8 assigns
booked money to the regulated double-entry ledger and processor/network records
to the card processor. The card and transaction databases are projections and
workflow stores.

This division avoids treating a responsive read model as a financial ledger. It
also explains why the specification requires:

- idempotent commands;
- a transactional outbox;
- durable webhook ingestion;
- duplicate and out-of-order event handling;
- explicit unconfirmed states;
- scheduled and on-demand reconciliation;
- safe repair that never weakens a control under ambiguity.

### How performance targets were chosen

Sections 5.3 and 5.4 label latency, availability, recovery, throughput, page
size, rate limit, and traffic values as assumed planning targets.

The targets balance:

- interactive customer expectations for card reads and controls;
- the additional latency of processor confirmation;
- durable persistence before webhook acknowledgement;
- operational access to recent audit evidence;
- recovery of projection drift before it becomes prolonged customer impact;
- burst and backlog capacity rather than average traffic alone.

They are not represented as guaranteed production policy. Processor selection,
contracted quotas, production telemetry, and updated traffic forecasts must
validate or replace them.

### Why verification is extensive

Happy-path examples are insufficient for financial controls. Section 9 maps each
MLO to evidence and requires unit, property, integration, contract, end-to-end,
security, performance, resilience, and manual compliance review.

The fixture set intentionally includes:

- every card state and contradictory control flags;
- exact-money boundaries and currency exponents;
- duplicate, changed-body, and out-of-order provider events;
- accept-then-timeout and partial provider updates;
- cross-customer and cross-entity access attempts;
- audit, broker, notification, processor, database, and restore failures.

Release gates make missing evidence visible and attributable instead of allowing
an assumed control to pass silently.

## Industry best practices and where they appear

| Practice | Why it matters | Specification location |
|---|---|---|
| Clear regulated-provider and issuer roles | Prevents misleading customers and unclear accountability | Sections 0.1–0.2 |
| Launch-time regulatory verification | Avoids relying on stale or superseded legal references | Sections 0.3–0.3.1, 9.4 |
| Explicit domain state machine | Prevents impossible or less-restrictive card states | Sections 3.2, 7.2; Task 1 |
| Exact integer money | Avoids rounding and serialization loss | Sections 6.2, 7.3; Task 2 |
| Customer-level multi-card limits | Prevents bypass by creating another card or wallet token | Sections 3.1, 4/MLO-3, 7.3; Tasks 2 and 8 |
| SCA and action binding | Reduces replay and unauthorized security-reducing actions | Section 5.1; Tasks 5, 7, and 8 |
| Idempotency and optimistic concurrency | Makes retries and concurrent controls deterministic | Section 6.3; Tasks 3, 5, 7, and 8 |
| Transactional outbox and durable audit | Prevents acknowledged mutations without required evidence/events | Sections 5.2 and 6.1; Tasks 3 and 12 |
| Data minimization and PCI boundary | Keeps prohibited cardholder data outside broad application scope | Sections 5.1 and 6.10; Tasks 4 and 15 |
| Purpose- and entity-based retention | Avoids unjustified group-wide over-retention | Section 5.1.2; Task 16 |
| Legal hold and controlled deletion | Preserves mandatory evidence while enforcing accountable disposal | Section 5.1.2; Task 16 |
| Regulated data-plane isolation | Prevents cross-entity, cross-region, support, and backup leakage | Section 6.9; Task 16 |
| Controlled international transfers | Applies SCC/TIA and supplementary controls to remote access paths | Section 6.9.4; Task 16 |
| Evidence-based processor qualification | Makes roadmap gaps and non-binding claims launch blockers | Section 6.10; Tasks 4 and 15 |
| Webhook authentication and deduplication | Handles replay, event-ID reuse, and out-of-order delivery | Sections 6.3 and 8; Task 9 |
| Stable snapshot pagination | Prevents duplicates or omissions during concurrent inserts | Sections 7.4 and 8; Task 10 |
| Authoritative-system separation | Keeps projections from being mistaken for the booked-money ledger | Sections 6.5 and 6.8; Task 13 |
| Reconciliation and fail-closed repair | Surfaces or safely repairs drift without weakening controls | Sections 5.3, 6.8, and 8; Task 13 |
| Internal/customer reason separation | Prevents disclosure of fraud, AML, sanctions, and legal logic | Section 6.7; Tasks 11 and 12 |
| Least privilege and dual approval | Controls privileged holds, exports, repair, and incident actions | Sections 5.1 and 6.11.2; Tasks 11–12 |
| Named incident ownership | Separates technical, financial, audit, and communication completion | Sections 6.11–6.11.2; Task 14 |
| Measurable SLOs and capacity | Makes reliability and performance testable | Sections 5.3–5.4; Tasks 14–15 |
| Backward-compatible schemas and safe unknowns | Prevents new provider values from crashing or weakening old consumers | Section 6.6; Tasks 4 and 9 |
| Layered verification and release gates | Requires evidence for objectives and blocks incomplete releases | Section 9; Task 15 |

## Key design boundaries

- The processor-hosted credential component may display card credentials, but
  the application backend must not receive full PAN or CVV.
- The card service does not adjust the authoritative ledger.
- Transaction history is informational unless a separate ledger contract makes
  it authoritative.
- Customer-facing reason messages do not expose internal fraud, AML, sanctions,
  legal, or processor decision logic.
- AWS is the initial approved infrastructure provider; other service providers
  remain unapproved until their precise legal entities, regions, support paths,
  subprocessors, audit rights, and exit obligations pass the required review.
- Poland, Romania, and Moldova require market-specific limits, notices,
  complaint contacts, regulatory evidence, and final launch approval.

## Submission checklist

- [x] One crisp high-level objective and scope boundary
- [x] Six observable mid-level objectives
- [x] Security, privacy, audit, reliability, and measurable performance targets
- [x] Implementation and data-handling guardrails
- [x] Explicit beginning and ending context
- [x] Sixteen dependency-ordered low-level tasks with definitions of done
- [x] Feature-specific edge cases and failure behavior
- [x] Verification matrix, fixtures, test categories, and release gates
- [x] MLO-to-task traceability table
- [x] Agent rules with stack assumptions and regulated-domain constraints
- [x] Editor/AI instructions
- [x] README rationale and industry-practice mapping
- [x] No implementation code
