# Virtual Card Lifecycle Management Specification

> Ingest this specification, implement the Low-Level Tasks in dependency order, and produce a system that satisfies the High-Level Objective, Mid-Level Objectives, policy requirements, and acceptance criteria. Where this document labels a value as an assumption, do not silently turn it into a permanent policy: expose it as configuration and obtain product, security, and compliance approval before production release.

## 0. Document Control

| Field | Value |
|---|---|
| Status | Draft for product, architecture, security, and compliance review |
| Feature | Virtual card lifecycle management |
| Intended readers | Product, engineering, QA, security, compliance, operations, and AI coding agents |
| Delivery model | Documentation-only homework; implementation paths below describe the hypothetical target system |
| Primary actors | Cardholder, operations analyst, compliance analyst |
| External dependency | PCI-compliant card processor/tokenization provider |
| Ukrainian regulated provider | Licensed sponsor bank; legal name is a launch gate |
| Authoritative ledger owner | Issuing sponsor/regulated entity; Ukrainian sponsor bank for the first release |
| Initial market | Ukraine |
| Expansion markets | Poland as the EEA home state; Romania through passporting; Moldova through a separate local entity or licensed sponsor |
| Product risk profile | Retail neobanking, low-to-medium risk |
| Initial cloud baseline | AWS Europe (Frankfurt), `eu-central-1`; encrypted warm standby in AWS Europe (Ireland), `eu-west-1` |

### 0.1 Controlled Baselines and Remaining Assumptions

1. The first production launch uses a licensed Ukrainian sponsor bank. The sponsor bank is the customer’s regulated account provider, card issuer, funds holder, authoritative-ledger owner, and final KYC/AML decision-maker. The platform company is an outsourced technology and card-control provider and must not present itself as a deposit-taking or card-issuing entity.
2. Each card has one base currency and does not allow the user to change it after issuance.
3. The application never receives or stores CVV, PIN, magnetic-stripe data, or full PAN. Sensitive card data is rendered only by a processor-hosted component.
4. A verified low-to-medium-risk customer may hold at most five active or frozen virtual cards. Purchase limits are customer-level across all cards and wallet tokens and follow the Ukraine segment table in section 4; non-Ukrainian values are release-blocking local-market configuration.
5. Retention is controlled by data category and issuing legal entity. The longest period in one jurisdiction or category must never become the group-wide default. Section 5.1.2 defines the approved control model and jurisdictional AML/KYC baselines.
6. Customer-facing transaction history is available for at least 24 months. Older records remain available to authorized operations users according to the approved retention schedule.
7. The processor is authoritative for processor-side card status, network authorizations, and clearing records. For Ukraine, the sponsor bank owns the authoritative double-entry ledger and booked monetary values. The card database is a rebuildable projection and workflow store.
8. Strong customer authentication follows the action matrix in section 5.1. Assertions are short-lived and action-bound; payment and credential-display challenges are single-use.
9. First-year and 24-month traffic, processor quotas, and upstream SLOs are planning and procurement assumptions defined in sections 5.3 and 5.4. They must be recalculated after processor selection and production telemetry.
10. All monetary limits, retention periods, SCA policies, disclosure mappings, data locations, and processor quotas are versioned configuration with named business, Risk, Security, Privacy, and Compliance owners. The Frankfurt/Ireland hosting baseline is fixed for the first release unless the regulated change process approves a replacement.

### 0.2 Jurisdiction and Market-Entry Baseline

#### Ukraine launch

