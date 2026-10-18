"""Query layer over ao.db. Every public function returns a markdown string.

Used by both the CLI (aodb.cli) and the MCP server (aodb.mcp_server).
Item / mob / spell arguments accept an ID (T4_MAIN_SWORD, T4_MAIN_SWORD@2), a name in
any game language ("Broadsword", "Палаш") and an optional tier prefix ("6.1 палаш", "T8 bow").
"""
import functools, json, os, re, sqlite3, html as H
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.environ.get("AO_DB", os.path.join(ROOT, "ao.db"))
ICON = "https://render.albiononline.com/v1/item/{}.png"
SPELL_ICON = "https://render.albiononline.com/v1/spell/{}.png"
TIER_NAMES = {1: "Beginner", 2: "Novice", 3: "Journeyman", 4: "Adept", 5: "Expert", 6: "Master", 7: "Grandmaster", 8: "Elder"}
ENCHANT_NAMES = {0: "", 1: "Uncommon", 2: "Rare", 3: "Exceptional", 4: "Pristine"}
QUALITY_NAMES = {1: "Normal", 2: "Good", 3: "Outstanding", 4: "Excellent", 5: "Masterpiece"}
TYPES = ("items", "spells", "mobs", "zones", "loc", "docs")

STAT_KEYS = ["itempower", "abilitypower", "attackdamage", "attackspeed", "attackrange", "hitpointsmax", "hitpointsregenerationbonus",
             "energymax", "energyregenerationbonus", "physicalarmor", "magicresistance", "crowdcontrolresistance", "healmodifier",
             "physicalspelldamagebonus", "magicspelldamagebonus", "magiccooldownreduction", "magiccasttimereduction", "healbonus",
             "threatbonus", "bonusdefensevsplayers", "bonusdefensevsmobs", "bonusccdurationvsplayers", "bonusccdurationvsmobs",
             "attackspeedbonus", "movespeedbonus", "durability", "weight", "maxload", "maxstacksize", "itemvalue", "nutrition",
             "mountedbuff", "mounthitpointsmax", "mounttime", "focusfireprotectionpenetration", "activespellslots", "passivespellslots",
             "twohanded", "slottype", "attacktype", "maxqualitylevel", "tradable", "craftingcategory", "fishingfame", "maxfame",
             "consumespell", "destinyandjournalcraftfamefactor"]

LANG = "en"
_con = None


class AOError(Exception):
    """User-facing error (not found, bad input)."""


# ------------------------------------------------------------------ db helpers
def connect():
    global _con
    if _con is None:
        if not os.path.exists(DB):
            raise AOError(f"Database not found: {DB}. Run ./setup.sh (clones ao-bin-dumps and builds the index, ~15 s).")
        _con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, check_same_thread=False)
        _con.row_factory = sqlite3.Row
    return _con


def q(sql, *a):
    return connect().execute(sql, a).fetchall()


def q1(sql, *a):
    return connect().execute(sql, a).fetchone()


def fts_query(text, prefix=True):
    """Free text -> safe FTS5 query (AND of tokens; prefix match unless prefix=False)."""
    toks = [p for t in re.findall(r"[\w@]+", text, re.U) for p in t.replace("@", " ").split()]
    star = "*" if prefix else ""
    return " ".join(f'"{t}"{star}' for t in toks) if toks else '""'


def fmt(v):
    if isinstance(v, float):
        return f"{v:,.2f}".rstrip("0").rstrip(".") if abs(v) < 1e15 else str(v)
    return "" if v is None else str(v)


def money(v):
    return "n/a" if v is None else f"{v:,.0f}"


def table(rows, headers):
    if not rows:
        return "_(empty)_"
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for r in rows:
        out.append("| " + " | ".join(fmt(x).replace("|", "\\|").replace("\n", " ") for x in r) + " |")
    return "\n".join(out)


def pick(row, field="name"):
    ru = row[f"{field}_ru"] if f"{field}_ru" in row.keys() else None
    return ru if LANG == "ru" and ru else row[f"{field}_en"]


def label(iid):
    r = q1("SELECT name_en, name_ru, tier, enchant FROM items WHERE id=?", iid)
    if not r:
        return f"`{iid}`"
    t = f" {r['tier']}.{r['enchant']}" if r["tier"] else ""
    return f"{pick(r) or '?'}{t} (`{iid}`)"


def item_json(iid):
    r = q1("SELECT json FROM items WHERE id=?", iid)
    return json.loads(r["json"]) if r else {}


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ resolvers
def split_tier(text):
    m = re.match(r"^\s*[TtТт]?(\d)(?:[.@](\d))?\s+(.+)$", text)
    if m:
        return int(m.group(1)), int(m.group(2) or 0), m.group(3)
    return None, None, text


