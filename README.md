
# ao-db — Albion Online knowledge base

**Quick start:** `./setup.sh` (needs git + Python 3.9+, no dependencies), then `./ao search <words>`.

Local SQLite + FTS5 index over https://github.com/ao-data/ao-bin-dumps, queried by `ao`
(`./ao`). If `ao.db` is missing run `./setup.sh` (~15 s).

## Workflow (retrieve → read → answer)
1. Unknown term / fuzzy question → `ao search <words>` (EN or RU; searches items, spells, mobs, zones, all game text, and every raw JSON file).
2. Pull the right entity card: `ao item`, `ao spell`, `ao mob`, `ao zone`, `ao loot`.
3. Need more → `ao doc <file> <key>` (raw record), `ao sql "<query>"` (schema below), `ao item X --json`.
4. Answer in the user's language. Show icons as markdown images:
   items `https://render.albiononline.com/v1/item/<ID>.png?quality=1..5&size=..`, spells `https://render.albiononline.com/v1/spell/<SPELL_ID>.png`
   (official Albion render service). For visual answers: `ao html <items...> -o file.html` then send the file.
5. Cite IDs and say when a value is raw (spell numbers are before item-power scaling; loot "chance" values are the game's weights).

## Commands
| command | purpose |
|---|---|
| `ao search <q> [-t items,spells,mobs,zones,loc,docs] [-n N]` | global search |
| `ao item <id\|name> [--json] [--all-langs]` | stats, recipe, upgrade, spells, used-in, drop sources |
| `ao recipe <item> [-q QTY] [--full] [--recipe N]` | recursive crafting tree + total raw mats |
| `ao usedin <item>` / `ao drops <item>` | reverse lookups |
| `ao compare <a> <b> ...` | stat diff |
| `ao list --cat weapons --sub bow --tier 8 [--enchant 2] [--sort ip]` / `ao categories` | filter items |
| `ao spell <id\|name> [-v]` | spell with resolved description placeholders, items that have it |
| `ao mob <id\|name>` / `ao loot <LIST> [-d depth]` | mobs & loot tables |
| `ao zone <name>` | clusters (type/biome/tier/flags) |
| `ao loc <text>` / `ao loc --key @ITEMS_T4_BAG` | any in-game text in 15 languages |
| `ao files` / `ao doc <file> [key] [--keys]` | browse all 120 raw data files |
| `ao price <items...> [--server europe\|west\|east] [--cities A,B]` | live prices (albion-online-data.com) |
| `ao sql "..."` | raw SQL |

Item args accept `T4_MAIN_SWORD@2`, names (`Broadsword`, `Палаш`) and tier prefixes (`6.1 палаш`, `T8 bow`).
`--lang ru` (before the subcommand) shows RU names in labels.

## Schema (SQLite `ao.db`)
items(id, base_id, enchant, kind, tier, name_en, name_ru, desc_en, desc_ru, shopcat, sub1, sub2, sub3, slot, itempower, weight, itemvalue, craftcat, json)
recipes(item_id, recipe_no, silver, time, focus, amount, resource_id, count, maxreturn) · upgrades(item_id, resource_id, count)
item_spells(item_id, spell_id, slots, tag) · spells(id, kind, name_en, name_ru, desc_en, desc_ru, category, target, cooldown, energy, casttime, castrange, json)
mobs(id, name_en, name_ru, tier, category, typecat, faction, hp, damage, fame, armor, mres, json) · mob_loot(mob_id, lootlist, chance)
loot(list, kind[item|ref|silver], target, amount, chance, extra) · clusters(idx, name, file, type, biome, tier, zone)
loc(key, en, ru, all_json) · docs(id, file, path, key, json)
FTS5: items_fts, spells_fts, mobs_fts, clusters_fts, loc_fts, docs_fts (use `MATCH`, `bm25()`, `snippet()`).
`json` columns hold the full original record (attributes prefixed `@`) → `json_extract(json,'$."@attackdamage"')`.
