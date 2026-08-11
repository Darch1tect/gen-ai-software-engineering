---
name: research-quality-measurement
description: Defines how to score and label the quality of bug-research output (codebase-research.md) during verification. Use this whenever assessing or reporting research quality, e.g. in verified-research.md.
---

# Research Quality Measurement

A rubric for scoring `research/codebase-research.md` during verification. The
**Bug Research Verifier** agent must use this skill when writing the
`Research Quality Assessment` section of `verified-research.md`. It converts
subjective "does this research look right?" judgement into a repeatable,
auditable score.

## Dimensions

Score each dimension `0–3` against the evidence gathered while verifying the
research (see the verifier agent for the verification procedure):

| Dimension | 0 (absent) | 1 (weak) | 2 (adequate) | 3 (strong) |
|---|---|---|---|---|
| **Reference accuracy** | Cited file:line locations don't exist or don't match | Some file:line refs wrong or stale | All refs resolve; minor line drift (±3 lines) | Every file:line ref resolves exactly and the quoted snippet matches source verbatim |
| **Root cause identification** | No causal explanation, only symptoms | Cause is guessed, not tied to code | Cause is tied to code but missing an edge case or contributing factor | Root cause is precise, code-backed, and explains the observed symptom fully |
| **Completeness** | Only one of the reported issues is covered | Some issues covered, others missing detail | All reported issues covered with cause + location | All reported issues covered, plus related risk areas (callers, similar patterns elsewhere) |
| **Actionability** | A fixer could not act on this without re-investigating | Fix direction implied but not concrete | Enough detail to write a fix for most issues | Enough detail to write a fix for every issue without further investigation |

**Total score**: sum of the four dimensions, range `0–12`.

## Quality Levels

| Total score | Level | Meaning |
|---|---|---|
| 11–12 | **EXCELLENT** | Research is fully verified, precise, and directly actionable. Bug Planner can proceed with no caveats. |
| 8–10 | **GOOD** | Research is solid with only minor gaps (e.g. small line drift, one missing edge case). Bug Planner can proceed; note gaps as caveats. |
| 5–7 | **ADEQUATE** | Research captures the right area but has real gaps (wrong root cause on one issue, missing detail). Bug Planner should re-check flagged discrepancies before planning. |
| 0–4 | **POOR** | Research contains broken references, unverifiable claims, or wrong root causes for one or more issues. Must be sent back to Bug Researcher before planning continues. |

## Pass/Fail Gate

- **PASS**: every cited file:line reference verified AND total score ≥ 8 (GOOD or EXCELLENT).
- **FAIL**: any reference could not be verified, OR total score ≤ 7 (ADEQUATE or POOR).

A `FAIL` does not block the pipeline from producing `verified-research.md`,
but the verifier must state `PASS`/`FAIL` explicitly in the Verification
Summary and list every discrepancy, so Bug Planner (or a human) can decide
whether to proceed.

## Required Reporting Format

When writing `Research Quality Assessment` in `verified-research.md`,
report:

```
**Score**: <dimension scores, e.g. Reference accuracy 3/3, Root cause 3/3,
Completeness 2/3, Actionability 3/3 — Total 11/12>
**Level**: <EXCELLENT | GOOD | ADEQUATE | POOR>
**Reasoning**: <1–3 sentences per dimension tying the score to concrete
evidence from the verification pass — cite what was checked, not just the
number>
```
