# Research Notes — context7 queries

Documented per `TASKS.md` Task 4: at least 2 context7 queries made while building Agent 2 (code
generation) and the custom MCP server / coverage gate.

## Query 1: FastMCP server — tools, resources, stdio transport

- Search: `resolve-library-id(libraryName="FastMCP", query="defining tools and resources in a
  FastMCP server, running the server over stdio")` → then
  `query-docs(query="defining tools with @mcp.tool and resources with @mcp.resource, running
  server with mcp.run() over stdio")`
- context7 library ID: `/prefecthq/fastmcp`
- Applied: Confirmed the exact decorator API used in `mcp/server.py` —
  `@mcp.tool` for `get_transaction_status` / `list_pipeline_results`, `@mcp.resource("pipeline://summary")`
  for the summary resource, and `mcp.run()` (no arguments) at the bottom of the file to default to
  stdio transport, which is what `mcp.json`'s `"command": "python", "args": ["mcp/server.py"]`
  entry expects (a client-managed subprocess talking over stdio, not an HTTP server).

## Query 2: Python `decimal` module for monetary arithmetic

- Search: `resolve-library-id(libraryName="Python", query="decimal module for precise monetary
  arithmetic and rounding")` → then `query-docs(query="decimal.Decimal parsing from string and
  ROUND_HALF_UP quantize for currency")`
- context7 library ID: `/python/cpython`
- Applied: Confirmed `Decimal` should always be constructed from a **string**
  (`Decimal("1500.00")`), never from a `float`, to avoid binary floating-point representation
  error — this is why every agent module parses `data["amount"]` as `Decimal(str(...))` and every
  JSON message keeps `amount` as a string on the wire, per `specification.md` § Implementation
  Notes. Also confirmed rounding-mode constants (`ROUND_HALF_UP` etc.) live on `decimal.Context`
  for any future settlement rounding needs.

## Query 3: pytest-cov coverage gate behavior

- Search: `resolve-library-id(libraryName="pytest-cov", query="fail-under coverage threshold and
  terminal report options")` → then `query-docs(query="--cov-fail-under threshold and exit code
  behavior")`
- context7 library ID: `/pytest-dev/pytest-cov`
- Applied: Confirmed `--cov-fail-under=N` makes `pytest` itself exit non-zero when total coverage
  is below `N` (printing `FAIL Required test coverage of N% not reached...`), so
  `.claude/hooks/check_coverage.sh` can simply run
  `pytest --cov=agents --cov=integrator --cov-fail-under=80` and check `pytest`'s own exit code
  rather than re-implementing coverage-percentage parsing itself.
