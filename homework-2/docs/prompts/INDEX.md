# Documentation generation plan

Five documents, five audiences, model matched to how much synthesis each doc
requires. Each prompt file below is **self-contained**: open a Claude Code
session with the recommended model in the repo root and paste the prompt
(or pipe it in).

| # | Output file | Audience | Model | Model ID | Prompt |
|---|-------------|----------|-------|----------|--------|
| 1 | `README.md` (repo root) | Developers | Fable 5 (alt: Opus 4.8) | `claude-fable-5` | [01_README.md](01_README.md) |
| 2 | `docs/API_REFERENCE.md` | API Consumers | Sonnet 5 | `claude-sonnet-5` | [02_API_REFERENCE.md](02_API_REFERENCE.md) |
| 3 | `docs/ARCHITECTURE.md` | Technical Leads | Fable 5 (alt: Opus 4.8) | `claude-fable-5` | [03_ARCHITECTURE.md](03_ARCHITECTURE.md) |
| 4 | `docs/TESTING_GUIDE.md` | QA Engineers | Sonnet 5 | `claude-sonnet-5` | [04_TESTING_GUIDE.md](04_TESTING_GUIDE.md) |
| 5 | `docs/GENERAL_GUIDE.md` | General audience | Haiku 4.5 | `claude-haiku-4-5-20251001` | [05_GENERAL_GUIDE.md](05_GENERAL_GUIDE.md) |

## How to run

```bash
# interactive: start with the right model, then paste the prompt
claude --model claude-sonnet-5

# or one-shot:
claude --model claude-sonnet-5 -p "$(cat docs/prompts/02_API_REFERENCE.md)"
```

Recommended order: 2 → 4 → 1 → 3 → 5. The API reference and testing guide
are pure extraction; README and ARCHITECTURE build on verified facts; the
general guide is written last from the finished picture.

## Ground rules baked into every prompt

- The **code is the source of truth** — each prompt lists the files to read
  first and forbids inventing endpoints, fields, or behavior.
- Every prompt ends with a **verification checklist** (commands to run,
  facts to cross-check) before the document is written.
- Documents are written in English, except `GENERAL_GUIDE.md` (Ukrainian).
- Mermaid diagrams must be valid; keep them small enough to render on GitHub.
