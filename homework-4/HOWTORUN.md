# How to Run

## Prerequisites

- Python 3.9+ (stdlib only — no `pip install` required for the app or its
  tests).
- [Claude Code CLI](https://claude.com/claude-code) (`claude`) authenticated,
  for running the agent pipeline.

## 1. Run the sample application

```bash
# from repo root
python3 src/expense_tracker.py add "Coffee" 3.5 food
python3 src/expense_tracker.py add "Lunch" 12.0 food
python3 src/expense_tracker.py total food
python3 src/expense_tracker.py discount 100 1
python3 src/expense_tracker.py search Coff
```

This creates a local `expenses.db` SQLite file in the repo root (git-ignored).

## 2. Run the test suite

```bash
python3 -m unittest discover -s tests -v
```

Before the pipeline runs, 4 tests fail on purpose (they encode the correct
behavior for the 2 seeded functional bugs and the seeded SQL-injection
issue — see `context/bugs/001/bug-context.md`). After the pipeline runs
(step 3), all tests pass.

## 3. Run the full 4-agent pipeline (single command)

```bash
./run-pipeline.sh          # uses bug id "001" by default
./run-pipeline.sh 001      # equivalent, explicit bug id
```

This one command runs, in order, with no manual steps in between:

1. **Bug Researcher** (supporting) → `context/bugs/001/research/codebase-research.md`
2. **Bug Research Verifier** *(required agent)* → `context/bugs/001/research/verified-research.md`
3. **Bug Planner** (supporting) → `context/bugs/001/implementation-plan.md`
4. **Bug Fixer** *(required agent)* → applies the fix to `src/expense_tracker.py`, writes `context/bugs/001/fix-summary.md`
5. **Security Verifier** *(required agent)* → `context/bugs/001/security-report.md`
6. **Unit Test Generator** *(required agent)* → new tests under `tests/`, writes `context/bugs/001/test-report.md`

Each stage is a headless `claude -p` call with an explicit `--model` and a
restricted `--allowedTools` list, using the matching `agents/*.agent.md` file
as its system prompt (which in turn references the required skill under
`skills/` where applicable). See `run-pipeline.sh` for the exact flags.

The script exits non-zero and prints an error if `context/bugs/<id>/bug-context.md`
does not exist, or if the `claude` CLI is not on `PATH`.

## 4. Verify the result

```bash
python3 -m unittest discover -s tests -v   # should now be all-pass
python3 src/expense_tracker.py total food  # should now be 15.50, not 12.00
python3 src/expense_tracker.py discount 100 1   # should now be 90.00, not 110.00
```

Read `context/bugs/001/fix-summary.md`, `security-report.md`, and
`test-report.md` for the full agent-generated record of what changed, what
was found, and what was tested.