def resolve_items(text):
    """All candidate item IDs for a query, best first."""
    text = text.strip()
    if not text:
        raise AOError("Empty item query")
    r = q1("SELECT id FROM items WHERE id=?", text) or q1("SELECT id FROM items WHERE upper(id)=upper(?)", text)
    if r:
        return [r["id"]]
    tier, ench, name = split_tier(text)
    cond, args = "", []
    if tier:
        cond, args = " AND i.tier=? AND i.enchant=?", [tier, ench]
    rows = q(f"SELECT i.id FROM items i WHERE (lower(i.name_en)=lower(?) OR lower(i.name_ru)=lower(?)){cond} "
             "ORDER BY i.enchant, i.tier, length(i.id)", name, name, *args) if len(name) > 2 else []
    for prefix in (False, True):  # whole-word matches beat prefix matches ("bar" ≠ "bard")
        if rows:
            break
        rows = q(f"SELECT i.id FROM items_fts f JOIN items i ON i.id=f.id WHERE items_fts MATCH ?{cond} "
                 "ORDER BY i.enchant, (i.kind IN ('mountskin') OR i.shopcat IN ('skins', 'vanity')), "
                 "bm25(items_fts, 5, 10, 10, 1, 1, 1), length(i.id) LIMIT 50", fts_query(name, prefix), *args)
    if not rows and tier:
        return resolve_items(name)
    return [r["id"] for r in rows]


def resolve_item(text):
    ids = resolve_items(text)
    if not ids:
        raise AOError(f"Item not found: {text!r}. Try search.")
    return ids[0]


def resolve_entity(table_, text, what):
    text = text.strip()
    r = q1(f"SELECT id FROM {table_} WHERE id=?", text) or q1(f"SELECT id FROM {table_} WHERE upper(id)=upper(?)", text) \
        or q1(f"SELECT id FROM {table_} WHERE lower(name_en)=lower(?) OR lower(name_ru)=lower(?) ORDER BY length(id)", text, text) \
        or q1(f"SELECT t.id FROM {table_}_fts f JOIN {table_} t ON t.id=f.id WHERE {table_}_fts MATCH ? "
              f"ORDER BY (t.name_en IS NULL), bm25({table_}_fts), length(t.id) LIMIT 1", fts_query(text))
    if not r:
        raise AOError(f"{what} not found: {text!r}. Try search.")
    return r["id"]


# ------------------------------------------------------------------ search
def search(query, types=None, limit=10):
    fq = fts_query(query)
    want = set(types or TYPES)
    out = []

    def sec(title, rows, hdr):
        if rows:
            out.append(f"### {title}\n" + table([tuple(r) for r in rows], hdr))

    if "items" in want:
        sec("Items", q("SELECT i.id, i.name_en, i.name_ru, i.tier, i.kind, i.shopcat||'/'||COALESCE(i.sub1,'') FROM items_fts f "
                       "JOIN items i ON i.id=f.id WHERE items_fts MATCH ? AND i.enchant=0 ORDER BY bm25(items_fts, 5, 10, 10, 1, 1, 1) LIMIT ?",
                       fq, limit), ["id", "name", "ru", "T", "kind", "category"])
    if "spells" in want:
        sec("Spells", q("SELECT s.id, s.name_en, s.name_ru, s.kind, s.category, substr(replace(s.desc_en, char(10), ' '),1,90) FROM spells_fts f "
                        "JOIN spells s ON s.id=f.id WHERE spells_fts MATCH ? ORDER BY (s.name_en IS NULL), bm25(spells_fts, 5, 10, 10, 1, 1) LIMIT ?",
                        fq, limit), ["id", "name", "ru", "kind", "cat", "desc"])
    if "mobs" in want:
        sec("Mobs", q("SELECT m.id, m.name_en, m.name_ru, m.tier, m.category, m.faction, m.hp FROM mobs_fts f JOIN mobs m ON m.id=f.id "
                      "WHERE mobs_fts MATCH ? ORDER BY bm25(mobs_fts, 5, 10, 10, 1, 1) LIMIT ?", fq, limit),
            ["id", "name", "ru", "T", "cat", "faction", "HP"])
    if "zones" in want:
        sec("Zones", q("SELECT c.idx, c.name, c.type, c.biome, c.tier, c.zone FROM clusters_fts f JOIN clusters c ON c.idx=f.idx "
                       "WHERE clusters_fts MATCH ? ORDER BY bm25(clusters_fts) LIMIT ?", fq, limit), ["index", "name", "type", "biome", "T", "flags"])
    if "loc" in want:
        sec("Game text (localization)", q("SELECT l.key, substr(replace(l.en,char(10),' '),1,100), substr(replace(l.ru,char(10),' '),1,100) "
                                          "FROM loc_fts f JOIN loc l ON l.rowid=f.rowid WHERE loc_fts MATCH ? ORDER BY bm25(loc_fts, 2, 5, 5) LIMIT ?",
                                          fq, limit), ["key", "en", "ru"])
    if "docs" in want:
        sec("Raw game data (all files)", q("SELECT d.file, d.key, d.path, snippet(docs_fts, 2, '**', '**', '…', 12) FROM docs_fts f "
                                           "JOIN docs d ON d.id=f.rowid WHERE docs_fts MATCH ? ORDER BY bm25(docs_fts, 1, 5, 1) LIMIT ?",
                                           fq, limit), ["file", "key", "path", "snippet"])
    return "\n\n".join(out) or f"Nothing found for: {query}"


