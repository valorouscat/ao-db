# ao-db — Albion Online knowledge base
- Albion questions: use the `albion` skill → MCP tools `mcp__albion__*` (server in `.mcp.json`) or `./ao` CLI.
- Fresh checkout: `./setup.sh` (the SessionStart hook does it automatically when `ao.db` is missing).
- Code: `aodb/` — add a feature as a function in `core.py`/`market.py` returning markdown, then register it in `tools.py`
  (CLI and MCP are generated from that registry). Rebuild DB after `build.py` changes: `python3 -m aodb.build`.
- Tests: `python3 -m unittest discover tests` (needs ao.db; `AO_NET=1` for market).
