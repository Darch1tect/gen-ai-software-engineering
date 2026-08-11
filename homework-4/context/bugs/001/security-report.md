# Security Report: 001

## Scope

Sourced from `context/bugs/001/fix-summary.md`, which lists three changes,
all in a single file:

| Change | Location per fix-summary | Function |
|---|---|---|
| 1 | `src/expense_tracker.py:55-59` | `calculate_total` |
| 2 | `src/expense_tracker.py:75-79` | `apply_member_discount` |
| 3 | `src/expense_tracker.py:86-91` | `search_expenses` |

**Reviewed**: `src/expense_tracker.py` in full (137 lines), not just the
diff — a tainted value can originate outside the changed lines. Post-fix
line numbers shifted slightly from those recorded in `fix-summary.md`
(the file now has `calculate_total` at 55-60, `apply_member_discount` at
71-75, `search_expenses` at 78-84); this report cites **post-fix** line
numbers.

`tests/test_expense_tracker.py` was read for intent only (to establish what
the security test actually asserts). It is not a changed file and was not
audited as a sink.

**Dependencies**: no manifest exists (`requirements*.txt`, `pyproject.toml`,
`setup.py`, `Pipfile` all absent). Imports are stdlib only — `argparse`,
`sqlite3`, `sys`, `pathlib` (lines 13-16). No dependency was added by this
fix, so there is no unsafe-dependency / CVE surface to assess.

**Web surface**: none. This is a local `argparse` CLI with no HTTP handler,
no template rendering, and no HTML output sink (`_print_rows` writes to
stdout via f-string, line 92). XSS and CSRF are therefore **not applicable**
and were excluded on that basis rather than overlooked.

## Findings

### Finding 1 — LOW — LIKE wildcard injection survives the SQLi fix

**File**: `src/expense_tracker.py:80-83` (`search_expenses`, Change 3)
**CWE**: CWE-943 (Improper Neutralization of Special Elements in Data Query
Logic), residual to the CWE-89 fix.

**Description**: Change 3 correctly eliminated the SQL injection — the
keyword is now bound as a parameter and can no longer alter query structure.
However, the keyword is still concatenated into the *LIKE pattern*
(`f"%{keyword}%"`) with no escaping of LIKE's metacharacters `%` and `_`.
A keyword consisting of a bare `%` or `_` is a valid pattern that matches
every row, which reproduces the exact information-disclosure outcome the
fix's regression test was written to prevent — just through pattern
semantics instead of SQL syntax.

**Evidence**:
```python
cursor = conn.execute(
    "SELECT id, description, amount, category FROM expenses WHERE description LIKE ?",
    (f"%{keyword}%",),          # keyword's % and _ are unescaped wildcards
)
```

Confirmed by direct execution against an in-memory DB seeded with a
`Secret gift` row:
```
quote payload  ("nonexistent' OR '1'='1' --")  -> []                    # fix holds
percent payload ("%")                          -> ALL rows returned
underscore payload ("_")                       -> ALL rows returned
```

The regression test at `tests/test_expense_tracker.py:56-61` asserts only
the quote payload, so it passes while this path remains open.

**Impact**: Low. The application is a single-user local CLI: every row in
`expenses.db` already belongs to the operator, and `list` (line 51) returns
all rows unconditionally anyway, so no privilege or tenancy boundary is
crossed today. This matters as a latent defect — if `search_expenses` is
ever reused behind a multi-user or network-facing caller, it becomes an
authorization bypass. It also means the security test overstates the
guarantee it appears to provide.

**Remediation**: Escape the wildcards and declare the escape character:
```python
def search_expenses(conn: sqlite3.Connection, keyword: str):
    """Search expenses whose description contains the given keyword."""
    escaped = keyword.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    cursor = conn.execute(
        "SELECT id, description, amount, category FROM expenses "
        "WHERE description LIKE ? ESCAPE '\\'",
        (f"%{escaped}%",),
    )
    return cursor.fetchall()
```
Escape the backslash *first*, or the escape character itself becomes
injectable. Add a test asserting `search_expenses(conn, "%") == []` when no
description literally contains `%`.

---