# ------------------------------------------------------------------ items
def recipes_of(iid):
    out = defaultdict(lambda: {"res": []})
    for r in q("SELECT * FROM recipes WHERE item_id=? ORDER BY recipe_no, rowid", iid):
        d = out[r["recipe_no"]]
        d.update(silver=r["silver"], time=r["time"], focus=r["focus"], amount=r["amount"] or 1)
        if r["resource_id"]:
            d["res"].append((r["resource_id"], r["count"] or 0, r["maxreturn"]))
    return [out[k] for k in sorted(out)]


def returnable(maxreturn):
    return maxreturn is None or maxreturn > 0


@functools.lru_cache(maxsize=None)
def item_value(iid, _depth=0):
    """Game 'item value' (basis of station fees): own @itemvalue or sum over recipe resources."""
    v = num(item_json(iid).get("@itemvalue"))
    if v is not None or _depth > 3:
        return v
    recs = recipes_of(iid)
    if not recs or not recs[0]["res"]:
        return None
    total = 0.0
    for rid, cnt, _ in recs[0]["res"]:
        rv = item_value(rid, _depth + 1)
        if rv is None:
            return None
        total += rv * cnt
    return total / (recs[0]["amount"] or 1)


def drop_sources(iid, limit=25):
    """Loot lists containing the item (walking up references) and mobs that use them."""
    lists, frontier, depth = {}, [r["list"] for r in q("SELECT list FROM loot WHERE target=? AND kind='item'", iid)], 0
    while frontier and depth < 6:
        nxt = []
        for name in frontier:
            if name not in lists:
                lists[name] = depth
                nxt += [r["list"] for r in q("SELECT list FROM loot WHERE target=? AND kind='ref'", name)]
        frontier, depth = nxt, depth + 1
    mobs = []
    if lists:
        ph = ",".join("?" * len(lists))
        mobs = q(f"SELECT ml.mob_id, m.name_en, m.name_ru, m.tier, ml.lootlist, ml.chance FROM mob_loot ml LEFT JOIN mobs m ON m.id=ml.mob_id "
                 f"WHERE ml.lootlist IN ({ph}) ORDER BY ml.chance DESC LIMIT ?", *lists.keys(), limit)
    return lists, mobs


