# Security Checklist: Virtual Card Lifecycle Management

**Purpose**: Formal pre-implementation gate validating that security & data-protection
requirements in `spec.md` (PAN/CVV handling, vault boundary, least-privilege/permission
scoping, authentication/authorization boundaries, rate limiting, fail-closed dependency
handling) are complete, clear, consistent, measurable, and traceable — for sign-off by a
security reviewer before this specification is treated as implementation-ready.
**Created**: 2026-07-29
**Feature**: [spec.md](../spec.md)

**Note**: This checklist tests the *requirements themselves* — whether they are well-written,
complete, and unambiguous. It does not test or verify any implementation (none exists yet in
this documentation-only phase).

## Requirement Completeness

- [ ] CHK001 Are requirements defined for how the `vault_reference` token itself is protected in
      transit and at rest (as opposed to only the full PAN it references)? [Gap, data-model.md
      Virtual Card]
- [x] CHK002 Are authentication requirements (how an end-user or internal staff member proves
      their identity before any card action) documented anywhere, or does the spec only address
      authorization (Permission Scope) once identity is already assumed? [Gap]
      — Resolved via `/speckit-clarify` 2026-07-29 (round 3): baseline authentication is an
      explicit out-of-scope boundary (FR-035); high-risk actions require step-up
      re-authentication (FR-036, SC-013).
- [ ] CHK003 Are requirements defined for session/credential re-verification on high-risk actions
      (freeze, limit change, fraud flag) distinct from routine reads? [Gap]
- [ ] CHK004 Are requirements defined for behavior when rate-limit-counter or idempotency-record
      storage itself is unavailable, distinct from FR-032's external-dependency (KYC/vault/
      processor) case? [Gap]
- [ ] CHK005 Is a threat model or an explicit list of assumed adversaries (compromised internal
      credential, replay, enumeration) documented, with security requirements traceable back to
      it? [Gap, Traceability]

## Requirement Clarity

- [ ] CHK006 Is "least privilege" (constitution.md Principle I) translated into a specific,
      checkable rule per role, or left as a general principle without per-role enumeration?
      [Clarity, constitution.md Principle I]
- [ ] CHK007 Is the encryption standard for data in transit/at rest specified with a concrete
      minimum (e.g., TLS version, cipher strength), or left as unquantified "strong encryption"?
      [Clarity, Spec §Security & Privacy]
- [ ] CHK008 Is "opaque, non-guessable" (card ID, transaction ID) quantified with a minimum
      entropy or format requirement, or left to implementer judgment? [Clarity, data-model.md]
- [ ] CHK009 Is the per-action-type rate limit's actual numeric threshold specified anywhere, or
      only the qualitative rule that limits must be independent per action type? [Clarity, Spec
      §Reliability & Concurrency, FR-031]
- [ ] CHK010 Is "fail closed" (FR-032) defined precisely enough to rule out a fallback to a
      cached or default credential/response, or could it be satisfied by such a fallback under a
      literal reading? [Clarity, FR-032]

## Requirement Consistency

