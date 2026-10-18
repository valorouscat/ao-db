"""Single registry of operations. The CLI and the MCP server are both generated from it."""
from . import advisor, core, gearcheck, market, patchnotes

S, I, N, B, A = "string", "integer", "number", "boolean", "array"
Q_ITEM = "Item ID (T4_MAIN_SWORD@2) or name in any language, optional tier prefix ('6.1 broadsword', 'T8 палаш')"


def P(type_, desc, default=None, required=False, enum=None):
    return {"type": type_, "description": desc, "default": default, "required": required, "enum": enum}


TOOLS = [
    dict(name="search", fn=core.search,
         desc="Full-text search (EN/RU and other languages) across items, spells, mobs, zones, all in-game text and every raw game data file. "
              "Start here for anything vague.",
         params=dict(query=P(S, "Words to search for", required=True),
                     types=P(A, "Restrict to sections", enum=list(core.TYPES)), limit=P(I, "Rows per section", 10))),
    dict(name="item", fn=core.item,
         desc="Item card: names, tier, category, stats, item value, recipe(s), enchant upgrade, spells/abilities, what it is used in, drop sources.",
         params=dict(query=P(S, Q_ITEM, required=True), raw=P(B, "Append raw JSON record", False), all_langs=P(B, "Names in all 15 languages", False))),
    dict(name="variants", fn=core.variants, desc="All tiers (T1-T8) and enchantments (.0-.4) of an item family with item power and recipe.",
         params=dict(query=P(S, Q_ITEM, required=True))),
    dict(name="list_items", fn=core.list_items,
         desc="Filter items by shop category / subcategory / tier / enchant / slot. Use `categories` to see valid category values.",
         params=dict(cat=P(S, "shopcat, e.g. weapons, armor, accessories, consumables, artefacts (SQL LIKE)"),
                     sub=P(S, "sub1, e.g. sword, bow, plate_armor, cape (SQL LIKE)"), sub2=P(S, "sub2 (SQL LIKE)"),
                     kind=P(S, "weapon, equipmentitem, mount, consumableitem, simpleitem, furnitureitem, ..."),
                     slot=P(S, "mainhand, offhand, head, armor, shoes, cape, bag, mount, food, potion"), craftcat=P(S, "crafting category"),
                     name=P(S, "substring of EN/RU name"), tier=P(I, "tier 1-8"), enchant=P(I, "enchantment 0-4", 0),
                     sort=P(S, "order", "tier", enum=["tier", "ip", "name", "id"]), limit=P(I, "max rows", 100))),
    dict(name="categories", fn=core.categories, desc="List item shop categories and subcategories with counts.", params={}),
    dict(name="compare", fn=core.compare, desc="Side-by-side stat comparison of several items.",
         params=dict(items=P(A, "Two or more item IDs/names", required=True))),
    dict(name="recipe", fn=core.recipe,
         desc="Recursive crafting tree down to raw resources with total material quantities; optional resource return rate.",
         params=dict(query=P(S, Q_ITEM, required=True), qty=P(N, "How many items to craft", 1), depth=P(I, "Max tree depth", 5),
                     recipe_no=P(I, "Alternative recipe index (0-based)", 0), return_rate=P(N, "Resource return rate, % or fraction (e.g. 15.2)", 0),
                     full=P(B, "Also expand raw resources / artefacts (transmutation, shard crafting)", False))),
    dict(name="usedin", fn=core.usedin, desc="Which recipes consume this item (reverse recipe lookup).",
         params=dict(query=P(S, Q_ITEM, required=True), limit=P(I, "max rows", 200))),
    dict(name="drops", fn=core.drops, desc="Where an item drops: loot lists (incl. parent lists), mobs, other files mentioning it.",
         params=dict(query=P(S, Q_ITEM, required=True), limit=P(I, "max mobs", 40))),
    dict(name="loot", fn=core.loot, desc="Expand a loot list (from mob/item/drops output) into items and sub-lists.",
         params=dict(name=P(S, "Loot list name (partial name lists candidates)", required=True), depth=P(I, "Sub-list expansion depth", 1))),
    dict(name="mob", fn=core.mob, desc="Mob card: stats, faction, loot lists, spells, other variants with the same name.",
         params=dict(query=P(S, "Mob ID or name (EN/RU)", required=True), raw=P(B, "Append raw JSON", False))),
    dict(name="spell", fn=core.spell,
         desc="Spell/ability card with description (placeholders filled with base values), cooldown, energy, range, items that have it.",
         params=dict(query=P(S, "Spell ID or name (EN/RU)", required=True), raw=P(B, "Append raw JSON", False),
                     verbose=P(B, "Show placeholder sources", False))),
    dict(name="zone", fn=core.zone, desc="Find zones/clusters by name: type, biome, tier, flags.",
         params=dict(query=P(S, "Zone name", required=True), limit=P(I, "max rows", 30))),
    dict(name="loc", fn=core.loc, desc="Search all in-game text (15 languages) or fetch one localization key in all languages.",
         params=dict(text=P(S, "Text to search"), key=P(S, "Exact key, e.g. @ITEMS_T4_BAG"), limit=P(I, "max rows", 15))),
    dict(name="files", fn=core.files, desc="List all indexed raw game data files with record counts.", params={}),
    dict(name="doc", fn=core.doc, desc="Read raw records from any game data file (e.g. hellgate, mists, factionwarfare, achievements).",
         params=dict(file=P(S, "File name or part of it", required=True), key=P(S, "Record key, SQL LIKE pattern allowed"),
                     limit=P(I, "max records", 5), keys_only=P(B, "Only list record keys", False), max_chars=P(I, "Truncate each record", 8000))),
    dict(name="sql", fn=core.sql, desc="Read-only SQL over the knowledge base (see `schema`). Columns `json` hold full raw records: "
                                       "json_extract(json,'$.\"@attackdamage\"').",
         params=dict(query=P(S, "SELECT / WITH statement", required=True), limit=P(I, "max rows", 200))),
    dict(name="schema", fn=core.schema, desc="Database tables and columns.", params={}),
    dict(name="info", fn=core.info, desc="Data versions and freshness: dump date, current patch, last major update, row counts.", params={}),
    dict(name="price", fn=market.price, desc="Live market prices per city (Albion Online Data Project).",
         params=dict(items=P(A, "Item IDs/names", required=True), server=P(S, "Game server", "europe", enum=list(market.SERVERS)),
                     cities=P(S, "Comma list, e.g. 'Caerleon,Martlock'"), quality=P(I, "1-5", 1))),
    dict(name="history", fn=market.history, desc="Average daily price, volume and trend per city.",
         params=dict(item=P(S, Q_ITEM, required=True), server=P(S, "Game server", "europe", enum=list(market.SERVERS)),
                     cities=P(S, "Comma list"), quality=P(I, "1-5", 1), days=P(I, "Days back", 14))),
    dict(name="best_city", fn=market.best_city, desc="Cheapest city to buy, best buy orders to sell, and the instant flip margin.",
         params=dict(item=P(S, Q_ITEM, required=True), server=P(S, "Game server", "europe", enum=list(market.SERVERS)), quality=P(I, "1-5", 1))),
    dict(name="craft_profit", fn=market.craft_profit,
         desc="Crafting profit estimate from live prices: material cost with return rate, station fee, taxes, revenue, margin.",
         params=dict(item=P(S, Q_ITEM, required=True), server=P(S, "Game server", "europe", enum=list(market.SERVERS)),
                     city=P(S, "City to buy materials / craft", "Caerleon"), sell_city=P(S, "City to sell (default: same)"),
                     return_rate=P(N, "Return rate % (default 15.2, or 43.5 with focus)"), focus=P(B, "Use focus", False),
                     station_fee=P(N, "Station usage fee per 100 nutrition", 0), premium=P(B, "Premium (4% tax vs 8%)", True),
                     qty=P(N, "Items to craft", 1), recipe_no=P(I, "Alternative recipe index", 0), days=P(I, "Days for average fallback", 7))),
    dict(name="build_cost", fn=advisor.build_cost,
         desc="Estimated cost of a gear set from live prices (per slot + total), base item power, and the same set at .0-.3 enchant. "
              "Use whenever gear is recommended or discussed. Consumables: '10x T8_MEAL_STEW'.",
         params=dict(items=P(A, "Items of the build (IDs/names, optional 'Nx' quantity)", required=True),
                     server=P(S, "Game server", "europe", enum=list(market.SERVERS)), city=P(S, "Market city", "Caerleon"),
                     quality=P(I, "1 normal … 5 masterpiece", 1), compare_enchants=P(B, "Add .0-.3 comparison", True))),
    dict(name="gear_check", fn=gearcheck.gear_check,
         desc="Can a player's loadout farm given PvE content? Parses an in-game loadout export (JSON), computes item power, checks the "
              "spell kit (AoE, sustain, defensive, mobility, CC) and consumables, models the camp's guards at every chest stage and tier "
              "from the game files, gives an IP margin + verdict per tier/stage, and the re-gear cost.",
         params=dict(loadout=P(S, "Loadout JSON (in-game export format with equipment/inventory) or @path/to/file.json", required=True),
                     content=P(S, "avalon_solo (green), avalon_veteran (blue), avalon_elite (gold)", "avalon_solo"),
                     tiers=P(A, "Content tiers to check, e.g. ['4','6','8']"), stages=P(A, "Chest stages: small, medium, large"),
                     spec_ip=P(I, "Flat extra IP for every slot without an explicit value", 0),
                     weapon_ip=P(I, "Weapon item power shown in game incl. mastery (= slot_ip mainhand)"),
                     slot_ip=P(S, "In-game IP per slot incl. mastery, e.g. 'mainhand=1300,head=1240,armor=1260,shoes=1250,cape=1100'"),
                     avg_ip=P(I, "Character's average IP from the game; slots without explicit IP share the difference equally"),
                     intents=P(S, "How Q/W/E are set up when the loadout lacks spells or the user described them: 'q=damage,w=damage' "
                                  "or free text like 'Q W на урон'"),
                     hp=P(N, "Character max health from the game (replaces the estimate: 1200 base + items)"),
                     dodge=P(N, "Share of telegraphed (ground/area) mob ability damage dodged", 0.9),
                     dodge_low=P(N, "Pessimistic dodge share shown as a second scenario", 0.5), server=P(S, "Market server", "europe", enum=list(market.SERVERS)),
                     city=P(S, "Price city for re-gear cost", "Caerleon"), price=P(B, "Look up re-gear cost", True),
                     calibrate=P(B, "Shift margins by the calibration offset from real outcomes (knowledge/calibration.json)", True))),
    dict(name="group_check", fn=gearcheck.group_check,
         desc="Predict how a small group (2-3, up to 5) performs in PvE camps, built on the concrete monsters of the content: every "
              "template variant, guards per chest stage clustered into pulls by position, each mob's HP, auto-attack + ability DPS and "
              "resistances vs the group's damage type; players get kit-based weapon factors (real spell damage), roles "
              "(itemroles.json), coordination penalty. Shows hardest pull, mechanics to dodge, loot per player, re-gear risk.",
         params=dict(loadouts=P(A, "One loadout JSON (or @file) per player", required=True),
                     content=P(S, "avalon_veteran (blue, default), avalon_solo (green), avalon_elite (gold)", "avalon_veteran"),
                     ips=P(S, "In-game IP (and optionally max health) per player, separated by '|': 'avg=1250,mainhand=1300,hp=2400 | avg=1180'"),
                     intents=P(S, "Spell intents per player separated by '|': 'q=damage,w=damage | ' (missing spells are auto-picked: "
                                  "damage, or heal for healer weapons)"),
                     dodge=P(N, "Share of telegraphed (ground/area) mob ability damage dodged", 0.9),
                     dodge_low=P(N, "Pessimistic dodge share shown as a second scenario", 0.5),
                     tiers=P(A, "Content tiers, e.g. ['4','6','8']"), stages=P(A, "Chest stages: small, medium, large"),
                     server=P(S, "Market server", "europe", enum=list(market.SERVERS)), city=P(S, "Price city", "Caerleon"),
                     price=P(B, "Look up re-gear cost", True),
                     calibrate=P(B, "Shift margins by the calibration offset from real outcomes (knowledge/calibration.json)", True))),
    dict(name="record_outcome", fn=gearcheck.record_outcome,
         desc="Record a REAL fight result (loadouts, IP, content/tier/chest stage, outcome) in the calibration journal "
              "knowledge/calibration.json; gear_check/group_check shift their margins by the mean model error over the journal. "
              "Use when the user reports how a run actually went. Commit the journal afterwards.",
         params=dict(loadouts=P(A, "One loadout JSON (or @file) per player", required=True),
                     content=P(S, "avalon_solo (green), avalon_veteran (blue), avalon_elite (gold)", required=True),
                     tier=P(I, "Content tier", required=True), stage=P(S, "Chest stage: small, medium, large", required=True),
                     outcome=P(S, "How it went", required=True, enum=list(gearcheck.OUTCOME_MARGIN)),
                     ips=P(S, "In-game IP per player as in group_check: 'avg=1250,mainhand=1300 | avg=1180'"),
                     intents=P(S, "Spell intents per player separated by '|'"), min_hp=P(N, "Lowest HP share during the fight, 0-1"),
                     consumables_used=P(S, "Consumables used, e.g. '2x T6 poison potion'"), notes=P(S, "Free-text notes"),
                     runs=P(I, "How many times this setup cleared this content with this outcome (repeat confirmations)", 1),
                     mastery=P(I, "Average mastery/spec level of the gear (info; the IP values already include it)"),
                     save=P(B, "Write to the journal (false = dry run)", True))),
    dict(name="calibration", fn=gearcheck.calibration,
         desc="Calibration journal: every recorded real outcome vs the current model's raw margin, and the offset applied.", params={}),
    dict(name="chest_value", fn=advisor.chest_value,
         desc="Expected loot value of chests (Avalon roads, corrupted dungeons, hellgates, mists, static dungeons, treasure...) computed "
              "through the loot tables; ranks chests so you can tell which are worth opening.",
         params=dict(query=P(S, "Chest name part (AVALON, ROAD, CORRUPTED...) or chest type (avaroadloot, rdsololoot, cdboss...)", required=True),
                     tier=P(I, "Content tier (4-8)", 8), live=P(B, "Use live market prices instead of game item value", False),
                     server=P(S, "Game server", "europe", enum=list(market.SERVERS)), city=P(S, "Price city", "Caerleon"),
                     top=P(I, "Top value drivers per chest", 8))),
    dict(name="meta_builds", fn=advisor.meta_builds,
         desc="Real usage stats from the official killboard: most successful weapons (kills, deaths, K/D, avg IP) and, for one weapon, "
              "what armor/offhand/cape/food its players use.",
         params=dict(weapon=P(S, "Weapon to drill into (optional)"), server=P(S, "Game server", "europe", enum=list(advisor.GAMEINFO)),
                     pages=P(I, "Pages of 51 events (1-20)", 10), min_ip=P(I, "Ignore players below this average IP", 0),
                     top=P(I, "Rows", 12))),
    dict(name="difficulty", fn=advisor.difficulty,
         desc="Reward multipliers (loot ×, silver ×, fame ×), mob buffs (HP/damage) and entry rules per content type and level, from the "
              "game files: dungeon enchant .1-.4 and boss rooms, zone colour and Outlands region quality, mists, depths, dragon areas, "
              "expeditions, corrupted dungeons, hellgates, tier scaling, market taxes. No argument = overview.",
         params=dict(content=P(S, "Content: " + ", ".join(advisor.DIFFICULTY) + " (RU/EN aliases ok)"))),
    dict(name="mechanics", fn=advisor.mechanics,
         desc="Official in-game descriptions and data files for a content type: " + ", ".join(advisor.TOPICS) + ".",
         params=dict(topic=P(S, "Topic", required=True), limit=P(I, "Max texts", 25))),
    dict(name="notes", fn=advisor.notes, desc="Search curated, sourced knowledge notes (strategy, verified findings). No query lists all notes.",
         params=dict(query=P(S, "Search words"), limit=P(I, "Max notes", 5))),
    dict(name="save_note", fn=advisor.save_note,
         desc="Save a verified finding as a knowledge note (knowledge/*.md) for future answers. Requires sources.",
         params=dict(title=P(S, "Title", required=True), body=P(S, "Markdown body", required=True),
                     sources=P(A, "URLs / game IDs / tool outputs used", required=True), tags=P(A, "Tags"))),
    dict(name="patchnotes", fn=patchnotes.patchnotes,
         desc="Search official patch notes / dev updates (Steam news, 2018→now). Results relevant to the query, newest first. "
              "Use to check that any mechanic, number, build or guide is still current.",
         params=dict(query=P(S, "What changed (item, ability, content, mechanic)", required=True),
                     since=P(S, "Only notes on/after YYYY-MM-DD"), limit=P(I, "Max sections", 6), max_chars=P(I, "Truncate each section", 1500))),
    dict(name="latest_patches", fn=patchnotes.latest_patches, desc="Current patch, last major update and the latest official posts.",
         params=dict(limit=P(I, "Rows", 12))),
    dict(name="update_patchnotes", fn=patchnotes.update, desc="Fetch new official posts from Steam into knowledge/patchnotes and reindex.",
         params=dict(full=P(B, "Re-scan the whole history", False))),
    dict(name="html", fn=core.html_cards, desc="Render item cards with icons to an HTML file.",
         params=dict(items=P(A, "Item IDs/names", required=True), out=P(S, "Output path", "cards.html"))),
]

BY_NAME = {t["name"]: t for t in TOOLS}


def call(name, args):
    t = BY_NAME[name]
    kw = {k: v for k, v in args.items() if k in t["params"] and v is not None}
    return t["fn"](**kw)
