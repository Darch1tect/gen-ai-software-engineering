---
description: Validate all transactions in sample-transactions.json without running the full pipeline
---

Validate all transactions in `sample-transactions.json` without processing them through fraud
detection, compliance, or settlement.

Steps:
1. Load `sample-transactions.json` from the project root.
2. For each transaction, call `agents.transaction_validator.validate_transaction(data)` directly
   (e.g. via `.venv/bin/python -c "..."` or a short throwaway script) — do **not** invoke
   `integrator.run_pipeline`, and do not write anything to `shared/`. This is a dry-run: read-only
   against the input file, no side effects.
3. Report:
   - Total transaction count
   - Valid count (`status == "validated"`)
   - Invalid count (`status == "rejected"`)
   - For each invalid transaction: its `transaction_id` and `reason`
4. Show the results as a table with columns: `transaction_id | status | reason`.