def item(query, raw=False, all_langs=False):
    ids = resolve_items(query)
    if not ids:
        raise AOError(f"Item not found: {query!r}. Try search.")
    iid = ids[0]
    it = q1("SELECT * FROM items WHERE id=?", iid)
    data = json.loads(it["json"])
    o = [f"## {it['name_en'] or iid}  /  {it['name_ru'] or ''}", f"![{iid}]({ICON.format(iid)}?size=128)\n",
         f"- **ID:** `{iid}`  (base `{it['base_id']}`, kind `{it['kind']}`)",
         f"- **Tier:** {it['tier']}.{it['enchant']}  ({TIER_NAMES.get(it['tier'] or 0, '')} {ENCHANT_NAMES.get(it['enchant'], '')})".rstrip(),
         f"- **Category:** {' / '.join(x for x in (it['shopcat'], it['sub1'], it['sub2'], it['sub3']) if x)}"]
    if it["desc_en"]:
        o.append(f"- **Description:** {it['desc_en']}")
    if it["desc_ru"]:
        o.append(f"- **Описание:** {it['desc_ru']}")
    iv = item_value(iid)
    if iv:
        o.append(f"- **Item value:** {fmt(iv)} (station fee = value × 0.1125 × fee/100 nutrition)")
    o.append(f"- **Icon:** {ICON.format(iid)}  (`?quality=1..5&size=N`)")
    stats = [(k, data["@" + k]) for k in STAT_KEYS if "@" + k in data]
    if stats:
        o.append("\n### Stats\n" + table(stats, ["stat", "value"]))
    if all_langs:
        o.append("\n### Names\n" + table(list(json.loads(it["names_json"] or "{}").items()), ["lang", "name"]))
    for n, r in enumerate(recipes_of(iid)):
        o.append(f"\n### Recipe {n + 1}" + (f" (crafts ×{r['amount']})" if r["amount"] > 1 else "") +
                 f" — silver {fmt(r['silver'])}, focus {fmt(r['focus'])}, time {fmt(r['time'])}s")
        o.append(table([(label(x), c, "no" if not returnable(mr) else "") for x, c, mr in r["res"]], ["resource", "count", "returned?"]))
    ups = q("SELECT resource_id, count FROM upgrades WHERE item_id=?", iid)
    if ups:
        o.append("\n### Upgrade to next enchant\n" + table([(label(u["resource_id"]), u["count"]) for u in ups], ["resource", "count"]))
    sp = q("SELECT s.spell_id, s.slots, s.tag, sp.name_en, sp.name_ru, sp.kind FROM item_spells s LEFT JOIN spells sp ON sp.id=s.spell_id "
           "WHERE s.item_id=?", it["base_id"])
    if sp:
        o.append("\n### Spells\n" + table([(r["spell_id"], r["name_en"], r["name_ru"], r["kind"].replace("spell", ""),
                                            r["slots"] or "passive", r["tag"] or "") for r in sp],
                                          ["spell", "name", "ru", "kind", "slot(s)", "tag"]))
    used = q("SELECT DISTINCT item_id FROM recipes WHERE resource_id=? LIMIT 31", iid)
    if used:
        o.append(f"\n### Used in ({'30+' if len(used) > 30 else len(used)} recipes)\n" + ", ".join(label(u["item_id"]) for u in used[:30]))
    lists, mobs = drop_sources(iid, 10)
    if lists:
        o.append(f"\n### Drops from {len(lists)} loot lists\n" + ", ".join(f"`{k}`" for k in list(lists)[:15]) + (" …" if len(lists) > 15 else ""))
    if mobs:
        o.append("\n### Mobs (top by weight)\n" + table([(m["mob_id"], pick(m), m["tier"], m["lootlist"], m["chance"]) for m in mobs],
                                                       ["mob", "name", "T", "loot list", "weight"]))
    if len(ids) > 1:
        o.append("\n_Other matches:_ " + ", ".join(f"`{x}`" for x in ids[1:15]))
    if raw:
        o.append("\n### Raw\n```json\n" + json.dumps(data, ensure_ascii=False, indent=1) + "\n```")
    return "\n".join(o)


def variants(query):
    """All tiers × enchantments of an item family with IP and recipe summary."""
    iid = resolve_item(query)
    base = q1("SELECT base_id FROM items WHERE id=?", iid)["base_id"]
    family = re.sub(r"_LEVEL\d$", "", re.sub(r"^T\d_", "", base))
    bases = [f"T{t}_{family}{lv}" for t in range(1, 9) for lv in ("", "_LEVEL1", "_LEVEL2", "_LEVEL3", "_LEVEL4")]
    rows = q(f"SELECT id, tier, enchant, itempower, name_en, name_ru FROM items WHERE base_id IN ({','.join('?' * len(bases))}) "
             "ORDER BY tier, enchant", *bases)
    out = []
    for r in rows:
        rec = recipes_of(r["id"])
        mats = ", ".join(f"{c}× {x}" for x, c, _ in rec[0]["res"]) if rec else ""
        out.append((r["id"], f"{r['tier']}.{r['enchant']}", r["itempower"], mats, f"![]({ICON.format(r['id'])}?size=40)"))
    head = pick(q1("SELECT name_en, name_ru FROM items WHERE id=?", iid)) or family
    return f"## {head}: all tiers/enchantments ({len(out)})\n\n" + table(out, ["id", "T", "IP", "recipe #1", "icon"])


def list_items(cat=None, sub=None, sub2=None, kind=None, slot=None, craftcat=None, name=None, tier=None, enchant=0, sort="tier", limit=100):
    cond, args = ["1=1"], []
    for col, val in (("shopcat", cat), ("sub1", sub), ("sub2", sub2), ("kind", kind), ("slot", slot), ("craftcat", craftcat)):
        if val:
            cond.append(f"{col} LIKE ?"); args.append(val)
    if tier is not None:
        cond.append("tier=?"); args.append(tier)
    if enchant is not None:
        cond.append("enchant=?"); args.append(enchant)
    if name:
        cond.append("(name_en LIKE ? OR name_ru LIKE ?)"); args += [f"%{name}%"] * 2
    order = {"ip": "itempower DESC", "tier": "tier, id", "name": "name_en", "id": "id"}.get(sort, "tier, id")
    rows = q(f"SELECT id, name_en, name_ru, tier, enchant, shopcat, sub1, sub2, itempower FROM items WHERE {' AND '.join(cond)} "
             f"ORDER BY {order} LIMIT ?", *args, limit)
    return table([tuple(r) for r in rows], ["id", "name", "ru", "T", "ench", "cat", "sub1", "sub2", "IP"]) + f"\n\n{len(rows)} rows"


