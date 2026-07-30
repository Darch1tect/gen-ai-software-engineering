# Copilot Instructions — Virtual Card Specification

This repository task is documentation-only. Work inside `homework-3/` and do
not generate implementation unless the user explicitly changes the scope.

## Source of truth

- Read `../specification.md` before making a substantive change.
- Use `../agents.md` for the complete agent contract.
- Preserve traceability from the high-level objective through MLOs, acceptance
  criteria, edge cases, verification, low-level tasks, and the traceability
  table.
- Treat section 13 decisions as fixed direction and its remaining items as
  release blockers.
- Treat regulatory links as baselines. Never claim that a law is current or
  applicable without the dated verification required by section 0.3.1.

## FinTech-safe defaults

- Fail closed on unknown, contradictory, unauthorized, or cross-entity state.
- Never log or expose PAN, CVV, PIN, magnetic-stripe data, tokens, secrets, raw
  processor payloads, SCA payloads, AML/sanctions details, STR/SAR activity, or
  law-enforcement requests.
- Use integer minor units plus ISO currency; never use floating-point money.
- Keep customer freeze and risk hold independent; the more restrictive control
  wins.
- Require idempotency, optimistic versioning, durable audit, and reconciliation
  for sensitive writes.
- Treat the regulated ledger as authoritative for booked money and the
  processor as authoritative for processor/network records.
- Bind all resources and access to a regulated entity. Deny cross-plane access
  by default.
- Separate internal reason codes from localized customer message codes.
- Never present an assumed SLO, limit, retention period, vendor, or location as
  approved production policy.

## Writing rules

- Use normative language deliberately: `must` for requirements, `should` for
  recommendations, and `may` for explicitly permitted options.
- Prefer measurable outcomes and checkable definitions of done.
- For each important failure, describe customer behavior plus audit, security,
  or recovery implications.
- Keep terminology aligned with section 3. Do not introduce processor-specific
  enums into domain language.
- Use links to exact specification sections instead of copying large policy
  blocks.
- Keep customer messages safe, actionable, localized, and free of confidential
  decision logic.
- Mark new assumptions and configuration candidates with the required approval
  owners.

## If implementation is later requested

- Keep domain, API, persistence, provider, audit, reconciliation, and privacy
  boundaries separate.
- Use ports for external systems and allowlisted models at trust boundaries.
- Add positive, negative, concurrency, failure-injection, and privacy tests.
- Do not acknowledge a mutation before the state and its required durable audit
  or outbox guarantee are committed.
- Do not auto-repair ambiguity by making a card less restrictive.