- [ ] CHK011 Are the `INSUFFICIENT_PERMISSION`, `RATE_LIMIT_EXCEEDED`, and
      `DEPENDENCY_UNAVAILABLE` error codes documented consistently across all three contract
      files, with none omitting a code the others define? [Consistency, contracts/*.md]
- [ ] CHK012 Do end-user-facing operations (card-lifecycle.contract.md) and internal ops-facing
      operations (ops-compliance.contract.md) apply the same idempotency/correlation-ID/
      rate-limit/fail-closed conventions, with no operation silently exempted? [Consistency]
- [ ] CHK013 Is the distinction between "denied and audited" (permission failures) versus
      "denied and only logged, not audited" (rate-limit/dependency failures) applied
      consistently everywhere it should hold? [Consistency, Spec §Audit & Logging]

## Acceptance Criteria Quality

- [ ] CHK014 Can "no field capable of holding full PAN/CVV" (a stated model-level acceptance
      criterion) be objectively verified without implementation access, or does it rely on
      trusting a future implementer's self-report? [Measurability]
- [ ] CHK015 Is there a measurable acceptance criterion confirming that the capability check and
      the scope-boundary check are evaluated *independently* (neither masking the other), rather
      than just asserting both exist? [Acceptance Criteria Quality, Gap]
- [ ] CHK016 Is SC-007's "0% of views ever display unmasked PAN/CVV" paired with a defined
      verification method (automated scan vs. manual review), or does it state the target with
      no means to check it? [Measurability, Spec §SC-007]

## Scenario Coverage

- [ ] CHK017 Are requirements defined for a stolen idempotency key being replayed by an attacker,
      as distinct from a legitimate client's own retry? [Gap, Coverage]
- [ ] CHK018 Are requirements defined for detecting or limiting a brute-force-style enumeration
      attempt against card IDs or transaction IDs? [Gap, Coverage]
- [ ] CHK019 Are requirements defined for an internal staff credential being used from an
      unexpected context (concurrent sessions, anomalous access pattern), or is this left
      unaddressed without stating so? [Gap, Coverage]
- [ ] CHK020 Are requirements defined for verifying a Permission Scope grant is still valid at
      the moment of use, rather than relying on a cached earlier check? [Gap, Coverage]

## Edge Case Coverage

- [ ] CHK021 Is there a documented edge case addressing whether a rate-limit-exceeded response
      could be used as a timing/enumeration side-channel (e.g., distinguishing "customer doesn't
      exist" from "rate limited")? [Gap, Edge Case]
- [x] CHK022 Is there a documented edge case for the external vault/tokenization provider
      returning a valid-looking but *incorrect* response (data-integrity failure), as opposed to
      only an unavailable/timeout failure — does FR-032's fail-closed guarantee cover this case?
      [Gap, Edge Case, FR-032]
      — Resolved via `/speckit-clarify` 2026-07-29 (round 3): fail-closed now explicitly covers
      integrity failures too (FR-034, edge case E17), uniformly across all three dependencies.
- [ ] CHK023 Is there a documented edge case for a freeze or fraud-flag action performed using a
      credential that is revoked or expires mid-request (a race between revocation and action)?
      [Gap, Edge Case]

## Non-Functional Requirements (Security)

- [ ] CHK024 Is a maximum retention period defined for idempotency-key/rate-limit-counter data,
      balancing replay-window security against unbounded storage growth? [Gap, data-model.md
      Idempotency Record]
- [ ] CHK025 Is a requirement defined for how frequently Permission Scope grants must be
      reviewed or recertified, given the spec otherwise models them as a point-in-time grant
      with no expiry cycle? [Gap]
- [ ] CHK026 Is access control for the structured observability log (which contains actor
      identities and correlation IDs, per FR-029/030) specified as rigorously as access control
      for the audit trail, or left unaddressed by comparison? [Gap, Consistency]
- [ ] CHK027 Is a measurable target defined for how quickly a pattern of repeated
      security-relevant denials becomes visible to a human reviewer, or does the spec stop at
      "the denial is logged"? [Gap, Measurability]

## Dependencies & Assumptions

- [ ] CHK028 Is the assumption that the external KYC/onboarding system's eligibility decision
      cannot itself be spoofed or replayed explicitly stated, or silently trusted? [Assumption,
      Spec §Assumptions]
- [ ] CHK029 Is it explicitly documented that this feature depends on, but does not control,
      the vault/tokenization provider's guarantee that a `vault_reference` token cannot be
      exchanged for the real PAN by an unauthorized caller? [Assumption, Gap]
- [ ] CHK030 Is the payment processor's own authorization-security posture (e.g., its fraud
      scoring) assumed sufficient on its own, or does this spec require additional checks beyond
      frozen/limit status — and is that assumption stated either way? [Assumption, Spec
      §Assumptions]

## Ambiguities & Conflicts

- [ ] CHK031 Does "fail closed" (FR-032) address the boundary case of a dependency that is slow
      but has not yet timed out — could a slow-but-eventually-successful dependency call cause a
      latency-budget breach (SC-001–SC-003) that the spec doesn't reconcile with the fail-closed
      rule? [Conflict, Ambiguity, FR-032, SC-001-003]
- [x] CHK032 Is the residual risk of a coordinated multi-action-type attack (spreading requests
      across create/freeze/limit-update to stay under each individual per-action-type rate
      limit) explicitly acknowledged as accepted, or left unaddressed by the "independent
      per-action-type" framing in FR-031? [Ambiguity, Gap, FR-031]
      — Resolved via `/speckit-clarify` 2026-07-29 (round 3): an aggregate cross-action-type
      rate limit was added (FR-032, edge case E18), closing the gap rather than just documenting
      it as accepted risk.

## Traceability

- [ ] CHK033 Is a security-requirement tagging scheme established (e.g., marking FR-026, FR-031,
      FR-032, and related items as a distinct "security-critical" subset) so a security reviewer
      can filter to just those without re-reading the entire FR list? [Traceability, Gap]
- [ ] CHK034 Do plan.md's Constitution Check citations for Principle I (Sensitive Data
      Protection) and Principle III (Reliability, covering rate-limiting/fail-closed)
      reference the complete, current set of security-relevant requirements? [Traceability,
      plan.md]

## Notes

- Focus area: Security & data protection (PAN/CVV handling, vault boundary, least-privilege/
  permission scoping, authN/authZ boundaries, rate limiting, fail-closed dependency handling) —
  as explicitly requested.
- Depth: Formal pre-implementation gate (34 items), consistent with `compliance.md`'s depth.
- Audience/timing: Security reviewer, evaluated before this spec package is treated as
  implementation-ready.
- This checklist intentionally minimizes overlap with `compliance.md`: that checklist covers
  audit/retention/regulatory-process quality; this one covers technical security-control
  requirements quality (identity, encryption, rate limiting, dependency trust boundaries).
- Check items off as reviewed: `[x]`. Add findings inline under the relevant item if a gap is
  confirmed and needs a follow-up spec amendment.