def categories():
    rows = q("SELECT shopcat, sub1, COUNT(*) FROM items WHERE enchant=0 GROUP BY 1, 2 ORDER BY 1, 2")
    return table([tuple(r) for r in rows], ["shopcat", "sub1", "items"])


def compare(items):
    ids = [resolve_item(x) for x in items]
    datas = [item_json(i) for i in ids]
    keys = [k for k in STAT_KEYS if any("@" + k in d for d in datas)]
    rows = [(k, *[d.get("@" + k, "") for d in datas]) for k in keys]
    return table(rows, ["stat"] + [label(i) for i in ids])


# ------------------------------------------------------------------ crafting
def _is_leaf(iid, full):
    if full:
        return False
    it = q1("SELECT shopcat, sub1 FROM items WHERE id=?", iid)
    return bool(it) and (it["shopcat"] == "artefacts" or it["sub1"] == "resources")


def _tree(iid, qty, depth, maxdepth, rr, full, totals, lines, recipe_no=0, ret=True):
    lines.append(f"{'  ' * depth}- {qty:,.2f}".rstrip("0").rstrip(".") + f" × {label(iid)}")
    recs = recipes_of(iid)
    if not recs or depth >= maxdepth or (depth > 0 and _is_leaf(iid, full)):
        totals[iid] += qty
        return
    r = recs[min(recipe_no, len(recs) - 1)]
    if not r["res"]:
        totals[iid] += qty
        return
    crafts = qty / r["amount"]
    for rid, cnt, mr in r["res"]:
        if rid != iid:
            k = (1 - rr) if returnable(mr) else 1
            _tree(rid, crafts * cnt * k, depth + 1, maxdepth, rr, full, totals, lines)


def recipe(query, qty=1, depth=5, recipe_no=0, return_rate=0.0, full=False):
    iid = resolve_item(query)
    recs = recipes_of(iid)
    if not recs:
        raise AOError(f"{label(iid)} has no crafting recipe")
    rr = return_rate / 100 if return_rate > 1 else return_rate
    totals, lines = defaultdict(float), []
    _tree(iid, qty, 0, depth, rr, full, totals, lines, recipe_no)
    r = recs[min(recipe_no, len(recs) - 1)]
    crafts = qty / r["amount"]
    o = [f"## Crafting tree: {label(iid)} ×{fmt(float(qty))}" + (f" (return rate {rr:.1%})" if rr else ""), ""]
    if len(recs) > 1:
        o.append(f"_{len(recs)} alternative recipes; showing #{min(recipe_no, len(recs) - 1) + 1} (recipe_no is 0-based)_\n")
    o += lines
    o.append(f"\nPer craft: silver {fmt(r['silver'])} · focus {fmt(r['focus'])} · time {fmt(r['time'])}s · crafts needed: {fmt(crafts)}")
    o.append("\n### Total base materials\n" + table(sorted(((label(k), round(v, 2)) for k, v in totals.items()), key=lambda x: -x[1]),
                                                   ["material", "qty"]))
    if not full:
        o.append("\n_Raw resources and artefacts are leaves; full=True expands transmutation / shard recipes._")
    return "\n".join(o)


def usedin(query, limit=200):
    iid = resolve_item(query)
    rows = q("SELECT DISTINCT r.item_id, r.count, i.name_en, i.name_ru, i.tier, i.enchant FROM recipes r JOIN items i ON i.id=r.item_id "
             "WHERE r.resource_id=? ORDER BY i.tier, i.id LIMIT ?", iid, limit)
    return f"## {label(iid)} is used in {len(rows)} recipes\n\n" + table([tuple(r) for r in rows], ["item", "count", "name", "ru", "T", "ench"])


def drops(query, limit=40):
    iid = resolve_item(query)
    lists, mobs = drop_sources(iid, limit)
    direct = q("SELECT list, amount, chance FROM loot WHERE target=? AND kind='item'", iid)
    o = [f"## Where {label(iid)} drops\n", "### Direct loot lists\n" + table([tuple(r) for r in direct], ["list", "amount", "weight"]),
         f"\n### All lists incl. parents ({len(lists)})\n" + ", ".join(f"`{k}`(d{v})" for k, v in list(lists.items())[:40]) + (" …" if len(lists) > 40 else ""),
         "\n### Mobs\n" + table([(m["mob_id"], m["name_en"], m["name_ru"], m["tier"], m["lootlist"], m["chance"]) for m in mobs],
                                ["mob", "name", "ru", "T", "list", "weight"])]
    other = q("SELECT d.file, d.key, d.path FROM docs_fts f JOIN docs d ON d.id=f.rowid WHERE docs_fts MATCH ? "
              "AND d.file NOT IN ('items.json','loot.json','mobs.json') LIMIT 20", f'"{iid}"')
    if other:
        o.append("\n### Mentioned in other game files\n" + table([tuple(r) for r in other], ["file", "key", "path"]))
    return "\n".join(o)


