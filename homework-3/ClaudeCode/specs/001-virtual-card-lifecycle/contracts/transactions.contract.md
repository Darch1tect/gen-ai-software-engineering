# Contract: Transaction Visibility

**Status**: Hypothetical / illustrative only — no API is implemented in this phase. Describes
the operation-level contract for User Story 4 (FR-016–FR-018).

## `ListTransactions`

**Serves**: User Story 4 (FR-016, FR-017, FR-018)

- **Actor**: end-user (owning customer)
- **Preconditions**: card exists and belongs to the requesting customer
- **Input**: `card_id`, `cursor` (opaque, optional — omitted for first page), `page_size`
  (optional, default and max 50 per SC-005)
- **Output (rejected — rate limit)**: `RATE_LIMIT_EXCEEDED` if the caller exceeds this
  operation's per-action-type rate limit (FR-031, edge case E15) or the aggregate
  cross-action-type limit (FR-032, edge case E18); logged (FR-029), not audited since no state
  changed.
- **Output (rejected — dependency unavailable)**: `DEPENDENCY_UNAVAILABLE` if a required
  external dependency times out, is unreachable, or fails an integrity check (FR-033
  availability, FR-034 integrity; edge cases E16, E17); fail-closed, no partial state
  committed, logged (FR-029). This is a read operation, so `STEP_UP_REQUIRED` never applies.
- **Output (success, has data)**: `{transactions: [Transaction{transaction_id, amount,
  currency, status, decline_reason?, masked_merchant, occurred_at}], next_cursor?}`, ordered
  reverse-chronological (acceptance scenario 1)
- **Output (success, empty)**: `{transactions: [], next_cursor: null}` — an explicit empty
  result, never an error or null response (FR-017, E6)
- **Pagination stability (FR-018)**: `cursor` anchors to a stable position (timestamp + ID), so
  a new transaction arriving between page requests does not shift or duplicate items on
  subsequent pages (research.md #8)
- **Recency labeling (E7)**: a transaction visible within the time-to-consistency window
  (SC-004, ≤10s p95) may show `status=Pending` before settling; this is expected and MUST be
  labeled as such in the response, not hidden
- **Acceptance criteria / Definition of Done**:
  - [ ] Empty-state and error are never conflated — a card with zero transactions returns an
        empty list, not a 404/error
  - [ ] Requesting a second page never returns an item already seen on the first page, even if
        new transactions were inserted in between
  - [ ] Every page response is ≤ 50 items and completes within 2s p95 (SC-005)
  - [ ] No response field ever contains raw/unmasked merchant payment-network payload data
