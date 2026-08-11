# Homework 5: Configure MCP Servers

**Author:** Vitalii Roditieliev

## Overview

This homework configures four MCP (Model Context Protocol) servers for use with Claude Code and demonstrates a working interaction with each one:

1. **GitHub MCP** — official remote GitHub MCP server (`https://api.githubcopilot.com/mcp/`), authenticated with a Personal Access Token. Used to list real pull requests on this repository.
2. **Filesystem MCP** — official `@modelcontextprotocol/server-filesystem`, scoped to the `homework-5/` project directory. Used to list files and read `TASKS.md`.
3. **Jira MCP** — Atlassian's official remote MCP server (`https://mcp.atlassian.com/v1/mcp/authv2`), authenticated via OAuth 2.1. Used to fetch the last 5 bug tickets from a real Jira project (ticket keys/status only — no sensitive content).
4. **Custom MCP server (FastMCP)** — a self-built server in [`custom-mcp-server/`](custom-mcp-server/) that exposes a lorem-ipsum text resource and a `read` tool.

All four servers are registered in [`.mcp.json`](.mcp.json).

## Custom MCP Server: Resources vs. Tools

- **Resources** are URIs Claude can read from, similar to files or API endpoints — they represent data. This project exposes `lorem://ipsum` (default 30 words) and the templated `lorem://ipsum/{word_count}`.
- **Tools** are actions Claude can call to perform an operation. This project exposes a `read` tool that takes an optional `word_count` parameter (default `30`) and returns that many words from `lorem-ipsum.md`.

See [`HOWTORUN.md`](HOWTORUN.md) for install, run, connect, and test instructions, and [`custom-mcp-server/`](custom-mcp-server/) for the implementation.

## Deliverables

| Deliverable | Location |
|---|---|
| MCP configuration | [`.mcp.json`](.mcp.json) |
| Custom MCP server | [`custom-mcp-server/server.py`](custom-mcp-server/server.py) |
| Dependencies | [`custom-mcp-server/requirements.txt`](custom-mcp-server/requirements.txt) (includes `fastmcp`) |
| Lorem ipsum source | [`custom-mcp-server/lorem-ipsum.md`](custom-mcp-server/lorem-ipsum.md) |
| Screenshots | [`docs/screenshots/`](docs/screenshots/) |
| How-to-run guide | [`HOWTORUN.md`](HOWTORUN.md) |

## Notes on Task 3 (Jira)

The task originally called for Jira **or** Notion. Notion's remote MCP server was set up first, but the only meaningful "pages" available in that workspace were personal 1:1 tracking notes containing coworkers' salary/health details — unsuitable to capture in a screenshot for this submission. The task was completed with **Jira** instead (Atlassian's official remote MCP server), querying a real project's bug tickets and keeping the captured response to ticket keys and status only, per the task's privacy guidance.