def loot(name, depth=1):
    if not q1("SELECT 1 FROM loot WHERE list=?", name):
        cand = q("SELECT DISTINCT list FROM loot WHERE list LIKE ? LIMIT 30", f"%{name}%")
        raise AOError("Unknown loot list. Candidates: " + (", ".join(r["list"] for r in cand) or "none"))
    o = [f"## Loot list `{name}`\n"]

    def expand(lst, d):
        for r in q("SELECT * FROM loot WHERE list=?", lst):
            ch = f" weight={fmt(r['chance'])}" if r["chance"] is not None else ""
            if r["kind"] == "ref":
                o.append(f"{'  ' * d}- ↳ list `{r['target']}`{ch}")
                if d < depth:
                    expand(r["target"], d + 1)
            else:
                o.append(f"{'  ' * d}- {label(r['target'])} ×{r['amount'] or 1}{ch}")

    expand(name, 0)
    mobs = q("SELECT mob_id, chance FROM mob_loot WHERE lootlist=? LIMIT 20", name)
    if mobs:
        o.append("\nUsed by mobs: " + ", ".join(f"`{m['mob_id']}`({fmt(m['chance'])})" for m in mobs))
    return "\n".join(o)


# ------------------------------------------------------------------ mobs
MOB_KEYS = ["hitpointsmax", "hitpointsregeneration", "attackdamage", "attackspeed", "attackrange", "attacktype", "physicalarmor",
            "magicresistance", "crowdcontrolresistance", "movespeed", "fame", "abilitypower", "aggroradius", "respawntimesecondsmin",
            "respawntimesecondsmax", "npchostility", "lootprefab", "dangerstate", "avatar"]


def mob(query, raw=False):
    mid = resolve_entity("mobs", query, "Mob")
    m = q1("SELECT * FROM mobs WHERE id=?", mid)
    d = json.loads(m["json"])
    o = [f"## {m['name_en'] or mid} / {m['name_ru'] or ''}\n",
         f"- **ID:** `{mid}` · tier {m['tier']} · type `{m['typecat']}` · category `{m['category']}` · faction `{m['faction']}`\n",
         table([(k, d["@" + k]) for k in MOB_KEYS if "@" + k in d], ["stat", "value"])]
    lootl = q("SELECT lootlist, chance FROM mob_loot WHERE mob_id=? ORDER BY chance DESC", mid)
    if lootl:
        o.append("\n### Loot lists\n" + table([tuple(r) for r in lootl], ["list", "weight"]) + "\n_Expand with loot(<list>)_")
    spells = sorted(set(re.findall(r'"@(?:name|uniquename|spell)": "([A-Z0-9_]+)"', json.dumps(d.get("Spells") or d.get("spells") or {}))))
    if spells:
        o.append("\n### Spells\n" + ", ".join(f"`{s}`" for s in spells))
    variants_ = q("SELECT id, tier, hp, fame FROM mobs WHERE name_en=? AND id<>? ORDER BY tier LIMIT 12", m["name_en"], mid) if m["name_en"] else []
    if variants_:
        o.append("\n### Same name, other variants\n" + table([tuple(r) for r in variants_], ["id", "T", "HP", "fame"]))
    if raw:
        o.append("\n```json\n" + json.dumps(d, ensure_ascii=False, indent=1) + "\n```")
    return "\n".join(o)


# ------------------------------------------------------------------ spells
def _get_path(obj, path):
    """Navigate 'directattributechange[0].change' in an xmltodict-style dict."""
    cur = obj
    for part in path.split("."):
        m = re.match(r"^(\w+)(?:\[(\d+)\])?$", part)
        if not m or cur is None:
            return None
        k, i = m.group(1), m.group(2)
        nxt = None
        if isinstance(cur, dict):
            nxt = cur.get("@" + k, cur.get(k))
            if nxt is None:
                for v in cur.values():
                    if isinstance(v, dict) and (k in v or "@" + k in v):
                        nxt = v.get("@" + k, v.get(k))
                        break
        if i is not None:
            lst = nxt if isinstance(nxt, list) else [nxt]
            nxt = lst[int(i)] if nxt is not None and int(i) < len(lst) else None
        elif isinstance(nxt, list):
            nxt = nxt[0]
        cur = nxt
    return cur


