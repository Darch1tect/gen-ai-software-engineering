# HOWTORUN

Instructions to install, run, connect, and test the MCP servers configured for this homework.

## 1. Prerequisites

- [Claude Code CLI](https://code.claude.com/docs/en/mcp) installed and logged in (`claude --version`)
- [`uv`](https://docs.astral.sh/uv/) (Python package/venv manager) — used to run the custom FastMCP server
- [`gh`](https://cli.github.com/) CLI, authenticated (`gh auth status`) — used as the GitHub PAT source
- Node.js / `npx` available — used to run the Filesystem MCP server
- Access to an Atlassian/Jira Cloud site (for the Jira MCP server)

## 2. MCP configuration overview

All four servers are declared in [`.mcp.json`](.mcp.json) at the project root:

| Server | Type | Auth |
|---|---|---|
| `github` | remote HTTP (`api.githubcopilot.com/mcp`) | PAT via `Authorization` header, env var `GITHUB_PERSONAL_ACCESS_TOKEN` |
| `filesystem` | local stdio (`npx @modelcontextprotocol/server-filesystem`) | none — scoped to this project directory |
| `atlassian` | remote HTTP (`mcp.atlassian.com/v1/mcp/authv2`) | OAuth 2.1 (browser login on first use) |
| `lorem-ipsum` | local stdio (custom FastMCP server) | none |

Claude Code treats project-scoped `.mcp.json` servers as untrusted until approved interactively. The first time you run `claude` in this directory after this config exists (or changes), it will prompt you to approve each server — approve them.

### GitHub MCP: environment variable

GitHub's remote MCP endpoint does not support Claude Code's OAuth dynamic client registration, so it's configured with a PAT header instead. Before launching `claude`, export the token **in the same shell**:

```bash
export GITHUB_PERSONAL_ACCESS_TOKEN=$(gh auth token)
```

(Any PAT with `repo` scope works — reusing your `gh` CLI login avoids creating a separate token.)

### Atlassian/Jira MCP: OAuth

No token needed. On first connection, Claude Code opens a browser window for Atlassian login — sign in and grant access to your Jira site.

### Verifying connections

```bash
claude mcp list
```

Each server should show `✔ Connected` (or `⏸ Pending approval` until you run `claude` interactively once).

## 3. Custom MCP server (FastMCP)

Located in [`custom-mcp-server/`](custom-mcp-server/):

```
custom-mcp-server/
├── server.py          # FastMCP server: resource + `read` tool
├── lorem-ipsum.md      # source text
└── requirements.txt    # includes fastmcp
```

### Install dependencies

```bash
cd custom-mcp-server
uv venv --python 3.12
uv pip install -r requirements.txt
```

`requirements.txt` pins `fastmcp>=2.0` — confirm it's present:

```bash
cat requirements.txt   # fastmcp>=2.0
.venv/bin/pip show fastmcp
```

### Run the server standalone

```bash
.venv/bin/python server.py
```

This starts the server over stdio and blocks, waiting for an MCP client to connect (Ctrl+C to stop). To sanity-check the server starts cleanly without wiring up a full client, you can also run:

```bash
.venv/bin/fastmcp inspect server.py
```

### Connect MCP configuration

The server is already registered in [`.mcp.json`](.mcp.json) as `lorem-ipsum`, pointing at the venv's Python interpreter and `server.py` directly (absolute paths — adjust if you cloned this repo elsewhere):

```json
"lorem-ipsum": {
  "type": "stdio",
  "command": "/absolute/path/to/custom-mcp-server/.venv/bin/python",
  "args": ["/absolute/path/to/custom-mcp-server/server.py"],
  "env": {}
}
```

If you move the project, update these two paths (or re-run the command below from the project root, which rewrites them for your machine):

```bash
claude mcp add lorem-ipsum --scope project -- \
  "$(pwd)/custom-mcp-server/.venv/bin/python" \
  "$(pwd)/custom-mcp-server/server.py"
```

### Use / test the `read` tool

With `claude` running in this directory (server approved, per section 2), prompt it directly, e.g.:

> Use the read tool from the lorem-ipsum MCP server to get the first 12 words, then again with the default word count.

Expected behavior: Claude calls the `read` tool (visible as "Called lorem-ipsum…" in the transcript) and returns exactly 12 words for the first call and exactly 30 words (the default) for the second.

You can also test the resource and tool directly without Claude, via FastMCP's in-process client:

```bash
cd custom-mcp-server
.venv/bin/python -c "
import asyncio
from fastmcp import Client
import server

async def main():
    async with Client(server.mcp) as client:
        print(await client.list_tools())
        print(await client.call_tool('read', {'word_count': 8}))
        print(await client.read_resource('lorem://ipsum/12'))

asyncio.run(main())
"
```

## 4. Screenshots

Captured MCP call results for all four servers are in [`docs/screenshots/`](docs/screenshots/):

- `github-mcp-result.png`
- `filesystem-mcp-result.png`
- `jira-or-notion-mcp-result.png`
- `custom-mcp-read-tool-result.png`
