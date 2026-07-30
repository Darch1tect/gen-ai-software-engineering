# Compliance & Audit Checklist: Virtual Card Lifecycle Management

**Purpose**: Formal pre-implementation gate validating that compliance/audit-trail requirements
in `spec.md` (and their reflection in `plan.md`/`data-model.md`) are complete, clear,
consistent, measurable, and traceable — for sign-off by an internal compliance/ops reviewer
before this specification is treated as implementation-ready.
**Created**: 2026-07-29
**Feature**: [spec.md](../spec.md)

**Note**: This checklist tests the *requirements themselves* — whether they are well-written,
complete, and unambiguous. It does not test or verify any implementation (none exists yet in
this documentation-only phase).

## Requirement Completeness

- [ ] CHK001 Are retention/deletion-prohibition requirements documented for every entity that
      touches audit data, not only the Audit Record itself? [Completeness, Spec §Key Entities]
- [ ] CHK002 Are requirements defined for how long masked (non-audit) card/transaction data
      itself must be retained, separate from the audit trail's indefinite retention (SC-012)?
      [Gap]
- [ ] CHK003 Are requirements defined for what a compliance reviewer must be able to export or
      extract from the audit trail (e.g., a case file for a regulator), or is "view" the only
      documented capability? [Gap, Spec §FR-021]
- [ ] CHK004 Is there a requirement for how an internal user's Permission Scope grant or
      revocation is itself audited (who granted/revoked access to whom, and when)? [Gap]
- [ ] CHK005 Are retention requirements defined for Idempotency Records and rate-limit counters
      for compliance replay/investigation purposes, or is their exclusion from the audit trail
      explicitly stated as intentional? [Gap, data-model.md]

## Requirement Clarity

- [ ] CHK006 Is "chronologically-ordered audit trail" (FR-021) accompanied by a tie-breaking
      rule for entries that share the same timestamp? [Clarity, Spec §FR-021]
- [ ] CHK007 Is "≥99.9% read-availability" (SC-012) quantified with a measurement window (e.g.,
      rolling 30-day) rather than left as a bare percentage with no observation period? [Clarity,
      Spec §SC-012]
- [ ] CHK008 Is the Audit Record's `reason/source` field constrained to an enumerated,
      compliance-reviewable set of values, or left as unconstrained free text that would be
      harder to report on consistently? [Clarity, data-model.md]
- [ ] CHK009 Is "scoped to a specific customer segment or case" (Permission Scope) defined
      precisely enough that a reviewer could determine, from the requirement text alone, whether
      a given grant is over-broad? [Clarity, Spec §Key Entities]
- [ ] CHK010 Is the distinction between the compliance audit trail (FR-027) and the structured
      observability log (FR-029) stated clearly enough that a reviewer would not conflate the
      two as a single evidentiary source? [Clarity, Spec §Observability, §Data Protection & Audit]

## Requirement Consistency

- [ ] CHK011 Are the Audit Record fields listed in spec.md's Key Entities section consistent
      with the field list in data-model.md's Audit Record table? [Consistency, Spec §Key
      Entities, data-model.md]
- [ ] CHK012 Is the "no update/delete capability" requirement (FR-028) stated consistently
      across spec.md, data-model.md, and contracts/ops-compliance.contract.md, with none of the
      three implying a restricted-but-present update path? [Consistency]
- [ ] CHK013 Do FR-020 (denied access is audited) and FR-024 (denied fraud-flag is audited) use
      a consistent audit action-type naming convention, so a reviewer would not mistake them for
      unrelated event classes? [Consistency, Spec §FR-020, FR-024]

## Acceptance Criteria Quality

- [ ] CHK014 Is SC-006's "zero unexplained gaps" reconciliation check specified with a defined
      review frequency (continuous, daily, per-release) a compliance reviewer could schedule
      against? [Acceptance Criteria Quality, Spec §SC-006]
- [ ] CHK015 Can "complete (no gaps)" (User Story 5, acceptance scenario 3) be objectively
      verified without implementation access — does the spec define what evidence would
      demonstrate completeness to an external auditor? [Measurability, Spec §User Story 5]
- [ ] CHK016 Is SC-012's ≥99.9% read-availability target paired with a defined consequence or
      escalation path if breached, or does the requirement stop at stating the number? [Acceptance
      Criteria Quality, Spec §SC-012]

## Scenario Coverage

- [ ] CHK017 Are requirements defined for how a compliance reviewer would respond to a
      regulator's ad-hoc audit-trail data request, or is this scenario entirely assumed
      out of scope without saying so? [Gap, Coverage]
- [ ] CHK018 Are periodic/scheduled compliance review requirements (e.g., recurring access-scope
      recertification) documented anywhere, or does the spec only address event-driven, per-request
      compliance checks? [Coverage, Gap]