def _resolve_tag(tag):
    m = re.match(r"^\$\$?([A-Z0-9_]+)\.(.+?)\$$", tag or "")
    if not m:
        return None
    r = q1("SELECT json FROM spells WHERE id=?", m.group(1))
    return _get_path(json.loads(r["json"]), m.group(2)) if r else None


def spell_text(s, d, lang=None):
    lang = lang or LANG
    desc = (s["desc_ru"] if lang == "ru" and s["desc_ru"] else s["desc_en"]) or ""
    refs = ((d.get("locareferences") or {}).get("description") or {}).get("locareference") or []
    refs = [x.get("@tag") for x in (refs if isinstance(refs, list) else [refs])]
    vals = [_resolve_tag(t) for t in refs]
    for i, v in enumerate(vals):
        if v is not None and not isinstance(v, (dict, list)):
            nv = num(v)
            desc = desc.replace("{%d}" % i, fmt(abs(nv)) if nv is not None else str(v))
    return re.sub(r"\[/?\w+\]", "", desc), list(zip(refs, vals))


def spell(query, raw=False, verbose=False):
    sid = resolve_entity("spells", query, "Spell")
    s = q1("SELECT * FROM spells WHERE id=?", sid)
    d = json.loads(s["json"])
    o = [f"## {s['name_en'] or sid} / {s['name_ru'] or ''}\n", f"![{sid}]({SPELL_ICON.format(sid)})\n",
         f"- **ID:** `{sid}` · {s['kind']} · category `{s['category']}` · target `{s['target']}`",
         f"- **Cooldown:** {fmt(s['cooldown'])}s · **Energy:** {fmt(s['energy'])} · **Cast:** {fmt(s['casttime'])}s · **Range:** {fmt(s['castrange'])}"]
    en, refs = spell_text(s, d, "en")
    ru, _ = spell_text(s, d, "ru")
    if en:
        o.append(f"\n**EN:** {en}")
    if ru and ru != en:
        o.append(f"\n**RU:** {ru}")
    if refs:
        o.append("\n_Numbers are raw base values from spells.xml (damage before item-power scaling)._")
    if refs and verbose:
        o.append(table([(i, t, v) for i, (t, v) in enumerate(refs)], ["#", "tag", "value"]))
    items = q("SELECT DISTINCT s.item_id FROM item_spells s WHERE s.spell_id=? LIMIT 40", sid)
    if items:
        o.append("\n### Available on items\n" + ", ".join(label(r["item_id"]) for r in items))
    if raw:
        o.append("\n```json\n" + json.dumps(d, ensure_ascii=False, indent=1) + "\n```")
    return "\n".join(o)


# ------------------------------------------------------------------ zones / text / raw
def zone(query, limit=30):
    rows = q("SELECT c.* FROM clusters_fts f JOIN clusters c ON c.idx=f.idx WHERE clusters_fts MATCH ? LIMIT ?", fts_query(query), limit)
    return table([tuple(r) for r in rows], ["index", "name", "cluster file", "type", "biome", "tier", "flags"]) + \
        ("\n\n_types: CTY city, WRL open world, DNG dungeon, RDS roads of Avalon, ISL island, HEL hellgate, EXP expedition, TNL tunnel; "
         "biome: SW swamp, FO forest, HL highland, ST steppe, MO mountain; flags: ROY royal, BLK black zone, KPR/MOR/UND/HER/AVA mob factions._")


def loc(text=None, key=None, limit=15):
    if key:
        r = q1("SELECT all_json FROM loc WHERE key=? OR key=?", key, "@" + key.lstrip("@"))
        if not r:
            raise AOError(f"No localization key {key}")
        return table(list(json.loads(r["all_json"]).items()), ["lang", "text"])
    rows = q("SELECT l.key, l.en, l.ru FROM loc_fts f JOIN loc l ON l.rowid=f.rowid WHERE loc_fts MATCH ? ORDER BY bm25(loc_fts, 2, 5, 5) LIMIT ?",
             fts_query(text or ""), limit)
    return "\n".join(f"- `{r['key']}`\n  - EN: {r['en']}\n  - RU: {r['ru']}" for r in rows) or "Nothing found"


def files():
    return table([tuple(r) for r in q("SELECT file, COUNT(*) n FROM docs GROUP BY file ORDER BY n DESC")], ["file", "records"])


