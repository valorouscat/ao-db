---
name: albion
description: Answer any Albion Online question — factual (items, stats, recipes, spells, mobs, loot, zones, prices) or strategic ("best gear for corrupted dungeons", "which Avalon chests to skip", "is this craft profitable") — with evidence from the ao-db knowledge base, the official killboard, live market data and open web sources, and always with an estimated gear cost. Use whenever the user asks about Albion Online.
---

# Albion Online advisor (ao-db)

Tools: MCP `mcp__albion__*` (preferred) or the identical CLI `./ao <tool>` from the repo root (`./ao <tool> -h`).
Missing DB → `./setup.sh`. Open web: your own WebSearch / WebFetch (wiki.albiononline.com, forum and reddit block
scripts behind Cloudflare; search result snippets and other guide sites usually work).

## 0. Freshness rules (always)
- Know "now": `latest_patches` (or `info`) → current patch and last major update. Game data stats come from the dump
  (`info` shows its date); balance changes after that date exist only in patch notes.
- Before stating any number, mechanic or recommendation, check `patchnotes <topic>` — results are newest first; the newest
  note is in force. Item and spell cards include "Recent patch changes": read them, mention relevant ones.
- Web sources: put the current year or patch name in queries; treat anything published before the last major update as
  outdated unless a patch note confirms it is unchanged. Say the date of each source.
- `notes` flags notes written before the last major update (⚠): re-verify with `patchnotes` and refresh via `save_note`.
- Session start updates dumps and patch notes automatically; mid-session use `update_patchnotes` if a new patch dropped.

## A. Factual questions
`search` → entity tool (`item`, `spell`, `mob`, `zone`, `variants`, `recipe`, `usedin`, `drops`, `loot`) → `doc` / `sql` for details.

## B. General / strategy questions (grounded answer protocol)
1. **Frame it.** Pin down content type, zone (lethal or not), tier/IP target, solo/group, server, budget. If unstated,
   pick sensible defaults and say so (e.g. europe server, T8-equivalent 1200+ IP for Slayer corrupted dungeons).
2. **Collect evidence — at least three independent kinds:**
   - Game rules: `mechanics <topic>` (official texts: IP requirements, rules, rewards), `doc` on the topic's data file.
   - Game numbers: `difficulty <content>` (loot/silver/fame multipliers, mob buffs, IP requirements per level and zone),
     `chest_value` (loot value ranking), `mob` (HP/damage of the content's mobs), `spell`, `item` stats.
   - Real usage: `meta_builds` (killboard: K/D and what players of a weapon wear). It's PvP data, so say so for PvE questions.
   - Official changes: `patchnotes <topic>` (and `since=<date of a source>` to see what changed after it).
   - Community knowledge: `notes <query>` first, then WebSearch (2+ sources, prefer the current patch and year,
     check dates; patch notes beat guides). Mark anything older than the latest major update as possibly outdated.
   - Player's own gear (loadout JSON pasted from the game): `gear_check` → IP, kit, camp strength per tier/stage, verdict, re-gear cost.
     Ask for in-game IP incl. mastery: per slot → `slot_ip` (or `weapon_ip`), character average → `avg_ip` (unspecified slots share
     the difference equally). Present the verdict as a model estimate.
   - Small groups (2-3 loadouts): `group_check` → roles, combined power, verdict per camp tier/stage, composition gaps,
     loot per player, total re-gear risk. Ask for each player's in-game IP (`ips`, players separated by '|').
3. **Cost every recommended setup — mandatory whenever gear comes up.** Call `build_cost` with the full set
   (weapon, offhand, head, armor, shoes, cape, food, potions; mount if relevant). Report the total, the .0–.3
   comparison and IP vs the content requirement. For several options, cost each one. Full-loot zones: this is the re-gear cost.
   Market API rate limited? Say so, give the item list, and use `history` or `price` later.
4. **Answer format:**
   - **Recommendation** (concrete item IDs, with icons `![](https://render.albiononline.com/v1/item/<ID>.png?size=48)`)
   - **Why**: evidence bullets, each with its source (tool + ID, killboard numbers, or a link)
   - **Cost** table from `build_cost` (+ cheaper/expensive variants)
   - **As of**: current patch name/date the answer is valid for
   - **Caveats**: model assumptions (loot `chance` interpretation, spell numbers before IP scaling), data age, patch risk
   - **Sources**: links used
5. **Learn.** Save a verified, non-obvious finding with `save_note` (title, body, sources). Never save a note without sources.

## Facts to keep straight
- Item IDs `T<tier>_<NAME>[@<enchant>]`; enchanted resources `T5_ORE_LEVEL2@2`; queries accept `8.3 claymore`, `палаш`.
- Quality adds IP: good +20, outstanding +40, excellent +60, masterpiece +100.
- Return rate: royal city 15.2% / 43.5% with focus; bonus city 24.8% / 47.9%. Market tax 4% premium / 8% otherwise + 2.5% setup fee.
- Corrupted dungeons: Hunter = blue/yellow, no item loss; Stalker = red/black, full loot; Slayer = red/black, Might, full loot.
  Entry uses **base** IP: 700 / 900 / 1100 (Abyssal Depths, 2025-06-30; game data agrees). The in-game tutorial text still says
  800/900/1200 — it is outdated. Since then loot no longer scales with Infamy; Infamy fame scaling max 20%.
- In-game texts (`mechanics`) can lag behind changes: cross-check numbers with `difficulty` (game data) and `patchnotes`.
