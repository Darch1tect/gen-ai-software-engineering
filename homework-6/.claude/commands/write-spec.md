---
description: Generate or refresh specification.md for the multi-agent banking pipeline from the standard template
---

Generate (or refresh) `specification.md` at the project root, following the Banking-Specific
Specification Template from `../homework-3/specification-TEMPLATE-example.md` and the structure
required by `TASKS.md`.

Steps:
1. Read `TASKS.md` (Task 1 requirements) and `sample-transactions.json` to ground every objective
   and low-level task in the real shape of the input data — don't invent fields that aren't there.
2. Read the existing `specification.md` if present, and `agents.md`, to preserve any
   project-specific decisions already recorded (thresholds, statuses, agent names) rather than
   silently overwriting them.
3. Write `specification.md` with exactly these five sections, in this order:
   - **High-Level Objective** — one sentence.
   - **Mid-Level Objectives** — 4-5 concrete, testable bullets (e.g. fraud threshold, rejected-
     transaction handling, audit logging, PII handling).
   - **Implementation Notes** — monetary type (`decimal.Decimal`, never `float`), ISO 4217
     currency handling, audit-log fields (timestamp, agent name, transaction ID, outcome), and the
     no-plaintext-PII rule for account numbers/names.
   - **Context** — Beginning state (`sample-transactions.json`) and Ending state (`shared/results/`
     populated, a pipeline summary report, test coverage target).
   - **Low-Level Tasks** — one entry per agent (Transaction Validator, Fraud Detector, Compliance
     Checker, Settlement Processor, and any others actually implemented), each with the exact
     `Task / Prompt / File to CREATE / Function to CREATE / Details` fields from the template.
4. Cross-check every Low-Level Task against the real files in `agents/` and `integrator.py` if
   they already exist — the spec must describe the system as built, not an aspirational one.
5. Report a short diff summary of what changed versus the previous `specification.md` (or note
   that it was created fresh).
