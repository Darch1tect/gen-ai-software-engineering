---
description: Run the multi-agent banking pipeline end-to-end and summarize the results
---

Run the multi-agent banking pipeline end-to-end.

Steps:
1. Check that `sample-transactions.json` exists in the project root; stop and report if it's
   missing.
2. Clear the `shared/` directories by removing any stale JSON files from
   `shared/{input,processing,output,results}/` (or simply let `integrator.py` do this — it clears
   `input`, `processing`, `output`, and prior `shared/results/*.json` on every run, but never
   truncates `shared/results/audit.log`).
3. Run the pipeline: `.venv/bin/python integrator.py` (or `python integrator.py` if the venv is
   already activated).
4. Read every `shared/results/*.json` file (excluding `summary.json`) and show a summary table:
   transaction ID, status, currency, amount, risk level (when present).
5. Report any transactions with `status: "rejected"`, including their `reason` field, separately
   from the settled ones.
6. Print the contents of `shared/results/summary.json` (counts by status, settled totals by
   currency) as the final line of the report.
