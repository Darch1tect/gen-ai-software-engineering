#!/usr/bin/env bash
# Single-command entry point for the 4-agent bug-fix pipeline.
#
# Usage: ./run-pipeline.sh [bug-id]
#   bug-id defaults to "001" (matches context/bugs/001/).
#
# Runs, in order, via headless `claude -p` calls, each with its own
# explicit --model and --allowedTools (loading the agent's persona from
# agents/*.agent.md as an appended system prompt, and its required skill(s)
# from skills/ as referenced inside that persona):
#
#   Bug Researcher -> Bug Research Verifier -> Bug Planner -> Bug Fixer
#   -> Security Verifier -> Unit Test Generator
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

BUG_ID="${1:-001}"
BUG_DIR="context/bugs/${BUG_ID}"
RESEARCH_DIR="${BUG_DIR}/research"

if [ ! -f "${BUG_DIR}/bug-context.md" ]; then
  echo "ERROR: ${BUG_DIR}/bug-context.md not found." >&2
  echo "Seed a bug first (see context/bugs/001 for an example)." >&2
  exit 1
fi

if ! command -v claude >/dev/null 2>&1; then
  echo "ERROR: 'claude' CLI not found on PATH. Install Claude Code first." >&2
  exit 1
fi

mkdir -p "${RESEARCH_DIR}"

run_agent() {
  local name="$1" agent_file="$2" model="$3" tools="$4" prompt="$5"
  echo ""
  echo "================================================================"
  echo " STAGE: ${name}   (model: ${model})"
  echo "================================================================"
  claude -p "${prompt}" \
    --append-system-prompt "$(cat "${agent_file}")" \
    --model "${model}" \
    --allowedTools "${tools}" \
    --permission-mode bypassPermissions \
    --output-format text
}

echo "############################################################"
echo "# 4-Agent Bug-Fix Pipeline — bug id: ${BUG_ID}"
echo "############################################################"

# 0. Bug Researcher (supporting — not one of the 4 graded agents)
run_agent "Bug Researcher" "agents/bug-researcher.agent.md" "sonnet" \
  "Read Grep Glob Write" \
  "Act as the bug-researcher agent for bug id ${BUG_ID}. Read ${BUG_DIR}/bug-context.md and investigate the source tree. Write your findings to ${RESEARCH_DIR}/codebase-research.md exactly per the output format defined in your system prompt."

# 1. Bug Research Verifier (REQUIRED — Task 1)
run_agent "Bug Research Verifier" "agents/research-verifier.agent.md" "opus" \
  "Read Grep Glob Write" \
  "Act as the research-verifier agent. Verify ${RESEARCH_DIR}/codebase-research.md (bug id ${BUG_ID}) against the real source tree, using the required skills/research-quality-measurement.md skill. Write ${RESEARCH_DIR}/verified-research.md exactly per the output format defined in your system prompt."

# 2. Bug Planner (supporting — not one of the 4 graded agents)
run_agent "Bug Planner" "agents/bug-planner.agent.md" "sonnet" \
  "Read Grep Glob Write" \
  "Act as the bug-planner agent. Read ${RESEARCH_DIR}/verified-research.md (bug id ${BUG_ID}) and produce ${BUG_DIR}/implementation-plan.md exactly per the output format defined in your system prompt. The project's test command is: python3 -m unittest discover -s tests -v"

# 3. Bug Fixer (REQUIRED — Task 2)
run_agent "Bug Fixer" "agents/bug-fixer.agent.md" "sonnet" \
  "Read Edit Write Grep Glob Bash" \
  "Act as the bug-fixer agent. Read ${BUG_DIR}/implementation-plan.md (bug id ${BUG_ID}) and apply every planned change to the real source tree, running the plan's test command after each change. Write ${BUG_DIR}/fix-summary.md exactly per the output format defined in your system prompt."

# 4. Security Verifier (REQUIRED — Task 3)
run_agent "Security Verifier" "agents/security-verifier.agent.md" "opus" \
  "Read Grep Glob Write" \
  "Act as the security-verifier agent. Read ${BUG_DIR}/fix-summary.md (bug id ${BUG_ID}) and review every changed file it lists for security issues. Write ${BUG_DIR}/security-report.md exactly per the output format defined in your system prompt. Do not modify any source file."

# 5. Unit Test Generator (REQUIRED — Task 4)
run_agent "Unit Test Generator" "agents/unit-test-generator.agent.md" "haiku" \
  "Read Write Edit Grep Glob Bash" \
  "Act as the unit-test-generator agent. Read ${BUG_DIR}/fix-summary.md (bug id ${BUG_ID}), apply the required skills/unit-tests-FIRST.md skill, and generate/update tests under tests/ for the changed code only. Run the full suite with: python3 -m unittest discover -s tests -v . Write ${BUG_DIR}/test-report.md exactly per the output format defined in your system prompt."

echo ""
echo "################################################################"
echo " PIPELINE COMPLETE — bug id: ${BUG_ID}"
echo "################################################################"
echo "Outputs:"
for f in \
  "${RESEARCH_DIR}/codebase-research.md" \
  "${RESEARCH_DIR}/verified-research.md" \
  "${BUG_DIR}/implementation-plan.md" \
  "${BUG_DIR}/fix-summary.md" \
  "${BUG_DIR}/security-report.md" \
  "${BUG_DIR}/test-report.md"
do
  if [ -f "$f" ]; then echo "  [ok]      $f"; else echo "  [MISSING] $f"; fi
done

echo ""
echo "Final test run:"
python3 -m unittest discover -s tests -v