- The Ukrainian launch uses a licensed Ukrainian sponsor bank. The sponsor bank is the customer’s regulated account provider, card issuer/BIN sponsor, funds holder, owner of the authoritative ledger, and final KYC/AML and regulatory decision-maker.
- The platform company provides the customer application, card-control domain, processor integration, customer-safe projections, and operational tooling under a regulated outsourcing agreement. The agreement must allocate control ownership, audit access, incident duties, data processing, business continuity, exit assistance, and the sponsor bank’s approval and oversight rights.
- Customer terms, UI, statements, notifications, complaint routes, and marketing must identify the sponsor bank’s regulated role and must not represent the platform as accepting deposits, holding customer funds, or issuing cards.
- The launch baseline is the current [Law of Ukraine “On Payment Services” No. 1591-IX](https://zakon.rada.gov.ua/go/1591-20), applicable NBU regulations including the current authentication/SCA rules, the [Law of Ukraine “On Personal Data Protection” No. 2297-VI](https://zakon.rada.gov.ua/go/2297-17), Ukrainian AML/CFT law, consumer-protection rules, card-scheme rules, and the current PCI DSS version applicable to the card-data environment.
- The sponsor bank retains end-to-end regulatory accountability and approval authority for outsourced important payment functions. The platform’s controls supplement but do not replace the sponsor bank’s statutory controls.

#### EEA expansion

- The target independent EEA model is a Polish electronic-money institution because the intended product permits customers to fund and retain a reusable balance for card and transfer transactions. Initial authorization excludes deposit-taking, investment services, and general consumer credit. E-money must not be marketed as an insured bank deposit.
- If final legal analysis concludes that the product creates no e-money liability and all customer balances remain with a partner bank, the scope may be reduced to payment-institution or agent status through a documented regulatory-perimeter change approved under section 0.3.1.
- Poland is the assumed home Member State, conditional on genuine Polish management, Compliance, Risk, Finance, and operational substance. The authorization programme and operational validation launch first in Poland.
- Romania is entered through the applicable PSD2/EMD2 freedom-to-provide-services passport. A Romanian branch is added only when local establishment becomes operationally or regulatorily necessary. Romanian service must not start before completion of the home/host notification procedure, confirmation of the commencement date, and required register updates.
- Passporting does not displace Romanian AML/CFT, consumer-protection, complaints, language, tax, card-scheme, regulatory-reporting, or other host-state obligations.
- The EEA baseline includes PSD2 and its SCA/secure-communication RTS while in force, successor payment legislation when applicable, GDPR, DORA, the applicable AML/CFT framework, EBA guidance, local transposition, and national competent-authority requirements. The design must track regulatory change without hard-coding a directive version.
- EU customer funds are held in segregated safeguarding accounts at no fewer than two EEA credit institutions. Safeguarded funds are separated from operating funds, protected against set-off, reconciled daily to the authoritative e-money ledger, and independently reviewed. Insurance is not the primary safeguarding method.
- The Polish EMI submits the passport notification to KNF only after authorization and operational validation in Poland. EU customers must not be served under the Ukrainian sponsor arrangement merely because the software is technically available in the EEA.

#### Moldova

- Moldova uses a separate local sponsor or licensed entity and a separate regulated data plane. It is not covered by EEA passporting.
- Moldovan customer funds, ledger, processor programme, audit records, encryption keys, and regulatory reporting remain isolated from the Ukrainian sponsor-bank and Polish EMI arrangements.
- The National Bank of Moldova, local AML/CFT, payment-services, consumer, privacy, outsourcing, and data-location requirements must be mapped before onboarding any Moldovan customer.

### 0.3 Normative Reference Baseline

The implementation team must maintain a dated regulatory register. References are research baselines only and are not evidence that a requirement remains current, complete, effective, or applicable. At drafting time, the primary baselines include:

- [Ukraine: Law “On Payment Services” No. 1591-IX](https://zakon.rada.gov.ua/go/1591-20);
- [Ukraine: Law “On Personal Data Protection” No. 2297-VI](https://zakon.rada.gov.ua/go/2297-17);
- [Ukraine: NBU Resolution No. 58 on authentication and strong authentication, as amended](https://bank.gov.ua/admin_uploads/law/03052023_58.pdf);
- [Ukraine: AML/CFT Law No. 361-IX](https://zakon.rada.gov.ua/laws/show/361-20#Text);
- [EU: GDPR, Regulation (EU) 2016/679](https://eur-lex.europa.eu/eli/reg/2016/679/oj);
- [EU: PSD2, Directive (EU) 2015/2366](https://eur-lex.europa.eu/eli/dir/2015/2366/oj);
- [EU: Electronic Money Directive, Directive 2009/110/EC](https://eur-lex.europa.eu/eli/dir/2009/110/oj);
- [EU: SCA and secure-communication RTS, Delegated Regulation (EU) 2018/389](https://eur-lex.europa.eu/eli/reg_del/2018/389);
- [EU: DORA, Regulation (EU) 2022/2554](https://eur-lex.europa.eu/eli/reg/2022/2554/oj);
- [EU: Standard Contractual Clauses, Decision (EU) 2021/914](https://eur-lex.europa.eu/legal-content/en/ALL/?uri=CELEX%3A32021D0914);
- [Poland: AML Act, Article 49](https://eli.gov.pl/api/acts/DU/2018/723/text.html);
- [Romania: Law No. 129/2019, Article 21](https://legislatie.just.ro/public/DetaliiDocument/216157);
- [Moldova: applicable AML legislation](https://www.legis.md/cautare/downloadpdf/136906);
- current EBA authorization, passporting, ICT/security, outsourcing, and payment guidance;
- [PCI DSS v4.0.1](https://www.pcisecuritystandards.org/document_library/?class=pcidss&doc=pci_dss), card-scheme, sponsor-bank, processor, and tokenization requirements; successor PCI DSS versions enter the regulatory register through controlled change.

Where two rules differ, the relevant regulated entity applies the legally applicable result documented by local counsel; the system must not combine periods or controls into an unjustified group-wide maximum.

#### 0.3.1 Country-Launch Regulatory Verification

Before every country launch, Legal and Compliance must verify each reference against current consolidated law, amendments, successor legislation, regulator rules, binding guidance, and measures published but not yet effective.

| Review | Required timing |
|---|---|
| Initial applicability and gap review | At least 90 days before launch |
| Final Legal/Compliance certification | No earlier than 10 business days before production launch |
| Final change scan | Within 48 hours before go-live |
| Certification expiry | Repeat certification when launch is delayed by more than 10 business days |

A material regulatory change after approval blocks launch until reassessed. Each review creates an immutable record named `REG-LAUNCH-{MARKET}-{YYYY-MM-DD}` containing:

- market, issuing legal entity, sponsor/licensing model, and planned launch date;
- instrument name, official citation, consolidated version, effective date, official source URL, and access date;
- amendments and successor instruments checked;
- applicability conclusion and rationale;
- mapped product requirements, technical/operational controls, control owner, and evidence location;
- open gaps, remediation deadline, and launch-blocking status;
- local-counsel opinion where interpretation is required;
- reviewer names, roles, approval timestamps, and regulatory-register version/hash.

Required sign-off:

| Market | Required approvers |
|---|---|
| Ukraine | Ukrainian regulatory counsel; Compliance Officer/MLRO; DPO/privacy owner; sponsor-bank compliance representative |
| Poland | Polish regulatory counsel; EEA Compliance Officer/MLRO; DPO; licensing/passporting owner |
| Romania | Romanian local counsel; EEA Compliance Officer; DPO; Polish home-state regulatory owner |
| Moldova | Moldovan regulatory counsel; Compliance Officer/MLRO; privacy owner; local sponsor/licensing owner |

The review covers licensing and sponsorship; passporting; safeguarding and authoritative-ledger duties; payment and e-money rules; AML/KYC, sanctions, and monitoring; disclosures, complaints, ADR, and response periods; SCA, fraud, and incident reporting; privacy, localization, transfers, and retention; outsourcing, cloud, subprocessors, audit, and exit rights; scheme/PCI/processor requirements; FX and product limits; tax, accounting, recordkeeping, and regulatory reporting.

Official legislation and regulator publications are primary: the Verkhovna Rada and NBU; EUR-Lex and EU authorities; official Polish, Romanian, and Moldovan legislative databases and competent regulators. Vendor summaries, law-firm articles, and earlier opinions may support analysis but cannot be the sole authority.

Launch is prohibited when an applicable entry is `TBD` or `UNVERIFIED`, cites only superseded law, lacks an official source/effective date, leaves licensing/safeguarding/privacy-transfer/outsourcing approval unresolved, contains an unremediated high-impact gap, conflicts with customer terms/notices, or lacks an unexpired certification and 48-hour scan.

After launch, Regulatory Compliance monitors change continuously, performs a documented quarterly register review, and obtains full Legal/Compliance recertification at least annually. Emergency rules, sanctions, FX restrictions, and regulator directions are assessed within one business day of publication.

## 1. High-Level Objective

- Enable an authenticated customer to safely create and control a tokenized virtual payment card, set enforceable spending limits, and review card transactions, while giving authorized operations and compliance staff a complete, immutable, privacy-conscious record of all sensitive actions.

**Scope boundary:** This release specifies the virtual card after the customer has passed onboarding and KYC; physical cards, KYC onboarding, money movement, chargebacks, rewards, card replacement, PIN management, wallet provisioning, credential-display UI, and customer-initiated closure are not implemented by these Low-Level Tasks. The SCA, privacy, audit, and regulated-entity rules in this specification still govern those shared-platform actions if another component exposes them.

## 2. Stakeholders and User Outcomes

| Stakeholder | Required outcome |
|---|---|
| Cardholder | Create a virtual card, understand its status, freeze or unfreeze it, set limits, and review transactions without exposing sensitive credentials |
| Operations analyst | Inspect card state and action history, perform permitted emergency freezes, and diagnose processor synchronization failures |
| Compliance analyst | Search and export evidence of who performed a sensitive action, when it happened, why it was allowed, and what changed |
| Fraud/risk service | Apply a risk hold that the customer cannot bypass and receive consistent card-control events |
| Customer support | View masked, minimum-necessary card and transaction data without gaining card-control or audit-export permissions |
| Security and privacy | Keep sensitive authentication and card data out of application storage, logs, analytics, and support tooling |

## 3. Domain Terms and State Model

### 3.1 Definitions

| Term | Meaning |
|---|---|
| Card token | Opaque processor-issued identifier; it is not a PAN and must still be handled as confidential |
| Card projection | Local read model representing the last processor state known to this application |
| Available limit | Customer-level configured limit minus qualifying posted and pending spend across all cards and wallet tokens in the limit window |
| Risk segment | Versioned customer classification (`NEW`, `STANDARD`, `ESTABLISHED`, or `ENHANCED`) that sets the maximum configurable purchase limits |
| Risk hold | Restriction imposed by fraud, compliance, or operations that cannot be removed by the customer |
| Idempotency key | Client-generated opaque key that makes retries of a write return the original logical result |
| Correlation ID | Identifier propagated across API, processor call, event, notification, and audit record |

### 3.2 Card States

| State | Meaning | Customer can spend | Customer can transition |
|---|---|---:|---|
| `PENDING_ACTIVATION` | Processor creation accepted but final state not confirmed | No | No |
| `ACTIVE` | Card can be used subject to processor and platform controls | Yes | Freeze |
| `FROZEN_BY_CUSTOMER` | Customer temporarily disabled the card | No | Unfreeze |
| `HELD_BY_RISK` | Fraud/compliance/ops placed a mandatory hold | No | No |
| `CLOSED` | Card permanently closed | No | No |
| `FAILED` | Creation failed terminally and no usable card exists | No | No |

Rules:

- `ACTIVE → FROZEN_BY_CUSTOMER → ACTIVE` is the only customer-controlled status cycle.
- `ACTIVE` or `FROZEN_BY_CUSTOMER → HELD_BY_RISK` may be initiated only by an authorized internal actor or risk integration.
- A risk hold takes precedence over a customer freeze. Removing a risk hold restores the effective state to `FROZEN_BY_CUSTOMER` if the customer freeze was still set; otherwise it restores `ACTIVE`.
- `CLOSED` is terminal. Card closure is outside the customer-facing scope but may arrive from the processor and must be represented correctly.
- Unknown or contradictory processor states fail closed: the card is shown as unavailable and a reconciliation incident is created.

## 4. Mid-Level Objectives

### MLO-1 — Secure Virtual Card Issuance

- An eligible, strongly authenticated cardholder can request a card once and receive exactly one logical card despite retries, timeouts, or duplicate delivery.
- Eligibility checks include account status, the issuing entity’s current KYC/AML decision, active-card count, and a risk decision. For Ukraine, the sponsor bank’s decision is final.
- The application stores only the processor token, last four digits, network, expiry month/year, and operational metadata.
- A declined or failed issuance gives the customer a safe, actionable result without revealing internal fraud rules.

**Observable success:** an accepted request produces one processor card, one local card projection, one audit chain, and one customer notification; an ineligible request produces none of those card artifacts but does produce an appropriate audit/security event.

### MLO-2 — Safe Lifecycle Controls

- A cardholder can freeze an `ACTIVE` card and unfreeze a `FROZEN_BY_CUSTOMER` card.
- Authorized operations or risk actors can place and release risk holds according to role and reason-code policy.
- The UI/API never reports a successful state change until the processor has accepted it or the response explicitly communicates asynchronous processing.
- Concurrent or repeated state changes are deterministic and do not weaken a more restrictive state.

**Observable success:** processor state, local projection, audit event, and customer-visible status converge within the defined consistency target, with no customer path capable of removing a risk hold.

### MLO-3 — Spending-Limit Management

- A cardholder can view and configure customer-level per-transaction, daily, and monthly purchase limits. The same limits aggregate purchases across all of the customer’s virtual cards and provisioned wallet tokens in the issuing legal entity.
- Limits are positive, ordered consistently, bounded by product/risk policy, and enforced by the authorization control integration.
- A limit reduction may take effect immediately. A limit increase requires strong customer authentication and may require a risk review.
- All changes preserve exact money values and include before/after values in the audit trail.

Ukraine purchase-limit ceilings:

| Risk segment | Per transaction | Calendar day | Calendar month |
|---|---:|---:|---:|
| `NEW` | UAH 20,000 | UAH 40,000 | UAH 100,000 |
| `STANDARD` | UAH 50,000 | UAH 100,000 | UAH 300,000 |
| `ESTABLISHED` | UAH 100,000 | UAH 250,000 | UAH 750,000 |
| `ENHANCED` | UAH 250,000 | UAH 500,000 | UAH 1,500,000 |

- When the first card is issued and no customer-level purchase-limit aggregate exists, it is initialized to UAH 10,000 per transaction, UAH 20,000 per day, and UAH 50,000 per month. Issuing an additional card reuses the existing aggregate and never resets it. Segment promotion never raises configured limits automatically.
- Calendar-day and calendar-month windows use the issuing legal entity’s timezone; Ukraine uses `Europe/Kyiv`. Non-customer-configurable rolling controls additionally cap spend at 150% of the configured daily limit over any 24 hours and 125% of the configured monthly limit over any 30 days.
- An increase within the `STANDARD` ceiling requires fresh SCA and automated risk checks. A limit above `STANDARD` and up to `ESTABLISHED` requires one Risk Operations approval. A limit above `ESTABLISHED` and up to `ENHANCED` requires separate approvals from Risk Operations and Compliance/Financial Crime.
- `ENHANCED` limits are reviewed at least every 90 days. Temporary exceptions expire after 24 hours. Limits above `ENHANCED` are prohibited for this consumer product.
- Pending authorizations consume capacity immediately; reversals release it. Refunds do not restore daily capacity. A refund matched to a settled purchase may restore monthly capacity according to the ledger-backed policy.
- Regulatory, sanctions, sponsor-bank, processor, scheme, merchant-category, and FX restrictions override product limits. P2P transfers, cash withdrawals, account transfers, and credit exposure use separate limit policies and do not inherit these purchase ceilings.
- Poland, Romania, and Moldova require approved local-currency segment tables immediately before market launch under section 0.3.1; Ukraine limits must not be converted mechanically into launch limits for another market.

**Observable success:** accepted limits are represented identically in the API, database, processor/control integration, and authorization test fixtures; invalid or unsafe combinations are rejected without partial updates.

### MLO-4 — Privacy-Safe Transaction History

- A cardholder can list their card transactions with cursor pagination and filter by date, status, and transaction type.
- Each item shows merchant display name, amount, currency, status, timestamp, and masked card reference; it never exposes processor secrets or prohibited cardholder data.
- Pending-to-posted, reversal, refund, and duplicate-provider-event transitions update one logical transaction rather than creating misleading duplicates.

**Observable success:** customer-visible balances and transaction states reconcile to normalized processor events, while a customer cannot access another customer’s card or transaction identifiers.

### MLO-5 — Operations and Compliance Oversight

- An internal user sees only the data and actions allowed by role, purpose, and tenant/legal-entity scope.
- Operations can search by approved identifiers, inspect synchronization health, place a risk hold, and retry safe reconciliation actions.
- Compliance can reconstruct sensitive changes from immutable audit records and export a tamper-evident, access-logged evidence package.
- Privacy staff can identify each processing purpose and lawful basis, fulfill data-subject requests, apply legal holds and erasure restrictions, and prove that each regulated data plane follows its approved retention and transfer policy.

**Observable success:** every privileged read, export, and mutation is attributable to an authenticated internal identity and reason code; unauthorized combinations are denied and security-logged; privacy requests produce a complete, scope-correct response without erasing records that must be retained by law.

### MLO-6 — Reliable Integration and Recoverability

- Processor timeouts, event duplication, out-of-order events, transient outages, and partial local failures do not create duplicate cards or silently lose confirmed state changes.
- Reconciliation detects differences among processor records, double-entry ledger postings, and customer projections, repairs safe projection differences, and queues unsafe or financial differences for review.
- Operators can correlate one customer action across logs, audit records, events, notifications, and processor requests without using sensitive data.

**Observable success:** automated failure-injection and reconciliation tests restore or surface every seeded inconsistency within the recovery targets; every posted customer transaction references a balanced ledger transaction.

## 5. Non-Functional, Security, and Policy Requirements

### 5.1 Security and Privacy

- Authentication is delegated to the identity provider. Customer endpoints require an authenticated subject and server-side ownership checks on every resource.
- Strong customer authentication is required for virtual-card issuance, unfreeze, spending-limit increases, enabling spending capabilities, credential display, wallet provisioning, card replacement or closure, security-profile changes, release of risk holds, and compliance-export access.
- Except for payment initiation and other explicitly single-use flows, the maximum accepted SCA assertion age is five minutes. Assertions must be bound to the authenticated customer or internal actor, session, intended action, target resource, and material request parameters.
- Payment-authorization assertions and credential-display challenges are single-use and may not authorize another action. Payment SCA must meet applicable dynamic-linking requirements for amount and payee.
- Freeze, limit reduction, and capability disablement require an authenticated session but do not require step-up authentication unless risk policy detects elevated risk.
- SCA must use at least two independent elements from knowledge, possession, and inherence where required by the applicable jurisdiction. Recovery and device-rebinding flows must not be weaker than ordinary SCA.
- Internal access uses least-privilege RBAC with legal-entity scope:
  - `SUPPORT_READ`: masked card and customer-safe transaction view only;
  - `OPS_CONTROL`: support rights plus risk hold and reconciliation actions;
  - `COMPLIANCE_AUDIT`: audit search and export;
  - no role may retrieve full card credentials from this application.
- Service-to-service traffic uses mutually authenticated transport and short-lived workload identity. Public and internal traffic requires TLS 1.2 or later; approved production policy may require TLS 1.3.
- Data at rest is encrypted with managed keys and rotation. Backups use separate encryption keys and access policy.
- PAN, CVV, PIN, access tokens, strong-auth payloads, raw processor payloads, and authentication secrets must never enter logs, traces, analytics, error messages, audit metadata, test fixtures, or support exports.
- Card token, customer ID, transaction ID, IP address, and device data are confidential. Logs use a one-way or scoped correlation representation where the raw value is unnecessary.
- Processor-hosted credential display, if added later, must be isolated so the application backend and analytics cannot read the full PAN or CVV.
- Security controls follow the currently applicable PCI DSS, Ukrainian requirements, GDPR/EEA requirements, DORA where applicable, and approved card-scheme and sponsor controls. Compliance certification and legal interpretation remain organizational responsibilities rather than assumptions in code.

#### 5.1.1 GDPR and Privacy Governance

The Ukraine data plane must comply with Ukrainian personal-data law. The EEA data plane must be designed and operated for GDPR compliance from first use. Moldova must have its own local privacy mapping. The following controls are mandatory across all regions, with GDPR terminology used as the common engineering baseline:

- Maintain a Record of Processing Activities that maps each data category, data subject, purpose, controller/processor role, lawful basis, recipient, location, retention period, security control, and data-subject right.
- Do not use consent as a default basis for processing needed to issue and operate a card. Contract necessity, legal obligation, legitimate interest, fraud prevention, and other bases must be selected and documented per purpose; optional marketing consent must be freely given, granular, versioned, and withdrawable.
- Enforce purpose limitation and data minimization in schemas, APIs, events, analytics, exports, logs, fixtures, and support tooling. A field without an approved purpose, owner, and retention rule must not be collected.
- Legal and the DPO/privacy owner approve a separate privacy notice for each issuing legal entity before launch. The notice is provided in every required and supported market language and identifies the controller, DPO contact, purposes and lawful bases, recipients/processors, international transfers, retention periods, rights, complaint authority, mandatory data, profiling and automated-decision consequences, and available human review.
- The system records the privacy-notice version and delivery timestamp. It must not describe acknowledgement or continued product use as consent. Material changes are communicated before taking effect; separate affirmative consent is collected only where consent is the actual legal basis.
- Support authenticated requests for access, correction, restriction, portability, objection, and erasure. The workflow must search all regulated stores and processors, verify the requester without over-collecting, track the legal deadline, and return a machine-readable package where required.
- Erasure is not absolute. Records required for AML/CFT, accounting, payment disputes, fraud prevention, legal claims, or regulatory audit are restricted from ordinary use, placed under the applicable retention/legal-hold policy, and deleted or irreversibly anonymized when that basis expires.
- Decisions that produce legal or similarly significant effects must not rely solely on opaque automated processing unless an applicable legal basis and safeguards exist. Provide human review, a meaningful explanation of the decision factors that may lawfully be disclosed, and a contest/complaint route.
- Complete a Data Protection Impact Assessment before launch and before material changes to profiling, risk scoring, biometrics, device intelligence, location tracking, cross-region access, or large-scale transaction monitoring. Unmitigated high risk requires prior supervisory consultation where applicable.
- Apply privacy by design and default: least data, least access, shortest justified retention, regional isolation, encryption, pseudonymization, protected non-production data, and privacy acceptance tests.
- Maintain subprocessor inventory, data-processing agreements, transfer mechanism, transfer impact assessment, security due diligence, audit rights, deletion/return terms, incident duties, and advance change notification.
- Treat access from a third country, including remote support or administration by a separate non-EEA entity, as a controlled international-transfer scenario when applicable. No exceptional access occurs without the approved transfer mechanism, purpose, scope, duration, logging, and EEA-controlled keys required by section 6.9.
- Personal-data incidents enter a documented assessment immediately. For EEA processing, the system must provide the evidence needed to notify the supervisory authority within GDPR’s 72-hour window where notification is required and to notify affected people without undue delay where high risk exists.
- The DPO/privacy function reviews the DPIA, processing register, retention schedule, notices, transfer assessments, and data-subject-rights test evidence before release. Local counsel revalidates the schedule and notice before every new-country launch.

#### 5.1.2 Entity-Specific Retention, Legal Holds, and Deletion

Retention is selected by data category, purpose, and issuing legal entity. A longer period applicable to another category, entity, or market must not be applied automatically. GDPR storage limitation applies to identifiable Polish and Romanian data: it may be retained only as long as necessary for the documented purpose.

Jurisdictional AML/KYC overrides:

| Issuing entity/market | Minimum AML/KYC and transaction-evidence rule |
|---|---|
| Ukraine | At least 5 years after termination of the business relationship or completion of an occasional transaction under [Law No. 361-IX](https://zakon.rada.gov.ua/laws/show/361-20#Text), subject to current consolidated law and sponsor-bank policy |
| Poland | 5 years beginning on 1 January of the year following termination or the relevant occasional transaction; GIIF may require an extension of up to 5 additional years under [Polish AML Act Article 49](https://eli.gov.pl/api/acts/DU/2018/723/text.html) |
| Romania | 5 years after termination or the occasional transaction; a competent authority may extend by up to 5 additional years; delete afterward unless another law applies under [Romanian Law No. 129/2019 Article 21](https://legislatie.just.ro/public/DetaliiDocument/216157) |
| Moldova | 5 years after termination or an occasional transaction, with an authority-directed extension of up to 5 additional years under [applicable Moldovan AML legislation](https://www.legis.md/cautare/downloadpdf/136906) |

Other approved starting controls:

| Data class | Baseline | End-of-period action |
|---|---|---|
| AML/KYC evidence and transaction-identification records | Applicable jurisdiction row above plus documented regulator extension or legal hold | Delete or irreversibly anonymize when all holds expire |
| Double-entry ledger, settlement, accounting, and legally required financial records | Entity-specific statutory schedule approved by Finance and Legal; no group-wide 7-year default | Automatic expiry after all statutory and hold periods |
| Card-control audit and compliance decision records | 7 years after event or relationship end, whichever is later, subject to necessity review | Delete identifiers or archive under approved legal basis |
| Customer-visible transaction history | At least 24 months online; older data retrievable only for an approved purpose during statutory retention | Remove from interactive store, then delete/anonymize at statutory expiry |
| Authentication and security event logs | 13 months searchable; longer only for an active investigation or jurisdiction rule | Aggregate/anonymize security metrics and delete raw identifiers |
| General application and infrastructure logs | 90 days searchable, up to 12 months in protected cold storage when justified for resilience/security | Delete automatically |
| Customer-support case content | Case closure plus 2 years, unless tied to a complaint, dispute, fraud case, or legal hold | Delete attachments first; retain only required case metadata |
| Compliance exports | 24-hour download window; generated file deleted within 7 days | Cryptographic erasure and deletion audit |
| Idempotency records | 24 hours for ordinary writes; 7 days for card creation; retain only request hash and safe result | Automatic deletion |
| Product analytics | Use effectively anonymized aggregates where possible; identifiable event data no more than 13 months | Aggregate or delete identifiers |

Legal holds:

- Only the General Counsel or delegated senior Legal counsel may issue or release a legal hold. The MLRO or Compliance lead may impose an emergency preservation freeze for no more than 72 hours while Legal evaluates the matter.
- The DPO reviews scope and minimization but cannot cancel a legally mandatory hold.
- A hold identifies the matter, legal basis, custodians, datasets, jurisdictions, start date, and review date. Indefinite and system-wide holds are prohibited.

Deletion governance:

- Routine expiration-based deletion is automatic and needs no per-record approval after Legal, Privacy/DPO, Compliance, and the data owner approve the schedule.
- Early deletion or a customer erasure request requires Privacy/DPO approval and automated checks for regulatory retention and legal holds.
- An exception or manual purge requires separate approvals from Legal and the DPO. No administrator may approve and execute the same deletion.
- Deletion covers production data, indexes, caches, replicas, restored backups, and vendor copies. A pseudonymous deletion receipt is retained for 5 years.
- Backups inherit the schedule through bounded expiry and expiry-on-restore. A deleted record must never return to active use after restore.

Retention starts, pauses, holds, approvals, execution, vendor confirmation, and deletion outcomes must be machine-enforceable and auditable.

### 5.2 Auditability

Every card creation, freeze, unfreeze, limit change, risk hold, privileged read, export, reconciliation override, and authorization denial must emit an append-only audit event containing:

- unique event ID and schema version;
- UTC event time and server-received time;
- actor type and immutable actor ID;
- subject customer ID and affected resource IDs;
- action, result, reason code, and policy decision ID;
- taxonomy/policy version, disclosure/message code where applicable, reviewer, and review/expiry time;
- separate approval identities, approved scope/value/customer count, case reference, and approval expiry for threshold-controlled actions;
- sanitized before/after state for changed fields;
- correlation ID, request ID, source service, and source channel;
- idempotency key hash for writes, never the raw key if it could contain customer data;
- integrity hash/signature or equivalent tamper-evidence metadata.

Audit records are immutable to application users, access-controlled separately from operational tables, encrypted, replicated, and included in backup/restore tests. Failed and denied sensitive actions are audited. Audit-write failure blocks the corresponding sensitive mutation unless an approved durable transactional outbox guarantees the audit event.

### 5.3 Reliability and Consistency Targets

The following are **assumed initial SLOs** and must be validated against processor capability and production traffic:

| Capability | Target |
|---|---|
| Monthly availability for card reads and controls | 99.95%, excluding declared upstream processor outage only if status is communicated correctly |
| Card create/freeze/unfreeze/limit-write durability | No acknowledged mutation may be silently lost |
| Local read-after-write consistency | Updated state visible to the initiating user within 2 seconds for 99% of accepted synchronous changes |
| Eventual convergence after processor webhook | Within 30 seconds for 99.9% of valid events |
| Automated reconciliation recovery | Safe drift repaired within 15 minutes; unsafe drift queued for human review within 5 minutes |
| Recovery point objective | ≤ 5 minutes for operational projections; zero accepted audit events lost |
| Recovery time objective | ≤ 60 minutes for customer controls; read-only degraded status available within 15 minutes where safe |
| Notification delivery handoff | Event accepted by notification service within 60 seconds for 99% of successful sensitive actions |

Processor procurement SLOs:

| Processor capability | Minimum contractual target |
|---|---|
| Real-time authorization availability | 99.99% monthly |
| Card-management API availability | 99.95% monthly |
| Lifecycle mutation latency | p95 ≤ 1 s; p99 ≤ 2.5 s |
| Card-creation latency | p95 ≤ 2.5 s; p99 ≤ 6 s |
| Valid webhook delivery | p95 ≤ 5 s; p99 ≤ 30 s |
| Durability | No acknowledged mutation or processor event may be lost |
| P1 support | 24×7 acknowledgement ≤ 15 minutes; service restoration ≤ 60 minutes |

These upstream values are procurement requirements rather than a guarantee the application may assume. The platform must degrade safely when the processor breaches them, measure supplier performance independently, and preserve contractual evidence.

### 5.4 Performance and Capacity Targets

These are **assumed targets**, chosen to keep interactive card controls responsive while allowing for processor latency:

| Operation | Target measured at service boundary |
|---|---|
| Get card/list cards | p95 ≤ 300 ms, p99 ≤ 800 ms |
| List transactions from local store | p95 ≤ 500 ms, p99 ≤ 1 s for a page of up to 50 |
| Freeze/unfreeze/limit update | p95 ≤ 1.5 s, p99 ≤ 3 s when processor is healthy |
| Card creation | p95 ≤ 3 s, p99 ≤ 8 s; otherwise return an explicit pending result |
| Internal audit search | p95 ≤ 2 s for a 90-day window and a page of 100 |
| Webhook ingestion acknowledgment | p95 ≤ 200 ms after durable persistence |
| Reconciliation throughput | At least 100,000 cards/hour per worker pool without duplicate side effects |

#### 5.4.1 Traffic Forecast

| Measure | First-year baseline | 24-month growth test |
|---|---:|---:|
| Registered customers | 250,000 | Planning input only; MAU is the binding growth measure |
| Monthly active customers | 100,000 | 500,000 |
| Active virtual cards | 120,000 | 600,000 |
| Card transactions | Approximately 46,000/day | 100 transactions/second peak |
| Average customer API traffic | 15 requests/second | Derived during capacity model refresh |
| Peak customer API traffic | 250 requests/second | 1,000 requests/second |
| Short burst | 500 requests/second for 60 seconds | At least 2× the 24-month steady peak for 60 seconds |
| Processor-event ingestion | 50 events/second | 250 events/second |

- The production platform must meet first-year SLOs with at least 30% service-level headroom after loss of one availability zone.
- Pre-release load tests must cover the 24-month growth case and burst behavior, including webhook backlog replay, reconciliation, export generation, and processor degradation.
- Forecasts are reviewed quarterly and whenever actual peak utilization reaches 50% of a contracted processor quota or 60% of tested platform capacity.
- Forecasts and quotas are recalculated after processor selection and after at least eight weeks of representative production telemetry.

#### 5.4.2 Processor Capacity

The processor contract must publish per-operation quotas no lower than:

| Operation | Normal quota |
|---|---:|
| Card creation | 20 requests/second |
| Lifecycle controls | 50 requests/second |
| Limit updates | 25 requests/second |
| Card reads | 100 requests/second |
| Transaction webhooks | 100 events/second |
| Reconciliation/status retrieval | 100,000 cards/hour |

The table is the initial contracted minimum. Before utilization or the growth forecast exceeds a normal quota, the quota must be raised; transaction-webhook capacity must be at least 250 events/second before the 24-month growth case is admitted. Temporary capacity of at least 5× the normal quota must be contractually available or pre-approved for launches, backlog replay, incident recovery, and migration. Client-side concurrency limits, backpressure, circuit breakers, and replay pacing must keep recovery traffic from starving customer lifecycle controls.

Capacity and abuse boundaries:

- Customer list endpoints use opaque cursor pagination; default page size is 20 and maximum is 50.
- Internal audit search uses opaque cursor pagination; maximum page size is 100 and maximum synchronous date range is 90 days.
- Assumed customer rate limits: 60 read requests/minute, 10 lifecycle writes/minute, 5 creation attempts/day, and 10 limit changes/day per customer, with additional device/IP anomaly controls.
- Internal exports are asynchronous, size-limited, encrypted, expire after 24 hours, and require re-authorization before download.
- Rate-limit responses include a safe retry interval and do not disclose account existence.

### 5.5 Accessibility and Usability

- Customer-visible status names and error messages use plain language and do not rely on color alone.
- All actions expose a stable machine-readable state and a localized display message.
- Destructive or security-reducing actions, especially unfreeze and limit increase, require explicit confirmation.
- Dates are stored in UTC and displayed in the user’s selected time zone with the offset available.
- Monetary values display using the currency’s exponent and locale while remaining exact in storage and transport.

## 6. Implementation Notes and Builder Guardrails

### 6.1 Proposed Architecture

- `card-api`: public application boundary, authentication context, ownership checks, validation, and stable error contract.
- `card-service`: domain state machine, eligibility, idempotency orchestration, and policy evaluation.
- `processor-adapter`: anti-corruption layer around provider-specific card and transaction formats.
- `ledger-adapter`: read-only/reference and separately authorized posting boundary to the issuing entity’s double-entry ledger; the card domain cannot mutate or approve booked amounts.
- `transaction-ingestor`: validates and durably stores processor events before asynchronous normalization.
- `reconciliation-worker`: compares processor records, ledger postings, and local projections and emits repair/review outcomes.
- `ops-api`: separate internal boundary with stronger authorization, purpose/reason capture, and privileged-read auditing.
- PostgreSQL or equivalent transactional store for operational state, idempotency records, and outbox.
- Append-only audit store with access controls independent of the operational database.
- Message broker for durable outbox publication and downstream notifications.

These are guardrails, not a mandate to create distributed services on day one. A modular monolith is acceptable if module boundaries, independent authorization, transactional behavior, and future extraction points are preserved.

### 6.2 Data Conventions

- Monetary values use integer minor units plus ISO 4217 currency code. Floating-point types are forbidden.
- Store currency exponent used at calculation time so historical interpretation remains stable.
- Timestamps use UTC ISO 8601 externally and timezone-aware types internally. Never use local server time.
- Public resource IDs are UUIDv7/ULID-style opaque identifiers. Database sequences and processor IDs are not public IDs.
- API enums are versioned and unknown processor values are preserved in sanitized metadata while mapped to a safe `UNKNOWN` domain state.
- Free-text reason fields are prohibited for automated decisions. Use approved reason codes; optional analyst notes are length-limited, sanitized, access-controlled, and excluded from broad logs.
- Optimistic locking uses a monotonic `version` on card and limit aggregates.

### 6.3 Idempotency and Concurrency

- Card creation, lifecycle mutations, limit changes, risk holds, and privileged exports require an idempotency key.
- Idempotency scope is `(actor, operation, resource, key)` and assumed retention is 24 hours for ordinary writes and seven days for card creation.
- The system stores request fingerprint, processing state, and final response. Reuse with a different payload returns `IDEMPOTENCY_CONFLICT`.
- Concurrent writes use aggregate version checks or serialization. A stale version returns `STATE_CONFLICT` with the current safe state.
- Processor webhook deduplication uses provider event ID plus payload hash. A reused provider ID with a changed payload is quarantined and security-logged.
- Out-of-order events are ordered by provider sequence when available; otherwise the system uses effective time plus state-transition validity and sends ambiguous cases to reconciliation.

### 6.4 Error Semantics

All error responses contain `code`, safe localized `message`, `request_id`, and optional field-level details. They never contain a stack trace, raw provider response, policy rule, card token, or secret.

| Code | Meaning | Expected client behavior |
|---|---|---|
| `VALIDATION_ERROR` | Malformed or inconsistent input | Correct highlighted fields |
| `AUTHENTICATION_REQUIRED` | Missing/invalid authentication | Re-authenticate |
| `STEP_UP_REQUIRED` | Strong authentication missing or stale | Complete challenge |
| `FORBIDDEN` | Actor lacks permission or ownership | Do not retry unchanged |
| `CARD_NOT_FOUND` | Resource absent or concealed by ownership policy | Show generic not-found state |
| `STATE_CONFLICT` | Current state/version does not allow action | Refresh state |
| `LIMIT_POLICY_VIOLATION` | Limit is outside product/risk bounds | Show safe policy range where allowed |
| `IDEMPOTENCY_CONFLICT` | Key reused with a different request | Generate a new key only for a genuinely new action |
| `RATE_LIMITED` | Request exceeds allowed frequency | Retry after indicated interval |
| `UPSTREAM_UNAVAILABLE` | Processor temporarily unavailable | Preserve key and retry safely |
| `PROCESSING` | Durable work accepted but not complete | Poll or await event; do not resubmit as a new action |
| `INTERNAL_ERROR` | Unexpected sanitized failure | Show request ID; safe retry only where documented |

### 6.5 Transaction Semantics

- Transaction identity is based on stable processor transaction ID, not display fields.
- Supported normalized types are `PURCHASE`, `REFUND`, `REVERSAL`, and `ADJUSTMENT`.
- Supported statuses are `PENDING`, `POSTED`, `REVERSED`, `DECLINED`, and `UNKNOWN`.
- Pending and posted amounts are distinct versions of one logical transaction. Tips and incremental authorizations may change the amount and must preserve history.
- Reversal and refund links reference the original transaction when supplied; refund values may not be assumed to equal the original purchase.
- Merchant names are sanitized for display. Raw merchant data is not logged.
- The customer transaction list is a read projection. It must not be presented as the authoritative balance or ledger.
- Every posted customer transaction references a balanced double-entry ledger transaction. Pending authorizations remain distinguishable from posted ledger entries.
- Booked ledger entries are append-only. Corrections use idempotent, auditable compensating entries; reconciliation must never edit or delete an existing ledger entry.

### 6.6 Change Management

- Database and event-schema changes are backward compatible for at least one deployed consumer version.
- New enum values must not crash old consumers; unknown values produce safe behavior and metrics.
- Feature flags default to off and cannot bypass authorization, audit, strong authentication, or processor enforcement.
- Secrets and policy limits come from managed configuration, not source code.
- Production changes require peer review, automated verification, security checks for sensitive changes, and a rollback or forward-fix plan.

### 6.7 Decision Reasons, Customer Messages, and Complaints

Internal reason codes and customer-facing message codes are separate, independently versioned taxonomies. Internal codes, scores, rule identifiers, thresholds, sanctions matches, AML investigations, STR/SAR activity, law-enforcement requests, and analyst notes must never appear in customer APIs, notifications, support screens, complaint exports, analytics, or error details.

#### 6.7.1 Approved Internal Taxonomy

| Internal category/example codes | Disclosure rule | Customer message |
|---|---|---|
| `AUTH.SCA_FAILED`, `AUTH.SESSION_RISK`, `AUTH.DEVICE_INTEGRITY` | Actionable identity explanation only | `VERIFY_IDENTITY` |
| `SECURITY.ATO_SUSPECTED`, `SECURITY.CREDENTIAL_COMPROMISE` | Generic security explanation | `SECURE_ACCOUNT` |
| `LIMIT.PER_TRANSACTION`, `LIMIT.DAILY`, `LIMIT.MONTHLY` | Exact limit type may be disclosed | `LIMIT_REACHED` |
| `TRANSACTION.ANOMALOUS_PATTERN`, `TRANSACTION.MERCHANT_RISK`, `TRANSACTION.GEO_RISK`, `TRANSACTION.VELOCITY` | Generic review only | `CARD_REVIEW` |
| `PROCESSOR.RISK_DECLINE`, `NETWORK.RESTRICTION`, `MCC.RESTRICTED` | Generic decline; processor/network rules remain confidential | `PAYMENT_UNAVAILABLE` |
| `KYC.EXPIRED`, `KYC.DATA_MISMATCH`, `KYC.EDD_REQUIRED` | Required customer action only | `VERIFY_IDENTITY` |
| `AML.MONITORING_REVIEW`, `AML.SOURCE_OF_FUNDS`, `AML.STR_FILED` | Restricted; no investigation or report detail | `CARD_RESTRICTED` |
| `SANCTIONS.POTENTIAL_MATCH`, `SANCTIONS.CONFIRMED_MATCH` | Restricted; no match detail | `CARD_RESTRICTED` |
| `LEGAL.COURT_ORDER`, `LEGAL.LAW_ENFORCEMENT_REQUEST` | Disclose only when Legal authorizes | `CARD_RESTRICTED` |
| `INTEGRITY.STATE_MISMATCH`, `INTEGRITY.AUDIT_DEGRADED`, `PROCESSOR.UNAVAILABLE` | Technical explanation only | `SERVICE_UNAVAILABLE` |
| `OPS.PRECAUTIONARY_HOLD` | Generic review only | `CARD_REVIEW` |

Every decision records taxonomy version, immutable internal reason, source system, policy/rule version, decision ID, disclosure class, message code, review owner, and expiry/review time. Released internal codes are append-only; their meaning cannot be changed. A new meaning requires a new code and migration policy.

General support sees only the approved message and practical next steps. Internal-reason access requires a separate role, purpose, case reference, and audit event. No code, response timing, field, or message variant may allow inference of a confidential reason.

#### 6.7.2 Approved Localized Messages

| Code | Ukrainian | Polish | Romanian |
|---|---|---|---|
| `VERIFY_IDENTITY` | Щоб продовжити користуватися карткою, підтвердьте свою особу в застосунку. | Aby nadal korzystać z karty, potwierdź swoją tożsamość w aplikacji. | Pentru a continua să folosești cardul, verifică-ți identitatea în aplicație. |
| `SECURE_ACCOUNT` | Ми тимчасово обмежили картку, щоб захистити ваш рахунок. Перевірте останні операції та негайно зверніться до підтримки, якщо ви їх не впізнаєте. | Tymczasowo ograniczyliśmy działanie karty, aby chronić Twój rachunek. Sprawdź ostatnie transakcje i natychmiast skontaktuj się z pomocą, jeśli ich nie rozpoznajesz. | Am restricționat temporar cardul pentru a-ți proteja contul. Verifică tranzacțiile recente și contactează imediat serviciul de asistență dacă nu le recunoști. |
| `LIMIT_REACHED` | Платіж не виконано, оскільки досягнуто ліміту картки. Перевірте або змініть ліміти в застосунку. | Płatność nie została zrealizowana, ponieważ osiągnięto limit karty. Sprawdź lub zmień limity w aplikacji. | Plata nu a fost efectuată deoarece a fost atinsă o limită a cardului. Verifică sau modifică limitele în aplicație. |
| `CARD_REVIEW` | Картка тимчасово недоступна, поки ми проводимо перевірку безпеки. Ми повідомимо вас про результат. | Karta jest tymczasowo niedostępna na czas kontroli bezpieczeństwa. Powiadomimy Cię o wyniku. | Cardul este temporar indisponibil cât timp efectuăm o verificare de securitate. Te vom informa despre rezultat. |
| `CARD_RESTRICTED` | Наразі деякі функції картки недоступні. Зверніться до підтримки, щоб дізнатися про доступні подальші кроки. | Niektóre funkcje karty są obecnie niedostępne. Skontaktuj się z pomocą, aby uzyskać informacje o dostępnych dalszych krokach. | Unele funcții ale cardului sunt momentan indisponibile. Contactează serviciul de asistență pentru informații despre pașii disponibili. |
| `PAYMENT_UNAVAILABLE` | Цей платіж не вдалося виконати. Спробуйте інший спосіб оплати або зверніться до підтримки. | Nie udało się zrealizować tej płatności. Użyj innej metody płatności lub skontaktuj się z pomocą. | Plata nu a putut fi efectuată. Folosește o altă metodă de plată sau contactează serviciul de asistență. |
| `SERVICE_UNAVAILABLE` | Операцію не виконано через тимчасову технічну проблему. Спробуйте пізніше. | Operacja nie została wykonana z powodu tymczasowego problemu technicznego. Spróbuj ponownie później. | Operațiunea nu a fost efectuată din cauza unei probleme tehnice temporare. Încearcă din nou mai târziu. |

Messages must not accuse the customer of fraud or promise a resolution time that the investigation cannot meet. Every translation and material change requires local Legal and native-language review, effective date, jurisdiction, and version history.

#### 6.7.3 Complaint and Support Routes

- Every market provides 24×7 in-app card blocking and security reporting.
- Formal complaints are accepted through authenticated in-app messaging, electronic form/email, telephone-to-record, and postal mail. A reference number is issued within one business day.

| Market | Internal service | External escalation |
|---|---|---|
| Ukraine | Ukrainian-language support from Kyiv. Target response: 15 business days and never later than the applicable statutory period. | After contacting the institution, the customer may complain to the [National Bank of Ukraine](https://bank.gov.ua/ua/consumer-protection), including online or at `0 800 505 240`; the NBU states a standard 30-day response, extendable to 45 days for complex cases. |
| Poland | Polish-language support from Warsaw. Payment-service complaints: 15 business days; exceptionally 35 with a holding reply. Electronic complaints are supported. | After the internal complaint, the customer may request intervention or ADR from [Rzecznik Finansowy](https://rf.gov.pl/jak-zlozyc-reklamacje-do-banku-lub-ubezpieczyciela-wazne-zmiany-od-13-lutego-2026-r/). |
| Romania | Romanian-language support from Bucharest. Payment-service complaints: 15 business days; exceptionally 35. | The final response identifies [CSALB](https://csalb.ro/) and the [ANPC complaint portal](https://eservicii.anpc.ro/). |
| Moldova | Romanian-language support from Chișinău; Russian may be offered as an accessibility channel. Payment-service complaints: 15 working days; exceptionally 35. | The customer complains to the provider first and may then petition [CNPF](https://www.cnpf.md/ro/atentie-noua-procedura-de-solutionare-a-reclamatiilor-6307_94161.html); consumer line `+373 22 85 95 95`. |

For Poland and Romania, the 15/35-business-day rule follows [PSD2 Article 101](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32015L2366). The final response is on a durable medium, addresses every issue, and states the decision, permitted explanation, remedy, internal appeal, external authority/ADR body, and filing instructions.

A customer contesting a risk restriction receives human review. Legal or Compliance may redact information whose disclosure would enable control evasion, breach AML/sanctions secrecy, or reveal a protected investigation. Each legal entity’s internal telephone numbers, email addresses, postal addresses, and complaint owners must be populated in controlled configuration before launch; unresolved placeholders are release blockers.

### 6.8 Authoritative Systems and Financial Reconciliation

- The operational card database is a rebuildable projection and workflow store. It is not authoritative for balances, settled transactions, fees, refunds, reversals, or financial adjustments.
- A separate double-entry ledger is the sole source of truth for booked monetary values. For Ukraine it is owned and controlled by the sponsor bank; for the EEA it is the Polish EMI’s authoritative e-money ledger; Moldova uses the ledger of its separate sponsor or licensed entity.
- The processor is authoritative for processor-side card status, network authorizations, and clearing records.
- Customer freeze state, risk holds, capability controls, and configured limits are owned by the card-control domain and synchronized with the processor. A conflict is resolved toward the more restrictive state until reconciliation proves the safe result.
- Customer transaction history is a read projection constructed from processor and ledger events.
- Reconciliation runs continuously, incrementally at least every five minutes, and as a complete daily control with recorded sign-off.
- Safe projection drift is repaired within 15 minutes. Missing, duplicated, unbalanced, wrong-currency, or amount-mismatched financial postings create a high-priority operations case within five minutes.
- The card service cannot create, edit, delete, or approve authoritative-ledger entries. Financial corrections use the regulated entity’s separate idempotent compensating-entry workflow with Finance dual approval and any sponsor-bank approval required by policy.
- A processor or card-control incident is not resolved until processor state, ledger impact, event backlog, and customer projection are reconciled.

### 6.9 Regulated-Entity Isolation and Data Residency

The platform uses isolated regulated data planes for the Ukrainian sponsor bank, Polish EMI, and Moldovan sponsor/entity. Customer funds, ledgers, processor programmes, audit records, encryption keys, risk cases, support attachments, and regulatory reporting are separated by entity. Every request, job, event, export, key use, and support action enforces `regulated_entity_id` and region.

#### 6.9.1 Initial AWS Hosting Baseline

- Amazon Web Services EMEA SARL is the contracted cloud processor.
- Primary production runs in AWS Europe (Frankfurt), `eu-central-1`, Germany, across at least three Availability Zones.
- Disaster recovery uses AWS Europe (Ireland), `eu-west-1`, Ireland, across at least three Availability Zones as encrypted warm standby.
- The first release has one active processing region. Ireland is activated only through the approved DR runbook and becomes read/write only after the failover approvals in section 6.11.
- Customer data, backups, logs, audit records, and encryption keys must not be replicated to any other AWS region.
- The approved AWS infrastructure subprocessors for this topology are [A100 ROW GmbH for Frankfurt and Amazon Data Services Ireland Limited for Ireland](https://aws.amazon.com/compliance/sub-processors/). Region/AZ facts are verified against the [AWS region register](https://docs.aws.amazon.com/global-infrastructure/latest/regions/aws-regions.html).

Logical and cryptographic isolation between the three regulated data planes remains mandatory even though they use the same approved cloud regions. Cross-plane databases, replicas, indexes, buckets, queues, KMS keys, caches, observability stores, and support searches are denied by default.

#### 6.9.2 Approved Support Locations

| Managed support location | Permitted customer population |
|---|---|
| Kyiv, Ukraine | Ukrainian sponsor-bank customers only |
| Warsaw, Poland | EEA customers |
| Bucharest, Romania | EEA customers after the location is operationally approved |
| Chișinău, Moldova | Moldovan customers only |

- Cross-entity support access is denied by default. Access from any other country requires a documented exception, purpose-bound just-in-time authorization, recording, expiry, and any applicable transfer mechanism.
- Support data may not be downloaded to endpoints. Vendor tickets contain sanitized diagnostics only. Customer data must not be shared with globally located vendor support unless the specific transfer and support location are approved.
- No customer data is stored in or accessed from sanctioned jurisdictions or through an unapproved subprocessor.
- Code and effectively anonymized aggregate metrics may be shared globally. Personal data, KYC data, card tokens, transactions, ledger entries, identifiable audit events, attachments, and risk cases may not enter a global control or analytics plane. Pseudonymized data remains region-controlled unless an approved assessment establishes effective anonymization.

#### 6.9.3 Subprocessor Approval

- The initial approved list contains only AWS and the region-specific infrastructure entities above.
- The card processor/tokenization provider remains unapproved until its contracting legal entity, production and DR countries, token-vault/HSM locations, support countries, and downstream subprocessors are named and approved. The same launch gate applies to identity/SCA, KYC, fraud, messaging, observability, and customer-support vendors.
- Descriptions such as “EU,” “global infrastructure,” or “follow-the-sun support” are not sufficiently precise.
- Each register entry contains legal name, service, controller/processor role, data categories and subjects, production/DR regions, support-access countries, subprocessors, retention, deletion/return duties, audit rights, and exit plan.
- A new subprocessor requires at least 30 days’ notice, Privacy, Security, and Legal review, and a contractual right to object or terminate.
- For Ukraine, outsourcing an important payment function also follows the sponsor-bank/NBU process, including [notification to the NBU at least 30 working days before engaging the third party](https://bank.gov.ua/ua/supervision/payment-services/fps).

“Data location” includes storage, backup, DR, logs, observability, support systems, remote administration, vendor support, and every downstream access path.

#### 6.9.4 GDPR International Transfers

- Processing confined to Germany, Ireland, Poland, or Romania does not itself require a GDPR Chapter V transfer mechanism.
- EEA-to-Ukraine, EEA-to-Moldova, or another non-adequate-country remote access path is a restricted international transfer.
- Unless a valid adequacy decision applies to the recipient and processing, the transfer requires the [2021 EU Standard Contractual Clauses](https://eur-lex.europa.eu/legal-content/en/ALL/?uri=CELEX%3A32021D0914), normally Module 2 for controller-to-processor or Module 3 for processor-to-processor, plus an approved Transfer Impact Assessment.
- A separate TIA is required for every importer country and access path, including support, telemetry, backup, and downstream subprocessors. It assesses local surveillance/access law, practical government-access risk, data sensitivity, importer challenge/transparency practice, and supplementary measures.
- Mandatory supplementary measures include EEA-controlled keys, encryption in transit and at rest, pseudonymization, minimization, just-in-time access, MFA, session recording, and prohibition of local export.
- Legal and the DPO approve each TIA; Security validates technical measures. TIAs are reviewed annually and repeated after a material change in country, law, service, subprocessor, region, or access model, following [EDPB Recommendations 01/2020](https://www.edpb.europa.eu/documents/recommendation/recommendations-012020-on-measures-that-supplement-transfer-tools-to_en).
- AWS’s DPA/SCC provisions may support the transfer arrangement but do not replace the project’s TIA, role/module selection, or control assessment.

### 6.10 Processor Capability Contract

No processor is approved solely from sales statements, general documentation, non-binding service objectives, or roadmap commitments. Every critical capability must be demonstrated through versioned documentation, production-compatible sandbox tests, express contractual commitment, and applicable certification/audit evidence.

Each requirement is recorded in a processor qualification matrix as:

| Status | Meaning | Launch treatment |
|---|---|---|
| `SUPPORTED` | Demonstrated without launch-impacting constraint | Eligible for approval |
| `SUPPORTED_WITH_CONSTRAINTS` | Demonstrated with documented limits and accepted controls | Requires owner, residual-risk acceptance, and tests |
| `GAP` | Required capability is absent | Release blocker |
| `ROADMAP` | Depends on an uncommitted or future release | Release blocker; remove the feature or select another processor |
| `NOT_APPLICABLE` | Requirement does not apply to the contracted scope | Requires documented rationale and approval |

`GAP` and `ROADMAP` block production when they affect issuance, lifecycle controls, limits, idempotency, authoritative status lookup, event integrity, transaction normalization, reconciliation, data residency, regulatory audit, or exit.

The selected processor must demonstrate and contractually provide:

- idempotent card creation, lifecycle controls, and limit writes using a client reference;
- lookup by client idempotency/reference after uncertain timeout;
- atomic update of the complete limit set, or an explicit compensating/reconciliation contract where atomicity is impossible;
- authoritative status reads, version/effective time, and stable processor identifiers;
- authenticated, signed, replay-protected, versioned webhooks with stable event IDs and documented ordering semantics;
- duplicate delivery and event replay from an agreed checkpoint or time range;
- card, authorization, clearing, reversal, refund, fee, and dispute records needed for ledger reconciliation;
- bulk status/reconciliation APIs meeting the quotas in section 5.4.2;
- sandbox and certification fixtures for every supported event and failure state;
- separate credentials, keys, data, reports, and settlement configuration per regulated entity;
- audit rights, subprocessor/location disclosure, incident notification, exit/data-portability support, secure deletion evidence, and DORA/outsourcing terms where applicable.

Quotas, latency, availability, event durability, every data-processing/support location, subprocessors, audit rights, and migration/exit duties must appear expressly in the signed contract. Marketing targets do not satisfy this requirement.

Before production, the processor passes end-to-end lifecycle, accept-then-timeout, duplicate/out-of-order event, partial-failure, load, webhook replay, reconciliation, disaster-recovery, data-export, and exit tests. Approval requires recorded sign-off from Engineering, SRE, Security, Privacy, Compliance, Legal, Finance, Reconciliation Operations, and the accountable sponsor bank or regulated entity.

An operation without safe idempotency or result lookup must not be blindly retried. It uses a durable pending intent, processor investigation/reconciliation, and explicit customer processing state. A capability dependent on an uncommitted future processor release is removed from launch scope or causes selection of another processor.

### 6.11 Operational Ownership and Incident Closure

Production requires all named slots below to be populated in the restricted operational roster `OPS-CONTACTS-V1`. The repository stores role/rotation identifiers only, never personal phone numbers or private contact details. The roster contains verified work contacts, provider escalation details, effective dates, and quarterly verification evidence. Deployment is blocked while a required slot or provider escalation path is empty.

| Responsibility | Named accountable slot | Primary rotation | Secondary/escalation |
|---|---|---|---|
| Virtual-card service | `[Service Owner full name]` | `card-platform-primary` — 24×7 | `card-platform-secondary`; Head of Payments Engineering |
| Incident command | `[Incident Management Lead]` | `incident-commander` — 24×7 | Executive Duty Manager |
| Processor incidents | `[Processor Integration Owner]` | `card-platform-primary` | Processor 24×7 NOC, named TAM, contractual escalation manager |
| Infrastructure/database | `[SRE Manager]` | `payments-sre-primary` — 24×7 | `payments-sre-secondary`; cloud enterprise support |
| Reconciliation | `[Payments Operations Lead]` | `reconciliation-ops`; business hours with P0 paging | Finance Controller; Ledger Operations owner |
| Fraud/risk holds | `[Head of Fraud Risk]` | `fraud-risk-primary` — 24×7 | Risk Director |
| AML/sanctions | `[MLRO full name]` | `financial-crime-duty` — 24×7 for urgent cases | Deputy MLRO |
| Audit integrity | `[Audit Platform Owner]` | `security-platform-primary` — 24×7 | CISO or Security Duty Manager |
| Privacy/breach assessment | `[DPO full name]` | `privacy-incident-duty` | General Counsel |
| Customer communication | `[Customer Operations Lead]` | `customer-incident-comms` | Communications Director; Legal reviewer |
| Regulatory notification | `[Compliance Officer full name]` | `regulatory-response-duty` | MLRO, DPO, or General Counsel according to incident type |

Each rotation has a primary and secondary person, weekly handover, quarterly paging test, and maximum 15-minute acknowledgement target. An empty or unacknowledged rotation escalates automatically to the responsible department head.

#### 6.11.1 Incident Escalation

| Severity | Example trigger | Acknowledge | Incident commander | Stakeholder/customer update |
|---|---|---:|---:|---|
| `P0` Critical | Suspected data/audit loss; unauthorized card creation; financial mismatch above UAH 1,000,000 equivalent; more than 10% of customers affected; card controls unavailable for 15 minutes | 5 min | 10 min | Holding message within 30 min; then every 30 min |
| `P1` High | 1–10% of customers affected; processor degradation; reconciliation target missed with potential customer impact | 15 min | 30 min | Within 60 min; then every 60 min |
| `P2` Medium | Limited customer impact, recoverable drift, no funds or data at risk | 4 business hours | As required | Directly to affected customers where necessary |
| `P3` Low | Cosmetic or operational issue without customer impact | 1 business day | Not required | Normally none |

Any responder may declare a higher severity without management approval. Downgrading a `P0` or closing an incident requires both the Incident Commander and relevant accountable owner.

#### 6.11.2 Approval Thresholds

| Action | Required approval |
|---|---|
| Place a risk hold on one customer/card using an approved reason | One authorized Risk Operations analyst |
| Place holds on up to 25 customers/cards | Risk Operations shift lead |
| Place holds on 26–1,000 customers/cards | Separate approval by Risk Director and MLRO/Compliance |
| Hold more than 1,000 customers, more than 1% of active cards, or an entire market | Incident Commander, Risk Director, and Executive Duty Manager; Compliance informed immediately |
| Emergency restrictive action where delay creates material loss | Risk primary or Incident Commander may act; missing approvals recorded within 30 minutes |
| Release an ordinary risk hold | Risk Operations reviewer different from the placer |
| Release an AML, sanctions, legal-order, or confirmed-fraud hold | MLRO/Compliance and Risk Director; Legal approval where a legal order applies |
| Deterministic projection rebuild from authoritative events | Automated and fully audited; no manual approval |
| Restrictive projection correction affecting up to 100 records | Reconciliation Operations lead |
| Less-restrictive correction, more than 100 records, or financial exposure above UAH 100,000 equivalent | Separate approval by Reconciliation Operations and Risk/Finance |
| Any authoritative-ledger adjustment | Prohibited through the card service; use the separate ledger-adjustment process with Finance dual approval |
| DR failover | Incident Commander and SRE primary; Service Owner informed immediately |
| DR failback | Incident Commander, SRE owner, and Service Owner after reconciliation evidence |
| Continue sensitive mutations without durable audit | Prohibited; no override exists |
| Resume mutations after audit degradation | Audit Platform Owner and Incident Commander after integrity/backlog verification |
| Audit export for one customer and up to 90 days | One Compliance Audit approver |
| Export over 100 customers, over 90 days, or crossing legal-entity boundaries | Compliance and DPO/Legal; cross-entity export also requires documented legal basis |
| Publish a preapproved operational holding message | Customer Communications lead |
| Communication mentioning breach, fraud campaign, customer loss, regulatory action, or liability | Incident Commander, Legal, and relevant DPO/MLRO |
| Regulatory notification | Designated Compliance Officer, DPO, MLRO, or General Counsel according to legal responsibility |

All approvals use separate authenticated identities and record approver, action, scope, amount/customer count, case reference, reason, timestamp, and expiry. The requester cannot supply both approvals. Chat messages and verbal consent are not approval evidence. Currency thresholds use configurable local-currency equivalents approved per market.

- The neobank retains end-to-end accountability regardless of processor, sponsor, cloud, or other supplier responsibility.
- Technical recovery, financial reconciliation, audit recovery, privacy/regulatory assessment, and customer communication are separate workstreams with independent owners and completion criteria.
- A processor incident is not closed until card state is stable, the event backlog is drained, contract evidence is captured, and ledger/financial/customer projections are reconciled.
- An audit incident is not closed until queued events are replayed and completeness and tamper evidence are verified.
- Customer communication may announce recovery only after the relevant technical and reconciliation owners approve it. Legal or Compliance approval is required where the message concerns regulatory, privacy, fraud, sanctions, or confidential-investigation matters.
- The Incident Commander maintains one correlation/timeline record while each workstream owner maintains evidence and sign-off.

## 7. Key Flows and Acceptance Scenarios

### 7.1 Create a Virtual Card

1. Customer submits currency, accepted terms version, idempotency key, and recent SCA evidence bound to issuance, customer, session, currency, and terms version.
2. Service verifies identity, eligibility, active-card cap, the issuing entity’s authoritative KYC/AML decision, and risk policy.
3. A durable creation intent and pending audit/outbox state are recorded.
4. Processor adapter creates exactly one tokenized card.
5. Local projection stores only allowed masked metadata; first-card issuance initializes the customer-level limit aggregate when none exists.
6. Success audit event and customer notification are emitted.
7. Response is `ACTIVE`, `PENDING_ACTIVATION`, or a documented safe failure.

Acceptance criteria:

- Retrying the identical request with the same key returns the same logical card ID and does not call processor creation twice after a result is known.
- Reusing the key with a different currency or terms version is rejected.
- Processor timeout produces `PROCESSING` or `UPSTREAM_UNAVAILABLE` without creating a second card on safe retry.
- No prohibited card data appears in the database, logs, traces, analytics, audit record, or response.
- The card is created only in the customer’s regulated-entity data plane and processor program.

### 7.2 Freeze or Unfreeze

1. Customer submits desired action, current aggregate version, and idempotency key.
2. Unfreeze additionally requires recent action- and card-bound SCA; freeze needs an authenticated session unless elevated risk triggers step-up.
3. Domain state machine rejects invalid or less-restrictive transitions under a risk hold.
4. Processor accepts the change before synchronous success is returned.
5. Local state, audit, outbox, and notification are committed consistently.

Acceptance criteria:

- Repeated freeze of an already customer-frozen card returns the existing frozen result without duplicated side effects.
- Customer unfreeze during `HELD_BY_RISK` is denied and audited.
- Two conflicting concurrent actions yield one accepted transition and one `STATE_CONFLICT`, never an impossible state.
- User-visible state converges within the target in section 5.3.
- Freeze remains available during an SCA-provider outage when the authenticated session is valid and risk policy does not require step-up; unfreeze fails closed.

### 7.3 Change Spending Limits

1. Customer supplies all three purchase-limit types, currency, customer-limit aggregate version, and idempotency key.
2. Service validates currency, segment ceiling, approval tier, calendar/rolling controls, and relationships among the limits.
3. Increase requires recent SCA bound to the customer-limit aggregate and full proposed limit set plus automated risk evaluation; reduction requires an authenticated session unless risk policy triggers step-up.
4. Required Risk/Compliance approvals are collected through separate authenticated identities before the change is applied.
5. Authorization controls apply the customer-level set atomically across all cards and wallet tokens or reject it.
6. Exact before/after values, segment, policy version, approvals, and window timezone are audited.

Acceptance criteria:

- Zero, negative, over-policy, wrong-currency, fractional-minor-unit, and internally inconsistent values are rejected.
- A partial upstream update is not reported as success and triggers reconciliation.
- Concurrent updates cannot overwrite a newer set silently.
- Boundary-value fixtures prove exact integer money behavior.
- Ukraine limits do not exceed the assigned `NEW`, `STANDARD`, `ESTABLISHED`, or `ENHANCED` row in section 4; values above `ENHANCED` are always rejected.
- First-card issuance initializes UAH 10,000/20,000/50,000 defaults only when no customer-level aggregate exists; later cards reuse it. Segment promotion does not mutate configured limits.
- Calendar and rolling windows, pending authorizations, reversals, and refunds behave exactly as section 4 specifies.
- Approval-tier, 90-day `ENHANCED` review, and 24-hour temporary-exception tests block stale or under-approved limits.

### 7.4 List Transactions

1. Customer requests an owned card with optional filters and cursor.
2. Service performs ownership authorization before querying records.
3. Records are sorted by effective timestamp descending, then stable ID descending.
4. Response includes a next cursor only when more records exist.

Acceptance criteria:

- Pagination has no duplicates or omissions while new transactions arrive; a snapshot boundary or equivalent stable-cursor strategy is used.
- Invalid/expired cursors return a safe validation error.
- Cross-customer resource probing returns the same concealed response as an unknown resource.
- Pending-to-posted transitions produce one logical item with appropriate history.

### 7.5 Operations Risk Hold and Audit Export

1. Internal actor authenticates with the required role and legal-entity scope.
2. Actor supplies approved reason code, ticket/case reference, and idempotency key.
3. Hold is applied at processor and local projection; the internal reason is mapped to the jurisdiction-approved disclosure class and only the approved customer message is released.
4. Every view, action, and later export is audited.

Acceptance criteria:

- Support-only users cannot place/release holds or export audit data.
- The actor cannot operate outside assigned legal-entity scope.
- Export is generated asynchronously, encrypted, expires after 24 hours, and is unavailable after expiry.
- Export content is minimum necessary, integrity-verifiable, and download access is separately audited.
- Risk-hold release and compliance-export access require SCA for the authorized internal actor and cannot reuse an assertion from another action or case.
- Customer and general-support responses contain no internal reason code, risk score, rule ID, sanctions/watchlist detail, investigation reference, law-enforcement detail, or suspicious-activity-report indicator.

## 8. Edge Cases and Failure Modes

| Scenario | Expected customer/ops behavior | Audit, security, or recovery implication |
|---|---|---|
| Customer has no cards | Return an empty list, not an error | Record ordinary access metrics; no sensitive audit event required |
| Duplicate card-create request | Return original result for matching fingerprint | One logical creation audit chain; alert on suspicious repeated attempts across keys |
| Processor timeout after accepting creation | Show processing state; retry by same idempotency key | Reconcile by provider idempotency/reference before any new create call |
| Local commit fails after processor success | Do not claim ordinary success unless durable recovery state exists | Reconciliation creates projection from processor truth and links original correlation ID |
| Freeze and unfreeze arrive concurrently | Serialize/version-check; one succeeds, one conflicts | Audit accepted and rejected outcomes |
| Customer unfreezes during risk hold | Deny with safe explanation | Security audit includes policy decision but not private fraud logic |
| Risk hold arrives during customer unfreeze | More restrictive risk hold wins | Reconcile processor/local state; notify according to fraud-disclosure policy |
| Limit is zero, negative, or exceeds policy | Reject entire request | Audit repeated policy probing when threshold is met |
| Daily limit exceeds monthly limit | Reject inconsistent configuration | No partial write |
| Limit currency differs from the issuing entity’s purchase-limit policy currency | Reject | Include non-sensitive field error; Ukraine purchase limits are denominated in UAH |
| Amount contains fractional minor unit | Reject | Preserve exact integer-only invariant |
| Limit reduction is below already spent amount | Accept future control only if policy allows; show available limit as zero, never rewrite history | Audit policy outcome and before/after values |
| Processor applies only one of several limits | Show update as not confirmed | Reconcile, attempt safe rollback/forward repair, create ops incident |
| Webhook delivered twice | Acknowledge duplicate without duplicate mutation | Dedup metric and original event reference |
| Provider event ID reused with different body | Quarantine and acknowledge per provider contract | High-severity security/ops alert |
| Webhooks arrive out of order | Apply only valid monotonic transition | Ambiguous events go to reconciliation |
| Unknown processor status | Display unavailable/processing-safe state | Metric, alert, retain sanitized raw enum, fail closed |
| Pending transaction posts at a changed amount | Update one logical transaction and show final amount | Preserve version history for reconciliation |
| Reversal arrives before original transaction | Store unresolved link and retry association | Surface to reconciliation if unresolved after target window |
| Duplicate-looking merchant transactions | Keep separate when processor IDs differ | Do not deduplicate by amount/name/time heuristic |
| Refund exceeds original purchase | Preserve provider event but flag for review | Do not silently clamp or discard financial data |
| New transaction arrives during pagination | Maintain stable snapshot/cursor boundary | Test for no duplicates/omissions |
| Stale or tampered cursor | Return safe validation error | Do not reveal cursor internals |
| Customer guesses another card ID | Return concealed not-found response | Record authorization-denial security signal |
| Internal user lacks purpose/reason | Deny privileged action/read | Audit denial |
| Audit store temporarily unavailable | Block sensitive mutation unless durable outbox guarantees audit | Alert immediately; do not drop audit event |
| Notification service unavailable | Card action remains valid if securely committed | Retry from outbox; show state in-app; monitor delay SLO |
| Rate limit exceeded | Return safe retry guidance | Log structured abuse signal without secrets |
| Expired strong-auth assertion | Require a new challenge | Audit step-up requirement, not secret payload |
| SCA assertion reused for another card/action/amount | Reject as invalid and require a new challenge | Record replay signal without logging assertion material |
| Freeze requested while SCA service is unavailable | Allow with valid authenticated session unless risk policy requires step-up | Preserve the security-reducing restriction and audit degraded authentication path |
| Segment promotion occurs | Keep configured limits unchanged | Audit segment change separately; require a new SCA/risk/approval flow for any limit increase |
| Ukraine request exceeds `STANDARD` but not `ESTABLISHED` | Hold pending one Risk Operations approval | Bind approval to customer, complete limit set, policy version, and expiry |
| Ukraine request exceeds `ESTABLISHED` but not `ENHANCED` | Hold pending separate Risk Operations and Compliance/Financial Crime approvals | Reject requester-as-both-approvers and chat/verbal approval |
| Request exceeds `ENHANCED` | Reject for the consumer product | Audit policy decision; no manual override |
| Rolling 24-hour or 30-day control is reached before calendar limit | Decline further purchase capacity until the rolling window frees | Return only the applicable `LIMIT_REACHED` message and audit policy version |
| Pending authorization is reversed | Release consumed daily/monthly capacity | Apply once by stable authorization ID |
| Settled purchase is refunded | Do not restore daily capacity; restore monthly only when the refund is matched under policy | Reconcile processor and ledger references before release |
| Confidential AML/sanctions hold | Explain only permitted practical effects and complaint/support route | Use `CARD_RESTRICTED`; never expose internal reason, match detail, investigation, or report existence |
| Support user attempts to infer internal hold reason | Return only approved disclosure class/message | Deny and security-audit access to internal taxonomy |
| Posted processor transaction has no ledger entry | Mark projection as under reconciliation without inventing a booked balance | Create high-priority case within 5 minutes; post only through approved ledger workflow |
| Ledger transaction is unbalanced, duplicated, wrong-currency, or amount-mismatched | Do not edit/delete ledger entries or auto-present an unverified correction | High-priority case within 5 minutes; correction requires compensating entry and required approval |
| Cross-region or wrong-entity resource/event | Deny or quarantine; never auto-route based only on customer-supplied region | Security incident signal; prove no cross-plane persistence or support exposure |
| EEA data accessed from a third country without approved just-in-time grant | Block access | Privacy/security incident assessment and immutable access evidence |
| Data-subject erasure request conflicts with AML/accounting hold | Explain the restricted scope; erase eligible data and restrict retained data | Record lawful basis, retention expiry, and deletion follow-up |
| Legal hold requested by an unauthorized actor, without review date, or for an entire system | Reject | Security-audit the attempt; only General Counsel/delegated senior counsel may issue it |
| MLRO/Compliance emergency preservation reaches 72 hours without Legal decision | Stop treating it as a valid hold and escalate before expiry | Legal must issue a scoped hold or the emergency freeze releases automatically |
| Deletion executor is also an approver | Reject manual purge | Require separate Legal and DPO approvals plus a different authenticated executor |
| Configuration attempts replication outside Frankfurt/Ireland | Deployment policy denies the change | Security/Privacy incident; launch or change remains blocked |
| Processor requirement remains `GAP` or `ROADMAP` | Remove dependent feature or reject processor | Production approval cannot be granted |
| Required `OPS-CONTACTS-V1` slot or complaint address is empty | Block deployment | Escalate to accountable department and regulated-entity launch owner |
| Card is closed upstream | Display closed and disable all controls | Reconcile local projection; retain required audit history |
| Restore from backup | Rebuild projections and resume event offsets idempotently | Prove zero audit loss and no duplicate processor calls |

## 9. Verification Strategy and Traceability

### 9.1 Verification Matrix

| Objective | Required verification |
|---|---|
| MLO-1 | Unit tests for eligibility/idempotency; processor contract tests; integration tests for timeout-before/after acceptance; data scans proving prohibited fields are absent; manual security review |
| MLO-2 | State-machine property tests; concurrent integration tests; role/ownership negative tests; failure injection around processor and database boundaries; notification/outbox verification |
| MLO-3 | Boundary/property tests for every Ukraine segment; customer-level aggregation across cards/wallet tokens; calendar/rolling-window tests; approval-tier and expiry tests; atomicity/SCA/reconciliation tests |
| MLO-4 | Provider/ledger event normalization contract tests; balanced-ledger reference checks; stable-pagination tests under concurrent inserts; cross-customer authorization tests; masked-data snapshot tests |
| MLO-5 | RBAC and regulated-entity matrix tests; privileged-read audit tests; disclosure-taxonomy tests; export expiry/encryption/integrity tests; GDPR rights/retention/transfer tests; manual compliance evidence walkthrough |
| MLO-6 | Duplicate/out-of-order webhook tests; processor-ledger-projection drift tests; chaos tests for processor, broker, ledger, and database failures; regional isolation tests; backup restoration exercise |

### 9.2 Required Test Categories

- Unit tests: domain state transitions, policy decisions, exact money conversion, error mapping, cursor validation, and redaction.
- Property-based tests: arbitrary event order, duplicate delivery, limit values, and state-machine invariants.
- Integration tests: database transactions, transactional outbox, audit durability, idempotency, processor adapter, broker, and authorization context.
- Contract tests: processor requests/responses/webhooks and backward-compatible public/internal APIs.
- End-to-end tests: one customer happy path and major failure paths using synthetic processor fixtures only.
- Security tests: broken object-level authorization, role escalation, replay, injection, rate-limit bypass, sensitive-data leakage, export access, and dependency/container scanning.
- Privacy tests: entity/category-specific retention, data-subject rights, legal-hold authority and 72-hour emergency expiry, separation of approval/execution, deletion receipts, notice version/delivery, transfer denial, subprocessor controls, and backup expiry-on-restore.
- Performance tests: first-year and 24-month targets in section 5.4, 60-second bursts, backlog replay, availability-zone loss, and processor quota enforcement, reporting p50/p95/p99, saturation, queue lag, and error rate.
- Resilience tests: processor timeout, delayed webhook, broker outage, audit-store outage, database failover, worker restart, and backup restoration.
- Compliance review: `REG-LAUNCH-*` evidence, sponsor/EMI/passporting perimeter, safeguarding, DPIA, ROPA, retention/hold/deletion mapping, privacy notices, TIAs, subprocessor register, complaints/ADR routes, disclosure taxonomy, processor qualification, contact-roster completeness, processor/ledger responsibility boundary, and threat-model sign-off.

### 9.3 Minimum Fixtures

- Customers: eligible, KYC-pending, blocked, cross-legal-entity, and at active-card cap.
- Cards: all states, stale version, conflicting risk/customer flags, and unknown provider state.
- Limits: every Ukraine segment/default, one unit outside each bound, segment promotion without auto-increase, Standard/Established/Enhanced approvals, temporary expiry, 90-day review, calendar/rolling boundaries, multi-card/wallet aggregation, pending/reversal/refund behavior, currency exponents 0/2/3, and already-spent-above-new-limit.
- Transactions: pending→posted, incremental authorization, reversal-before-original, partial refund, duplicate event, reused-event-ID mismatch, and unknown type/status.
- Actors: customer owner, different customer, support, operations, compliance, expired session, and valid role with wrong legal-entity scope.
- Regions/entities: Ukraine, EEA/Poland, EEA/Romania, Moldova, Frankfurt primary, Ireland warm standby, prohibited third-region/cross-plane access, and approved time-bounded exceptional access.
- Privacy: jurisdiction-specific AML expiry, emergency 72-hour freeze, scoped legal hold, routine/early/manual deletion, dual approval, deletion receipt, notice delivery/version, access/correction/partial erasure/portability/objection, SCC/TIA path, and backup restore after deletion.
- Processor qualification: `SUPPORTED`, constrained, `GAP`, `ROADMAP`, and `NOT_APPLICABLE` capabilities; missing locations/subprocessors; sales-only claim; load, replay, DR, reconciliation, and exit evidence.
- Operations: empty roster slot, unacknowledged rotation, P0/P1 escalation, approval segregation, mass-hold thresholds, DR failover/failback, audit resume, and communication/regulatory approval.
- Failures: processor accept-then-timeout, processor partial update, missing/duplicate/unbalanced ledger posting, local commit failure, broker outage, audit outage, and notification outage.

### 9.4 Release Gates

- All acceptance criteria mapped to automated tests or an explicitly assigned manual review.
- No open critical/high security finding; medium findings have owners and approved deadlines.
- The processor qualification matrix contains no launch-blocking `GAP` or `ROADMAP`; every critical capability has versioned evidence, production-compatible test results, contractual commitment, and required cross-functional sign-off.
- Load test meets first-year SLOs, the 24-month case, burst and backlog-replay targets, and demonstrates controlled degradation when processor quotas are reached.
- Reconciliation repairs every safe seeded projection drift, creates a review item for every unsafe drift, and never edits/deletes a ledger entry.
- Audit sample reconstructs actor, authorization decision, before/after state, and correlation chain without exposing prohibited data.
- Backup restoration meets RPO/RTO targets and does not repeat external mutations.
- AWS Frankfurt/Ireland topology, region restrictions, per-entity keys/stores, warm-standby behavior, support locations, and absence of replication to a third region are proven.
- DPIA, ROPA, entity/category retention schedule, legal-hold/deletion controls, privacy notice, TIA, regulated-entity data-flow map, and subprocessor inventory are approved for each launch entity.
- Automated isolation tests prove that personal and financial data cannot cross regulated data planes or enter global analytics.
- All mandatory `OPS-CONTACTS-V1` owner, rotation, provider, and regulatory slots are populated and paging-tested; no personal phone number is present in the repository.
- Market complaint addresses/channels and external escalation wording are complete and locally approved; no unresolved placeholder remains.
- An unexpired `REG-LAUNCH-{MARKET}-{YYYY-MM-DD}` certification and 48-hour change scan satisfy section 0.3.1.
- Product, architecture, sponsor/regulated entity, Engineering, SRE, Security, Privacy/DPO, Compliance/MLRO, Legal, Finance, Reconciliation, QA, and Operations approve their respective gates.

## 10. Context

### 10.1 Beginning Context

This is a hypothetical greenfield feature within an existing regulated financial platform. Ukraine is the first market; EEA expansion to Poland and Romania and a separately regulated Moldova launch are planned but not yet authorized. Before implementation:

- Customer identity, KYC status, session management, and strong-auth challenge services already exist.
- Candidate processor documentation and sandbox access exist, but the processor is not approved until section 6.10 qualification is complete.
- The Ukrainian sponsor bank owns the authoritative double-entry ledger and final KYC/AML decision; the platform has only contracted integration ports.
- Standard PostgreSQL, message broker, secrets manager, metrics, tracing, and centralized logging are available.
- No application component is approved to store full PAN, CVV, or PIN.
- Regulatory-entity and regional data-plane isolation is an architecture requirement; shared personal-data stores are not available.
- The repository contains only shared platform scaffolding and documentation:
  - `docs/specification.md`
  - `docs/threat-model.md`
  - `src/shared/`
  - `tests/`
- The Ukraine sponsor model, Polish EMI target, Ukraine segment limits, entity-specific retention controls, and AWS regions are recorded decisions. Vendor identities/locations beyond AWS, named roster holders, non-Ukrainian limits, and market-specific final Legal/Compliance evidence remain launch gates.

### 10.2 Ending Context

After all implementation tasks are complete:

- Public card APIs support create, list/get, freeze, unfreeze, limits, and transaction history.
- Internal operations APIs support scoped inspection, risk holds, reconciliation review, and compliance export.
- Domain state machine and exact-money limit policy are independent of processor-specific models.
- Processor webhooks are authenticated, durably ingested, deduplicated, normalized, and reconciled.
- Every posted transaction references a balanced entry in the issuing entity’s authoritative double-entry ledger; for Ukraine that ledger belongs to the sponsor bank. The customer transaction list remains a rebuildable projection.
- Ukraine, EEA, and Moldova regulated data planes are isolated across storage, keys, logs, queues, backups, support, administration, and subprocessors.
- All sensitive mutations and privileged reads have durable, tamper-evident audit evidence.
- Documentation includes API/error contracts, data classification, threat model, DPIA, Record of Processing Activities, retention schedule, transfer assessment, regulated-entity data-flow map, disclosure matrix, runbooks, reconciliation policy, and processor/ledger responsibility boundary.
- Automated unit, property, integration, contract, end-to-end, security, resilience, and performance tests enforce the release gates.
- No implementation stores or logs prohibited cardholder data.

Expected hypothetical artifact tree:

```text
docs/
  specification.md
  architecture.md
  api-contract.md
  data-classification.md
  data-retention.md
  regulatory-register.md
  regulatory-launch/
  ropa.md
  dpia.md
  transfer-impact-assessment.md
  processor-qualification.md
  subprocessor-register.md
  complaints-and-adr.md
  ops-contacts-reference.md
  risk-hold-disclosures.md
  threat-model.md
  runbooks/
    processor-outage.md
    reconciliation.md
    audit-degradation.md
src/
  card_api/
  card_domain/
  processor_adapter/
  transaction_ingestor/
  reconciliation_worker/
  ops_api/
  audit/
  shared/
tests/
  unit/
  property/
  integration/
  contract/
  e2e/
  security/
  performance/
```

## 11. Low-Level Tasks

Tasks are ordered by dependency. Each task names the Mid-Level Objectives it serves.

### 1. Establish Domain Vocabulary and Card State Machine

**Traceability:** MLO-1, MLO-2, MLO-6

**What prompt would you run to complete this task?**  
Create processor-independent card domain types and an explicit state machine from sections 3 and 6. Reject invalid transitions and make more restrictive controls take precedence.

**What file do you want to CREATE or UPDATE?**  
`src/card_domain/models.*`, `src/card_domain/state_machine.*`, `tests/unit/test_card_state_machine.*`

**What function do you want to CREATE or UPDATE?**  
`Card`, `CardStatus`, `CardControlState`, `transition_card_state`

**What are details you want to add to drive the code changes?**

- Represent customer freeze and risk hold independently so releasing one cannot erase the other.
- Make `CLOSED` terminal and unknown/contradictory states fail closed.
- Use opaque IDs, UTC timestamps, and aggregate versions.
- Add table-driven tests for every permitted and denied transition.
- **Definition of done:** all state rules in section 3.2 are executable tests and no processor enum leaks into the domain layer.

### 2. Define Exact-Money and Spending-Limit Policy

**Traceability:** MLO-3

**What prompt would you run to complete this task?**  
Implement exact monetary value types and validation for per-transaction, daily, and monthly limits using configurable policy bounds.

**What file do you want to CREATE or UPDATE?**  
`src/card_domain/money.*`, `src/card_domain/limits.*`, `tests/property/test_limit_policy.*`

**What function do you want to CREATE or UPDATE?**  
`Money`, `SpendingLimits`, `validate_limit_change`

**What are details you want to add to drive the code changes?**

- Use integer minor units and ISO currency; forbid floating point.
- Validate currency, exponent, positivity, configured min/max, and relationships among limits.
- Implement the Ukraine `NEW`, `STANDARD`, `ESTABLISHED`, and `ENHANCED` UAH ceilings plus UAH 10,000/20,000/50,000 first-card initialization when no customer aggregate exists.
- Aggregate purchase consumption at customer level across all cards and wallet tokens; implement `Europe/Kyiv` calendar windows and 150%/24-hour plus 125%/30-day rolling controls.
- Model approval tiers, 90-day `ENHANCED` review, and 24-hour temporary exceptions. Segment promotion must not raise configured limits.
- Apply pending authorization, reversal, and refund capacity semantics from section 4.
- Return structured policy violations without exposing fraud rules.
- Include property tests across currency exponents 0, 2, and 3 and exact boundary fixtures.
- **Definition of done:** invalid values never reach persistence or processor calls, and serialization round-trips without value loss.

### 3. Design Persistence, Idempotency, and Transactional Outbox

**Traceability:** MLO-1, MLO-2, MLO-3, MLO-6

**What prompt would you run to complete this task?**  
Design transactional persistence for card projections, customer-level limit aggregates, creation intents, idempotency records, provider events, and outbox messages.

**What file do you want to CREATE or UPDATE?**  
`src/shared/persistence/*`, `migrations/*`, `tests/integration/test_transactions_and_idempotency.*`

**What function do you want to CREATE or UPDATE?**  
`IdempotencyRepository`, `CardRepository`, `OutboxRepository`, transaction unit-of-work

**What are details you want to add to drive the code changes?**

- Enforce unique idempotency scope and request fingerprints.
- Key each purchase-limit aggregate by customer and issuing legal entity; never create one independent bypassable limit budget per card or wallet token.
- Persist final responses and safe in-progress status for retries.
- Use optimistic version constraints and unique provider event IDs.
- Atomically commit state, audit intent, and outbox where required.
- **Definition of done:** crash-point integration tests show no acknowledged lost write, duplicate card, or missing required event.

### 4. Create Processor Anti-Corruption Adapter

**Traceability:** MLO-1, MLO-2, MLO-3, MLO-6

**What prompt would you run to complete this task?**  
Define a processor-neutral interface and one sandbox adapter for card creation, lifecycle controls, limits, status lookup, and transaction-event verification.

**What file do you want to CREATE or UPDATE?**  
`src/processor_adapter/ports.*`, `src/processor_adapter/provider_client.*`, `tests/contract/test_processor_contract.*`, `docs/processor-qualification.md`

**What function do you want to CREATE or UPDATE?**  
`CardProcessorPort`, `create_card`, `set_card_control`, `set_limits`, `get_card_state`, `verify_webhook`

**What are details you want to add to drive the code changes?**

- Pass provider idempotency/correlation references on all supported writes.
- Support result lookup by client reference after uncertain timeout and event replay from a documented checkpoint.
- Require atomic complete-limit updates or a documented partial-update/reconciliation contract.
- Map provider errors into the stable error contract.
- Sanitize responses before logging; never deserialize prohibited data into broad application models.
- Define timeouts, bounded retry with jitter, circuit breaking, and no blind retry for uncertain non-idempotent operations.
- Verify the capacity, latency, availability, data-residency, audit-right, exit, and incident obligations in sections 5.3, 5.4.2, 6.9, and 6.10.
- Produce the `SUPPORTED`/constrained/`GAP`/`ROADMAP`/`NOT_APPLICABLE` qualification matrix with versioned documentation, sandbox, contract, and certification evidence.
- Run end-to-end lifecycle, accept-then-timeout, duplicate/out-of-order event, partial failure, load, replay, reconciliation, DR, data-export, and exit tests.
- **Definition of done:** every critical capability is `SUPPORTED` or explicitly accepted `SUPPORTED_WITH_CONSTRAINTS`; no release-blocking `GAP`/`ROADMAP` remains; all section 6.10 sign-offs are recorded.

### 5. Implement Eligibility and Card Issuance Orchestration

**Traceability:** MLO-1, MLO-6

**What prompt would you run to complete this task?**  
Implement the issuance workflow in section 7.1 using identity, KYC, risk, idempotency, processor, persistence, audit, and outbox ports.

**What file do you want to CREATE or UPDATE?**  
`src/card_domain/issuance_service.*`, `src/card_api/create_card.*`, `tests/integration/test_card_issuance.*`

**What function do you want to CREATE or UPDATE?**  
`issue_virtual_card`, public create-card handler

**What are details you want to add to drive the code changes?**

- Require accepted terms version, card currency, and recent action-bound strong authentication.
- Enforce configurable card cap and safe risk/KYC decisions.
- Use the issuing entity’s final KYC/AML decision; for Ukraine the sponsor bank is authoritative. Initialize the Ukraine default limit aggregate only for the customer’s first card.
- Recover accept-then-timeout by querying processor reference before another creation attempt.
- Return active, pending, or documented failure; never fabricate success.
- **Definition of done:** the four acceptance criteria in section 7.1 pass under repeated and concurrent requests.

### 6. Implement Customer Card Read APIs

**Traceability:** MLO-1, MLO-2, MLO-3

**What prompt would you run to complete this task?**  
Create customer list/get endpoints that return masked metadata, effective control status, the shared customer-level purchase-limit view, and synchronization freshness.

**What file do you want to CREATE or UPDATE?**  
`src/card_api/card_queries.*`, `tests/integration/test_card_queries.*`

**What function do you want to CREATE or UPDATE?**  
`list_customer_cards`, `get_customer_card`

**What are details you want to add to drive the code changes?**

- Derive ownership from authenticated subject, never from a trusted request-body customer ID.
- Conceal cross-customer resources using the same response as an unknown card.
- Return only allowlisted fields and include projection freshness when stale.
- Meet pagination and latency targets.
- **Definition of done:** authorization-negative, empty-state, masking, pagination, and p95 performance tests pass.

### 7. Implement Freeze and Unfreeze Workflow

**Traceability:** MLO-2, MLO-6

**What prompt would you run to complete this task?**  
Implement idempotent freeze/unfreeze commands with version checks, strong authentication for unfreeze, processor confirmation, audit, and notification outbox.

**What file do you want to CREATE or UPDATE?**  
`src/card_domain/card_control_service.*`, `src/card_api/card_controls.*`, `tests/integration/test_card_controls.*`

**What function do you want to CREATE or UPDATE?**  
`freeze_card`, `unfreeze_card`

**What are details you want to add to drive the code changes?**

- Enforce the state model and risk-hold precedence.
- Treat repeated identical action as idempotent; reject conflicting stale versions.
- Preserve a recoverable record when processor success precedes local failure.
- Emit safe customer notification without revealing fraud logic.
- **Definition of done:** all acceptance criteria in section 7.2 and concurrent-action tests pass.

### 8. Implement Limit Read and Update Workflow

**Traceability:** MLO-3, MLO-6

**What prompt would you run to complete this task?**  
Implement read and atomic update of all spending limits with exact money, policy evaluation, strong authentication for increases, versioning, and audit.

**What file do you want to CREATE or UPDATE?**  
`src/card_domain/limit_service.*`, `src/card_api/card_limits.*`, `tests/integration/test_card_limits.*`

**What function do you want to CREATE or UPDATE?**  
`get_spending_limits`, `update_spending_limits`

**What are details you want to add to drive the code changes?**

- Update the complete customer-level limit set atomically across all cards and wallet tokens.
- Treat partial provider success as unconfirmed and create reconciliation work.
- Audit exact before/after minor units and currency.
- Require an SCA assertion bound to the customer-limit aggregate and complete proposed set for increases; allow authenticated-session reductions unless elevated risk triggers step-up.
- Enforce the Ukraine segment ceiling and separate Risk/Compliance approval tiers; prohibit above-`ENHANCED` consumer limits.
- Enforce idempotency and aggregate version.
- **Definition of done:** all acceptance criteria in section 7.3 and money property tests pass.

### 9. Build Durable Webhook Ingestion and Transaction Normalization

**Traceability:** MLO-4, MLO-6

**What prompt would you run to complete this task?**  
Authenticate processor webhooks, durably persist them before acknowledgment, deduplicate, order safely, and normalize card/transaction events.

**What file do you want to CREATE or UPDATE?**  
`src/transaction_ingestor/webhook.*`, `src/transaction_ingestor/normalizer.*`, `tests/contract/test_webhook_events.*`

**What function do you want to CREATE or UPDATE?**  
`ingest_webhook`, `normalize_transaction_event`, `apply_provider_event`

**What are details you want to add to drive the code changes?**

- Verify signature, timestamp/replay window, content type, and size before processing.
- Quarantine reused event IDs with changed hashes.
- Model pending→posted, reversals, refunds, and unknown statuses without misleading deduplication.
- Acknowledge within the performance target after durable persistence.
- **Definition of done:** duplicate/out-of-order/unknown/reversal-before-original fixtures converge or create explicit review work with no lost event.

### 10. Implement Stable Customer Transaction History

**Traceability:** MLO-4

**What prompt would you run to complete this task?**  
Create an ownership-protected transaction-list endpoint with stable opaque cursor pagination, filters, and allowlisted customer display fields.

**What file do you want to CREATE or UPDATE?**  
`src/card_api/transactions.*`, `src/card_domain/transaction_queries.*`, `tests/integration/test_transaction_history.*`

**What function do you want to CREATE or UPDATE?**  
`list_card_transactions`, cursor codec

**What are details you want to add to drive the code changes?**

- Support date, status, and type filters with maximum range policy.
- Sort by effective time and stable ID using a snapshot boundary.
- Mask card reference and sanitize merchant display name.
- Reject expired/tampered cursors safely.
- **Definition of done:** all acceptance criteria in section 7.4 pass, including concurrent-insert pagination tests and p95 target.

### 11. Add Internal Authorization and Risk-Hold Controls

**Traceability:** MLO-2, MLO-5

**What prompt would you run to complete this task?**  
Implement the internal authorization boundary and risk-hold workflow with role, legal-entity scope, purpose, reason, and case reference enforcement.

**What file do you want to CREATE or UPDATE?**  
`src/ops_api/authorization.*`, `src/ops_api/risk_holds.*`, customer-message configuration, `docs/risk-hold-disclosures.md`, `docs/complaints-and-adr.md`, `tests/security/test_internal_access_matrix.*`

**What function do you want to CREATE or UPDATE?**  
`authorize_internal_action`, `place_risk_hold`, `release_risk_hold`, `map_customer_message`, complaint intake/routing

**What are details you want to add to drive the code changes?**

- Deny by default and separate support, operations, and compliance capabilities.
- Require idempotency and an approved structured reason code.
- Apply the more restrictive state and preserve customer-freeze state underneath.
- Implement the immutable internal reason codes, customer-message codes, Ukrainian/Polish/Romanian text, disclosure rules, and complaint routes in section 6.7.
- Require action/case-bound SCA for risk-hold release.
- Return only approved localized customer messages and practical-effect guidance; never expose internal scores, rules, investigations, sanctions/watchlist details, law-enforcement requests, or suspicious-activity-report information.
- Enforce the single/mass-hold and hold-release approval thresholds in section 6.11.2 with separate identities.
- Audit denied actions and privileged reads.
- **Definition of done:** the actor/action/legal-entity/approval matrix passes; leakage tests find no internal reason in customer/support/complaint surfaces; every market’s complaint placeholders are completed.

### 12. Implement Append-Only Audit and Compliance Export

**Traceability:** MLO-5, MLO-6

**What prompt would you run to complete this task?**  
Create the audit schema and writer, privileged search, and asynchronous encrypted compliance export described in sections 5.2 and 7.5.

**What file do you want to CREATE or UPDATE?**  
`src/audit/events.*`, `src/audit/writer.*`, `src/ops_api/audit_search.*`, `src/ops_api/audit_export.*`, `tests/integration/test_audit.*`

**What function do you want to CREATE or UPDATE?**  
`append_audit_event`, `search_audit_events`, `request_audit_export`, `download_audit_export`

**What are details you want to add to drive the code changes?**

- Validate required audit fields and redact prohibited data.
- Provide tamper evidence and independent authorization.
- Make exports minimum-necessary, encrypted, expiring, and access-logged.
- Require action- and export-bound SCA before export generation and download; do not reuse another privileged assertion.
- Apply regulated-entity scope, GDPR/data-subject export rules, retention expiry, and legal holds.
- Block sensitive actions when their audit guarantee cannot be met.
- **Definition of done:** a reviewer reconstructs seeded flows end-to-end, detects a modified export, and proves expired/wrong-scope downloads fail.

### 13. Build Reconciliation and Safe Repair

**Traceability:** MLO-2, MLO-3, MLO-4, MLO-6

**What prompt would you run to complete this task?**  
Implement continuous, scheduled, and on-demand reconciliation among processor records, the authoritative double-entry ledger, and local card, limit, and transaction projections.

**What file do you want to CREATE or UPDATE?**  
`src/reconciliation_worker/reconcile.*`, `src/ops_api/reconciliation.*`, `tests/integration/test_reconciliation.*`

**What function do you want to CREATE or UPDATE?**  
`reconcile_card`, `reconcile_financial_posting`, `classify_drift`, `apply_safe_repair`, `create_review_item`

**What are details you want to add to drive the code changes?**

- Classify drift as safe auto-repair, retryable, or human-review-required.
- Never make a card less restrictive as an automatic repair when truth is ambiguous.
- Require every posted transaction to reference a balanced ledger transaction.
- Never edit or delete a ledger entry and never adjust it through the card service; invoke the regulated entity’s separate idempotent compensating-entry process with Finance dual approval.
- Run incrementally at least every five minutes and execute a complete daily control with sign-off.
- Create a high-priority case within five minutes for a missing, duplicate, unbalanced, wrong-currency, or amount-mismatched posting.
- Make repair idempotent and audit every decision.
- Support checkpoints so worker restarts do not skip or duplicate effects.
- **Definition of done:** all seeded drift fixtures meet the detection/recovery targets and throughput is at least 100,000 cards/hour per worker pool.

### 14. Add Observability, Redaction, Alerts, and Runbooks

**Traceability:** MLO-5, MLO-6

**What prompt would you run to complete this task?**  
Add privacy-safe metrics, structured logs, distributed correlation, SLO dashboards, alerts, and operator runbooks for processor, audit, event, and reconciliation failures.

**What file do you want to CREATE or UPDATE?**  
`src/shared/observability/*`, `docs/runbooks/*`, `docs/ops-contacts-reference.md`, deployment dashboard/alert and paging definitions

**What function do you want to CREATE or UPDATE?**  
redaction filter, correlation middleware, SLO metric emitters

**What are details you want to add to drive the code changes?**

- Use allowlisted log fields; test redaction against nested failures and provider payloads.
- Track latency, error rate, pending operations, webhook lag, reconciliation drift, notification lag, and audit-write failures.
- Alerts link to actionable runbooks and named workstream owners from section 6.11 and avoid customer data in titles/payloads.
- Resolve owners and provider escalations through `OPS-CONTACTS-V1`; keep personal phone numbers out of the repository.
- Implement P0–P3 paging, update cadence, empty-rotation escalation, quarterly paging tests, and closure approvals from section 6.11.
- Correlate end-to-end using safe IDs.
- **Definition of done:** synthetic processor, ledger, audit, privacy, and customer-communication incidents trigger the correct alert/runbook/owner; closure is blocked until each required workstream signs off; automated scans find no prohibited data in logs or traces.

### 15. Complete Security, Resilience, Performance, and Release Verification

**Traceability:** MLO-1 through MLO-6

**What prompt would you run to complete this task?**  
Implement the verification matrix in section 9, publish evidence, and block release when a required gate fails.

**What file do you want to CREATE or UPDATE?**  
`tests/security/*`, `tests/performance/*`, `tests/e2e/*`, CI configuration, `docs/verification-report.md`, `docs/regulatory-register.md`, `docs/regulatory-launch/*`

**What function do you want to CREATE or UPDATE?**  
Security test suite, load scenarios, failure-injection scenarios, release-gate workflow

**What are details you want to add to drive the code changes?**

- Exercise the first-year forecast, 24-month growth case, 60-second bursts, zone loss, event-backlog replay, and contracted processor quotas with percentile/error/saturation reporting.
- Verify broken-object authorization, RBAC scope, replay, rate limiting, redaction, and export controls.
- Verify action/resource/parameter-bound SCA, single-use payment and credential-display assertions, and authenticated-session freeze/reduction behavior.
- Inject processor, ledger, database, broker, audit, and notification failures.
- Perform backup restore and prove no external mutation is replayed.
- Produce an unexpired `REG-LAUNCH-*` record, 48-hour change scan, sponsor/EMI/passporting evidence, DPIA, ROPA, entity-specific retention/hold/deletion schedule, privacy notices, TIAs, subprocessor register, processor qualification, complaint/ADR evidence, contact-roster completeness report, and disclosure matrix.
- Map every acceptance criterion to test evidence or named manual approval.
- **Definition of done:** every release gate in section 9.4 is green or release is automatically blocked with an attributable exception record.

### 16. Implement Regulated-Entity Isolation and Privacy Lifecycle

**Traceability:** MLO-1, MLO-4, MLO-5, MLO-6

**What prompt would you run to complete this task?**  
Implement Ukraine, EEA, and Moldova regulated data-plane isolation plus GDPR/Ukrainian/Moldovan privacy lifecycle controls from sections 5.1 and 6.9.

**What file do you want to CREATE or UPDATE?**  
`src/shared/regulated_entity.*`, `src/shared/privacy/*`, infrastructure policies, `tests/security/test_region_isolation.*`, `tests/privacy/*`, `docs/ropa.md`, `docs/dpia.md`, `docs/data-retention.md`, `docs/transfer-impact-assessment.md`, `docs/subprocessor-register.md`, per-entity privacy notices

**What function do you want to CREATE or UPDATE?**  
regulated-entity authorization middleware, regional routing policy, retention/deletion orchestrator, data-subject-rights workflow, exceptional-access workflow

**What are details you want to add to drive the code changes?**

- Bind every customer, resource, event, key, queue, log, backup, support case, processor program, and ledger to one regulated entity and data plane.
- Deny cross-plane access by default; do not trust a customer-supplied region or entity identifier.
- Deploy active production only in AWS Frankfurt across three AZs and encrypted warm standby only in AWS Ireland; block all replication to a third AWS region.
- Enforce Kyiv/Warsaw/Bucharest/Chișinău support-location scope and prohibit local downloads and unsanitized vendor tickets.
- Keep EEA data and EEA-controlled keys in the EEA; require the applicable SCC module, per-country/access-path TIA, just-in-time grant, masking, MFA, session recording, and expiry for exceptional third-country access.
- Implement access, correction, restriction, portability, objection, and scoped erasure with statutory holds and deletion follow-up.
- Enforce entity/category-specific retention, 72-hour emergency freezes, scoped Legal holds, dual-approved manual purge, 5-year pseudonymous receipts, privacy-notice delivery/version, and backup expiry-on-restore.
- Prohibit identifiable regional data from global analytics; verify that pseudonymized data remains region-controlled unless an approved anonymization assessment says otherwise.
- **Definition of done:** isolation tests prove no cross-plane read/write/event/log/backup/support leakage; privacy fixtures complete within policy deadlines; expired data cannot reappear after restore; Privacy, Security, Compliance, and Legal approve the evidence.

## 12. Traceability Summary

| Task | MLO-1 | MLO-2 | MLO-3 | MLO-4 | MLO-5 | MLO-6 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| 1. Domain/state model | ✓ | ✓ |  |  |  | ✓ |
| 2. Money/limit policy |  |  | ✓ |  |  |  |
| 3. Persistence/idempotency | ✓ | ✓ | ✓ |  |  | ✓ |
| 4. Processor adapter | ✓ | ✓ | ✓ |  |  | ✓ |
| 5. Issuance | ✓ |  |  |  |  | ✓ |
| 6. Customer card reads | ✓ | ✓ | ✓ |  |  |  |
| 7. Freeze/unfreeze |  | ✓ |  |  |  | ✓ |
| 8. Limit workflow |  |  | ✓ |  |  | ✓ |
| 9. Webhook ingestion |  |  |  | ✓ |  | ✓ |
| 10. Transaction history |  |  |  | ✓ |  |  |
| 11. Internal controls |  | ✓ |  |  | ✓ |  |
| 12. Audit/export |  |  |  |  | ✓ | ✓ |
| 13. Reconciliation |  | ✓ | ✓ | ✓ |  | ✓ |
| 14. Observability/runbooks |  |  |  |  | ✓ | ✓ |
| 15. Release verification | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 16. Entity isolation/privacy | ✓ |  |  | ✓ | ✓ | ✓ |

## 13. Recorded Decisions and Final Approval Items

The product and architecture direction is now explicit:

1. Ukraine launches through a licensed sponsor bank that is the regulated account provider, issuer, funds holder, authoritative-ledger owner, and final KYC/AML decision-maker; the platform is an outsourced technology/card-control provider.
2. The independent EEA target is a Polish EMI with genuine Polish substance. Romania is entered through freedom-to-provide-services passporting and later a branch only if needed. Moldova remains under a separate local sponsor/entity.
3. Polish EMI customer funds use segregated safeguarding accounts at no fewer than two EEA credit institutions and are reconciled daily to the authoritative e-money ledger; they are not deposits.
4. Ukraine customer-level purchase limits, defaults, calendar/rolling windows, multi-card/wallet aggregation, approval tiers, reviews, and capacity semantics are fixed in section 4.
5. Retention, legal holds, deletion approvals/receipts, and privacy notices are controlled per data category and issuing entity under section 5.1.2.
6. The first hosting topology is active AWS Frankfurt with encrypted warm standby in AWS Ireland, isolated data planes, named support countries, a controlled subprocessor register, and SCC/TIA controls for restricted transfers.
7. A processor requires the evidence-based qualification matrix, contract terms, failure/load/DR/exit tests, and cross-functional sign-off in section 6.10; roadmap dependencies block release.
8. Internal risk codes, localized customer messages, complaint routes, and disclosure prohibitions are fixed in section 6.7.
9. Mandatory owner slots, `OPS-CONTACTS-V1`, P0–P3 escalation, approval thresholds, and incident-closure criteria are fixed in section 6.11.
10. Each country launch requires the staged, dated, and unexpired regulatory verification record in section 0.3.1.

The following items still require formal approval rather than another product-level assumption:

1. The Ukrainian sponsor bank’s legal name, executed outsourcing/issuer/ledger agreements, sponsor approvals, and NBU filings.
2. Polish EMI authorization, safeguarding-bank identities, KNF validation/passport notification, Romanian commencement confirmation, and Moldovan sponsor/entity authorization.
3. The selected processor and every other vendor’s complete legal entity, region, HSM/token-vault, support-country, subprocessor, retention, audit, and exit evidence; only AWS infrastructure is initially approved.
4. Poland, Romania, and Moldova purchase-limit tables and configurable local-currency equivalents for incident/approval thresholds.
5. Named roster holders, secondary responders, provider contacts, legal-entity complaint addresses/channels, and passing paging tests.
6. Per-entity final privacy notices, TIAs for every restricted access path, entity-specific non-AML statutory periods, and approved deletion-vendor evidence.
7. An unexpired `REG-LAUNCH-{MARKET}-{YYYY-MM-DD}` record and final 48-hour change scan for each actual launch date.
