---
name: albion
description: Answer any Albion Online question (items, stats, recipes, crafting costs and profit, spells/abilities, mobs, loot/drops, zones, in-game text, market prices) using the ao-db knowledge base. Use whenever the user asks about Albion Online.
---

# Albion Online knowledge base (ao-db)

Prefer the MCP tools `mcp__albion__*`. If they aren't loaded, use the identical CLI `./ao <tool> ...` from the repo root
(`./ao <tool> -h`). If the DB is missing: `./setup.sh`.

## Workflow
1. Vague question or unknown term → `search` (any game language).
2. Entity → `item` / `spell` / `mob` / `zone` / `variants`; relations → `recipe`, `usedin`, `drops`, `loot`.
3. Economy → `price`, `history`, `best_city`, `craft_profit` (live, crowd-sourced; mention data age).
4. Anything else → `files` → `doc <file> <key>`; aggregate questions → `sql` (`schema` first; `json_extract(json,'$."@attr"')`).
5. Answer in the user's language, cite item IDs, show icons as markdown images:
   `https://render.albiononline.com/v1/item/<ID>.png?size=64`, spells `https://render.albiononline.com/v1/spell/<ID>.png`.
   Visual comparison → `html` tool, then send the file.

## Facts to keep straight
- Item IDs: `T<tier>_<NAME>[@<enchant>]`; enchanted resources are `T5_ORE_LEVEL2@2`. Tier prefixes in queries work: `8.3 claymore`.
- Spell numbers are base values before item-power scaling; loot `chance` values are weights.
- Return-rate presets: royal city 15.2% / 43.5% with focus; bonus-city category 24.8% / 47.9%.
- Market taxes: 4% premium / 8% without premium, plus 2.5% setup fee.