def doc(file, key=None, limit=5, keys_only=False, max_chars=8000):
    if key:
        rows = q("SELECT * FROM docs WHERE file LIKE ? AND (key=? OR key LIKE ?) LIMIT ?", f"%{file}%", key, key, limit)
    else:
        rows = q("SELECT * FROM docs WHERE file LIKE ? LIMIT ?", f"%{file}%", limit)
    if not rows:
        raise AOError("No records. Use files() for file names; key accepts SQL LIKE patterns (%).")
    if keys_only:
        return "\n".join(f"{r['file']}\t{r['path']}\t{r['key']}" for r in rows)
    return "\n\n".join(f"### {r['file']} :: {r['path']} :: {r['key']}\n```json\n"
                       f"{json.dumps(json.loads(r['json']), ensure_ascii=False, indent=1)[:max_chars]}\n```" for r in rows)


def sql(query, limit=200):
    if not re.match(r"^\s*(SELECT|WITH|PRAGMA\s+table_info)\b", query, re.I):
        raise AOError("Only read-only SELECT / WITH queries are allowed")
    cur = connect().execute(query)
    hdr = [c[0] for c in cur.description] if cur.description else []
    rows = cur.fetchmany(limit)
    return table([tuple(r) for r in rows], hdr) + (f"\n\n_(first {limit} rows)_" if len(rows) == limit else "")


def schema():
    rows = q("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE '%fts_%' AND sql IS NOT NULL")
    return "\n".join(f"- {r['sql']}" for r in rows)


def info():
    o = [f"- {r['k']}: {r['v']}" for r in q("SELECT * FROM meta")]
    o += [f"- {t}: {q1(f'SELECT COUNT(*) FROM {t}')[0]}" for t in ["items", "recipes", "spells", "mobs", "loot", "clusters", "loc", "docs"]]
    return "\n".join(o)


# ------------------------------------------------------------------ html cards
def html_cards(items, out):
    cards = []
    for iid in (resolve_item(x) for x in items):
        it = q1("SELECT * FROM items WHERE id=?", iid)
        d = json.loads(it["json"])
        stats = "".join(f"<tr><td>{H.escape(k)}</td><td>{H.escape(str(d['@' + k]))}</td></tr>" for k in STAT_KEYS if "@" + k in d)
        rec = "".join("<div class=rec>" + "".join(f"<span class=res title='{H.escape(x)}'><img src='{ICON.format(x)}?size=48' loading=lazy>"
                                                  f"<b>{c}</b></span>" for x, c, _ in r["res"]) + "</div>" for r in recipes_of(iid)[:2])
        sp = q("SELECT s.spell_id, sp.name_en FROM item_spells s LEFT JOIN spells sp ON sp.id=s.spell_id WHERE s.item_id=?", it["base_id"])
        sps = "".join(f"<img class=sp src='{SPELL_ICON.format(s['spell_id'])}' title='{H.escape(s['name_en'] or s['spell_id'])}' loading=lazy>" for s in sp)
        cards.append(f"<div class=card><div class=head><img src='{ICON.format(iid)}?size=128'><div><h2>{H.escape(it['name_en'] or iid)}</h2>"
                     f"<div class=ru>{H.escape(it['name_ru'] or '')}</div><code>{iid}</code> · T{it['tier']}.{it['enchant']}</div></div>"
                     f"<p>{H.escape(it['desc_en'] or '')}</p><table>{stats}</table>{('<h3>Recipe</h3>' + rec) if rec else ''}"
                     f"{('<h3>Spells</h3>' + sps) if sps else ''}</div>")
    page = ("<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>Albion Items</title><style>"
            ":root{--bg:#f6f4ef;--fg:#222;--card:#fff;--mut:#777;--line:#e4e0d6}@media (prefers-color-scheme:dark){:root{--bg:#16181c;--fg:#e8e6e1;"
            "--card:#202329;--mut:#999;--line:#333}}body{background:var(--bg);color:var(--fg);font:14px system-ui;margin:0;padding:16px;display:flex;"
            "flex-wrap:wrap;gap:16px}.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;width:min(380px,100%);"
            "box-sizing:border-box}.head{display:flex;gap:10px;align-items:center}.head img{width:96px}h2{margin:0;font-size:18px}.ru{color:var(--mut)}"
            "table{width:100%;border-collapse:collapse;font-size:13px}td{border-top:1px solid var(--line);padding:3px}td:last-child{text-align:right}"
            ".rec{display:flex;gap:6px;flex-wrap:wrap}.res{position:relative}.res img{width:48px}.res b{position:absolute;right:2px;bottom:2px;"
            "font-size:11px;background:#000a;color:#fff;padding:0 3px;border-radius:3px}.sp{width:40px;margin:2px;border-radius:6px}code{font-size:12px}"
            "</style>" + "".join(cards))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(page)
    return f"wrote {out} ({len(cards)} cards)"