### Finding 2 — LOW — `expenses.db` created with world-readable permissions

**File**: `src/expense_tracker.py:22` (`get_connection`), reached by every
command path via line 117.
**CWE**: CWE-732 (Incorrect Permission Assignment for Critical Resource).

**Description**: `sqlite3.connect()` creates the database file using the
process umask with no explicit hardening. Under the umask observed in this
environment (`022`), `expenses.db` is created mode `0644` — readable by
every local account on the machine. The file holds personal financial
records (descriptions, amounts, categories).

**Evidence**:
```python
def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)   # no mode restriction applied
    init_db(conn)
    return conn
```
`DB_PATH` is a fixed repo-root path (line 18) and is **not** attacker
-controlled, so there is no path-traversal component to this.

**Impact**: Low, and defense-in-depth rather than an active vulnerability —
exploitation requires an existing local account on the same host. On a
single-user workstation the practical exposure is negligible; on a shared
or multi-tenant host it is a straightforward read of another user's
financial data.

**Remediation**: Restrict the file to the owner immediately after creation:
```python
import os, stat

def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    try:
        os.chmod(db_path, stat.S_IRUSR | stat.S_IWUSR)  # 0600
    except OSError:
        pass  # e.g. ":memory:" or a read-only mount
    init_db(conn)
    return conn
```
Note the repo already gitignores `expenses.db` (`.gitignore:3`), so there
is no committed-data exposure — this is strictly about on-disk permissions.

---

### Finding 3 — LOW — Unvalidated non-finite `amount` permanently poisons totals

**File**: `src/expense_tracker.py:110` (argparse `type=float`) flowing into
`add_expense` (41-47) and summed by the changed `calculate_total` (55-60).
**CWE**: CWE-20 (Improper Input Validation).

**Description**: `p_add.add_argument("amount", type=float)` accepts the
strings `inf`, `-inf`, and `infinity`, since Python's `float()` parses them.
The value is stored as a SQLite REAL and then summed by `calculate_total`,
the function modified in Change 1. Once an infinite row exists in a
category, that category's total is `inf` forever and cannot be corrected by
adding offsetting rows — there is no delete command in the CLI, so the only
recovery is deleting the database.

**Evidence** (executed against an in-memory DB):
```
add 'ok'     10.0        -> total = 10.0
add 'poison' float(inf)  -> total = inf
add 'neg'    -999999.0   -> total = inf     # unrecoverable
```
`float("nan")` is *not* exploitable here: Python's sqlite3 driver binds NaN
in a way that trips the `amount REAL NOT NULL` constraint (line 33), raising
`sqlite3.IntegrityError`. Only the infinite values get through.

**Impact**: Low. This is a local CLI where the only party supplying input is
the operator, so it is largely self-inflicted — a data-integrity and
availability defect rather than a confidentiality one. It is listed because
it reaches the code changed in Change 1 and would become a persistent
denial-of-service on the `total` feature if this module were ever driven by
untrusted input (an import path, an API wrapper).

**Remediation**: Reject non-finite and negative amounts at the parser
boundary:
```python
import math

def _amount(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or parsed < 0:
        raise argparse.ArgumentTypeError("amount must be a finite, non-negative number")
    return parsed

p_add.add_argument("amount", type=_amount)
```
Also apply `_amount` to the `discount` subcommand's `total` argument
(line 110), which has the same permissiveness.

---

### Finding 4 — INFO — Change 3 verified as a correct CWE-89 remediation

**File**: `src/expense_tracker.py:80-83` (`search_expenses`)

Recorded for traceability, not as an open issue. The pre-fix code
concatenated `keyword` directly into the query string, allowing
`%' OR '1'='1` to return every row. The replacement uses a bound parameter,
so the keyword can no longer influence query structure — verified by
executing the documented payload `nonexistent' OR '1'='1' --` against a
seeded database, which returns `[]`. The original CWE-89 finding is
**closed**. See Finding 1 for the residual pattern-level issue.

---

### Explicitly considered, no issue found

Per-category conclusions for the one changed file:

