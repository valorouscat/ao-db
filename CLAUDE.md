# ao-db — Albion Online knowledge base
- Albion questions: follow the `albion` skill (factual lookup, or the grounded-answer protocol for strategy questions).
  Tools: MCP `mcp__albion__*` (server in `.mcp.json`) or `./ao` CLI.
- **Whenever gear is recommended or discussed, run `build_cost` and show the estimated cost.**
- **Answers must be current:** check `patchnotes` for the topic (newest note wins), state the patch the answer is valid for.
- Fresh checkout: `./setup.sh` (the SessionStart hook does it automatically when `ao.db` is missing).
- Code: `aodb/` — add a feature as a function returning markdown (`core.py` data, `market.py` prices, `advisor.py` analysis, `gearcheck.py` PvE camps, `pvp.py` PvP/PvPvE),
  then register it in `tools.py`; CLI and MCP are generated from that registry. After `build.py` changes: `python3 -m aodb.build`.
- `knowledge/*.md`: curated, sourced notes (written via `save_note`); `knowledge/patchnotes/`: official posts from Steam
  (`python3 -m aodb.patchnotes --update`); `knowledge/calibration.json`: real fight outcomes (`record_outcome`); commit all. `knowledge.db` is a generated index of all three (gitignored, auto-rebuilt when any source changes).
- Index layout change in `build.py` (tables, indexes, FTS) → bump `SCHEMA_VERSION` there; the SessionStart hook rebuilds stale ao.db.
- Tests: `python3 -m unittest discover tests` (needs ao.db; `AO_NET=1` for market).