- [ ] CHK019 Is a scenario defined for an ops/compliance user's Permission Scope being revoked
      mid-session — what happens to a request already in flight when the revocation commits?
      [Coverage, Edge Case, Gap]
- [ ] CHK020 Are data-residency or cross-border storage requirements for audit records addressed,
      given the neobank framing implies a regulated, potentially multi-jurisdiction context? [Gap,
      Coverage]

## Edge Case Coverage

- [ ] CHK021 Is there a documented requirement for a compliance reviewer querying a card whose
      audit trail has grown very large (thousands of entries across years), addressing
      pagination or performance for compliance-facing queries specifically (separate from the
      end-user-facing pagination in FR-018)? [Gap, Edge Case]
- [ ] CHK022 Is there a requirement for what happens if the append-only audit store itself is
      unavailable mid-write to the operational store — distinct from edge case E16, which covers
      only external KYC/vault/processor dependencies? [Gap, Edge Case]
- [ ] CHK023 Are requirements defined for an audit record whose actor (an internal staff member)
      is later deactivated — does the spec state the historical record remains attributable to
      that actor regardless? [Gap, Edge Case]

## Non-Functional Requirements

- [ ] CHK024 Are the three reference frameworks named in the Regulatory Scope section (PCI DSS,
      SOC 2, GDPR-style rights) each tied to at least one concrete, testable requirement in the
      Functional Requirements section, or do they remain a general acknowledgment without
      traceable linkage? [Traceability, constitution.md, Spec §Regulatory Scope]
- [ ] CHK025 Is a requirement defined for periodically reconciling the Tier-1/Tier-2/Tier-3 data
      classification against the actual fields modeled in data-model.md, to catch future drift?
      [Gap]
- [ ] CHK026 Are non-functional requirements defined for compliance-reviewer-facing query
      performance (e.g., full customer audit-trail lookup latency), separate from the
      end-user-facing latency budgets in SC-001–SC-005? [Gap, Coverage]

## Dependencies & Assumptions

- [ ] CHK027 Is the assumption that KYC eligibility is determined by an out-of-scope onboarding
      system accompanied by a documented interface/data contract sufficient for a compliance
      reviewer to investigate a dispute spanning both systems? [Assumption, Spec §Assumptions]
- [x] CHK028 Is the out-of-scope status of the full dispute-case lifecycle (FR-025) accompanied
      by a requirement that the Audit Record retain enough information (e.g., a case reference)
      to be joined with the external dispute system's records? [Gap, Assumption, Spec §FR-025]
      — Resolved via `/speckit-clarify` 2026-07-29 (round 2): Audit Record now has an optional
      `external_case_reference` field (spec.md § Key Entities, data-model.md).
- [ ] CHK029 Is the assumption that customer notifications are out of scope (push/SMS on freeze
      or fraud flag) reconciled with any compliance expectation to notify customers of actions
      taken against their account, or is this tension explicitly flagged rather than silently
      assumed away? [Assumption, Spec §Assumptions]

## Ambiguities & Conflicts

- [x] CHK030 Does "retained indefinitely, no defined deletion" (SC-012) create an unaddressed
      tension with the GDPR-style data-subject rights acknowledged in the Regulatory Scope
      section, and if so, is that tension explicitly flagged as an open question rather than
      left to silent interpretation? [Conflict, Spec §SC-012, §Regulatory Scope]
      — Resolved via `/speckit-clarify` 2026-07-29 (round 2): audit records are now explicitly
      stated as exempt from erasure/correction requests (spec.md § SC-012).
- [ ] CHK031 Is "read-availability" in SC-012 unambiguous about whether it covers only
      successful reads or also reads that time out and are retried, which would change how the
      99.9% figure is measured? [Ambiguity, Spec §SC-012]

## Traceability

- [ ] CHK032 Is a requirement & acceptance-criteria ID scheme established and applied
      consistently across the FR-###, SC-###, and E## items relevant to compliance/audit,
      allowing a reviewer to cite one stable identifier per finding? [Traceability]
- [ ] CHK033 Do plan.md's Constitution Check citations for Principle II (Auditability)
      reference the current, complete set of compliance-relevant requirements (FR-027, FR-028,
      SC-006, SC-012), or could a reviewer be misled by a stale subset? [Traceability, plan.md]

## Notes

- Focus area: Compliance & audit (of the 4 candidates offered, this was selected over security,
  reliability, and a combined review).
- Depth: Formal pre-implementation gate (33 items) — sized for compliance/ops sign-off, not a
  quick sanity pass.
- Audience/timing: Internal compliance/ops reviewer, evaluated before this spec package is
  treated as implementation-ready.
- Check items off as reviewed: `[x]`. Add findings inline under the relevant item if a gap is
  confirmed and needs a follow-up spec amendment.
- This checklist evaluates requirements *quality*, not implementation — there is no running
  system to test against in this documentation-only phase.
