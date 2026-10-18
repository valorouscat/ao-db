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
`search` (also finds camps/spawns/chest stages and curated notes, the real-outcome journal, patch notes) → entity tool (`item`, `spell`, `mob`, `zone`, `variants`, `recipe`, `usedin`, `drops`, `loot`) → `doc` / `sql` for details.

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
   - PvP / PvPvE (mists, corrupted dungeons, hellgates, arenas, Roads, black zone): `pvp_rules` (lethality, IP soft cap +
     factor, entry IP, team, reward multipliers — from worldsettings.json), `pvp_builds` (killboard builds at the content's fight
     size simulated against each other at the cap IP, cheapest tier/enchant set reaching the cap), `pvp_check` (a player's
     loadout: effective IP and wasted IP above the cap, kit vs players, gaps such as no cleanse/escape, matchups),
     `farm_plan` (where to farm: win/death chance vs the meta, expected re-gear loss/h, break-even silver/h). The public
     killboard covers open-world kills only — say it is a proxy for instanced content. Fights/hour are assumptions: ask the
     user for their real numbers and pass `encounters_per_hour` / `silver_per_hour`.
   - Monster fights in detail: `encounter_sim` (corrupted dungeon maps, Mists camps / dungeon, hellgate PvE) and `camp_sim`
     (Roads camps) fight every pull second by second → clear time, lowest HP (both dodge scenarios), failed pulls, elite risk,
     fame/hour, hardest pull. Name the hardest pull and heavy hits in the answer; times are calibrated only if the journal has
     `clear_minutes` — ask the user how long their clears take and record it.
   - **Real outcomes calibrate the model.** When the user reports how a run actually went (cleared easily / barely / died, lowest HP,
     consumables), call `record_outcome` (outcome: easy / doable / hard / failed; same loadout + IP as the check) and commit
     `knowledge/calibration.json`. gear_check/group_check then show calibrated margins with the raw value in brackets;
     `calibration` lists the journal. Repeat clears of the same setup/content → `runs=N` (one entry, weighted), not duplicates.
     With fewer than 3 distinct entries say the offset may not transfer to other tiers/chests/builds.
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

## Content assessments must use the concrete monsters
Any "can I/we do X" answer is built on the actual mobs of that content (gear_check / group_check do this: map templates →
guards per chest stage → each mob's HP, auto-attack + ability DPS, armor/mres, pulls by position, all template variants).
In the answer, name the hardest pull (which mobs) and the telegraphed mechanics. Always report both dodge scenarios
(default 90% of telegraphed ground/area abilities, pessimistic 50%) and the "caught heavy hit" check (one-shot or % HP);
player defenses (shields, heals, lifesteal, CC, invulnerability, kiting) are credited from their actual spells.
Player stats come from their items (armor/mres/CC res/flat HP/damage & heal bonuses, scaled per slot by ItemPowerProgression);
max health = 1200 base + gear. If the user gives the in-game HP, pass it (`hp` / `ips "…,hp=2400"`). Never estimate only from "intended group size".
When the user describes spells in words ("Q W на урон", "хил на E"), pass that as `intents`; the tool picks the matching
spells per slot and shows them (marked *) — confirm the pick in the answer.

## Facts to keep straight
- Item IDs `T<tier>_<NAME>[@<enchant>]`; enchanted resources `T5_ORE_LEVEL2@2`; queries accept `8.3 claymore`, `палаш`.
- Quality adds IP: good +20, outstanding +40, excellent +60, masterpiece +100.
- Return rate: royal city 15.2% / 43.5% with focus; bonus city 24.8% / 47.9%. Market tax 4% premium / 8% otherwise + 2.5% setup fee.
- Corrupted dungeons: Hunter = blue/yellow, no item loss; Stalker = red/black, full loot; Slayer = red/black, Might, full loot.
  Entry uses **base** IP: 700 / 900 / 1100 (Abyssal Depths, 2025-06-30; game data agrees). The in-game tutorial text still says
  800/900/1200 — it is outdated. Since then loot no longer scales with Infamy; Infamy fame scaling max 20%.
- In-game texts (`mechanics`) can lag behind changes: cross-check numbers with `difficulty` (game data) and `patchnotes`.