- **Injection (SQL/command/LDAP/template)**: every other query in the file
  is either a static string (`init_db` 28-37, `list_expenses` 51) or
  correctly parameterized (`add_expense` 42-45, `total_for_category` 64-66,
  `search_expenses` 80-83). No `os.system`, `subprocess`, `eval`, `exec`,
  or template rendering anywhere in the module. No command, LDAP, or
  template injection surface exists.
- **Hardcoded secrets**: none. The module contains no API keys, passwords,
  tokens, or connection strings. `DB_PATH` (line 18) is a derived local
  filesystem path, not a credentialed DSN.
- **Insecure comparisons**: no secret, token, HMAC, or password comparison
  occurs anywhere in the file. The only boolean check is
  `if is_member:` (line 73), which tests a CLI-supplied flag constrained to
  `choices=[0, 1]` (line 111) — not a secret, so constant-time comparison is
  not warranted.
- **Missing validation**: `description` and `category` are untrusted but
  reach only parameterized binds, so no sink is exposed; length is
  unbounded but bounded in practice by the OS argv limit, which is not a
  meaningful DoS vector for a local CLI. The one genuine gap is the numeric
  `amount`, reported as Finding 3.
- **Unsafe dependencies**: not applicable — stdlib-only, no manifest, no
  package added by this fix.
- **XSS/CSRF**: not applicable — no web surface, as established in Scope.

Non-security observations noted but out of scope for this report: `conn` is
closed on line 131 without a `try`/`finally`, so it leaks on an exception
path (resource hygiene, not a vulnerability), and `calculate_total` could be
expressed as a `sum()` comprehension (style).

## Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 3 |
| INFO | 1 |

**Verdict: no blocking issues — the fix is safe to release.**

The security-relevant change in this batch (Change 3) is a correct fix: the
CWE-89 SQL injection is genuinely closed, and Changes 1 and 2 are pure
arithmetic corrections that introduce no new security surface. **No
vulnerability was introduced by this fix.**

All three LOW findings are pre-existing weaknesses in the touched file, none
individually exploitable in the current single-user local-CLI threat model.
Finding 1 is the one worth acting on soon: not because it is dangerous
today, but because the regression test accompanying this fix implies a
stronger guarantee ("search does not leak all rows") than the code actually
provides, and that gap will be invisible to whoever next reuses
`search_expenses` in a context where row-level access does matter.

Per this role's constraints, no source file was modified — all remediations
above are proposals for the Fixer or a follow-up bug.

## References

Every line reviewed in `src/expense_tracker.py`, with outcome:

| Lines | Element | Outcome |
|---|---|---|
| 1-12 | Module docstring | No issue |
| 13-16 | Imports (stdlib only) | No issue — no dependency risk |
| 18 | `DB_PATH` constant | No issue — fixed path, not user-controlled |
| 21-24 | `get_connection` | **Finding 2** (LOW, file permissions) |
| 27-38 | `init_db` | No issue — static DDL |
| 41-47 | `add_expense` | No issue — parameterized; but see Finding 3 for the `amount` value reaching it |
| 50-52 | `list_expenses` | No issue — static query |
| **55-60** | **`calculate_total` (Change 1)** | No injection/secret issue; **Finding 3** reaches this sum |
| 63-68 | `total_for_category` | No issue — parameterized on `category` |
| **71-75** | **`apply_member_discount` (Change 2)** | No issue — pure arithmetic, no untrusted sink |
| **78-84** | **`search_expenses` (Change 3)** | **Finding 1** (LOW, LIKE wildcards); **Finding 4** (INFO, CWE-89 closed) |
| 87-92 | `_print_rows` | No issue — stdout only, no HTML sink |
| 95-116 | `main` argparse setup | **Finding 3** (LOW, `amount`/`total` accept non-finite) |
| 117-132 | `main` dispatch + teardown | No security issue (unclosed-on-exception noted as non-security) |
| 135-136 | Entry point | No issue |

Supporting files consulted (not audited as changed code):
- `context/bugs/001/fix-summary.md` — scope definition, all 3 changes.
- `tests/test_expense_tracker.py:56-61` — injection test intent, cited in
  Finding 1.
- `.gitignore:3` — confirms `expenses.db` is not committed, cited in
  Finding 2.
