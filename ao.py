#!/usr/bin/env python3
"""ao — query tool over the Albion Online knowledge base built by build.py.

Run `ao.py -h` or `ao.py <command> -h`. Item / mob / spell arguments accept an ID
(T4_MAIN_SWORD, T4_MAIN_SWORD@2), a name in EN/RU ("Broadsword", "Палаш"), and an
optional tier prefix ("T6.1 broadsword", "8.3 палаш").
"""
import argparse, json, os, re, signal, sqlite3, sys, urllib.request, urllib.parse, html as H
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.environ.get("AO_DB", os.path.join(HERE, "ao.db"))
ICON = "https://render.albiononline.com/v1/item/{}.png"
SPELL_ICON = "https://render.albiononline.com/v1/spell/{}.png"
PRICE_API = "https://{srv}.albion-online-data.com/api/v2/stats/prices/{ids}.json"
CITIES = ["Caerleon", "Bridgewatch", "Fort Sterling", "Lymhurst", "Martlock", "Thetford", "Brecilien", "Black Market"]
TIER_NAMES = {1: "Beginner", 2: "Novice", 3: "Journeyman", 4: "Adept", 5: "Expert", 6: "Master", 7: "Grandmaster", 8: "Elder"}

con = None


def db():
    global con
    if con is None:
        if not os.path.exists(DB):
            sys.exit(f"DB not found: {DB}. Run: python3 {HERE}/build.py")
        con = sqlite3.connect(DB)
        con.row_factory = sqlite3.Row
    return con


def q(sql, *a):
    return db().execute(sql, a).fetchall()


def q1(sql, *a):
    return db().execute(sql, a).fetchone()


def fts_query(text):
    """Turn free text into a safe FTS5 query (AND of prefix tokens)."""
    toks = re.findall(r"[\w@]+", text, re.U)
    toks = [t.replace("@", " ") for t in toks]
    toks = [p for t in toks for p in t.split()]
    return " ".join(f'"{t}"*' for t in toks) if toks else '""'


def fmt(v):
    if isinstance(v, float):
        return f"{v:g}"
    return "" if v is None else str(v)


def table(rows, headers):
    if not rows:
        return "_(empty)_"
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for r in rows:
        out.append("| " + " | ".join(fmt(x).replace("|", "\\|").replace("\n", " ") for x in r) + " |")
    return "\n".join(out)


def pr(*a):
    print(*a)


def lang_name(row):
    return row["name_ru"] if ARGS.lang == "ru" and row["name_ru"] else row["name_en"]


def label(iid):
    r = q1("SELECT name_en, name_ru, tier, enchant FROM items WHERE id=?", iid)
    if not r:
        return f"`{iid}`"
    n = lang_name(r) or "?"
    t = f" T{r['tier']}.{r['enchant']}" if r["tier"] else ""
    return f"{n}{t} (`{iid}`)"


# ------------------------------------------------------------------ resolvers
def split_tier(text):
    m = re.match(r"^\s*[TtТт]?(\d)(?:[.@](\d))?\s+(.+)$", text)
    if m:
        return int(m.group(1)), int(m.group(2) or 0), m.group(3)
    return None, None, text


def resolve_item(text, many=False):
    text = text.strip()
    r = q1("SELECT id FROM items WHERE id=?", text) or q1("SELECT id FROM items WHERE upper(id)=upper(?)", text)
    if r:
        return [r["id"]] if many else r["id"]
    tier, ench, name = split_tier(text)
    cond, args = "", []
    if tier:
        cond, args = " AND i.tier=? AND i.enchant=?", [tier, ench]
    rows = q(f"SELECT i.id FROM items i WHERE (lower(i.name_en)=lower(?) OR lower(i.name_ru)=lower(?)){cond} ORDER BY i.enchant, i.tier, length(i.id)",
             name, name, *args)
    if not rows:
        rows = q(f"SELECT i.id FROM items_fts f JOIN items i ON i.id=f.id WHERE items_fts MATCH ?{cond} ORDER BY i.enchant, bm25(items_fts, 5, 10, 10, 1, 1, 1), length(i.id) LIMIT 50",
                 fts_query(name), *args)
    if not rows and tier:
        return resolve_item(name, many)
    if not rows:
        return [] if many else None
    return [r["id"] for r in rows] if many else rows[0]["id"]


def resolve_generic(table_, text):
    r = q1(f"SELECT id FROM {table_} WHERE id=?", text) or q1(f"SELECT id FROM {table_} WHERE upper(id)=upper(?)", text)
    if r:
        return r["id"]
    r = q1(f"SELECT id FROM {table_} WHERE lower(name_en)=lower(?) OR lower(name_ru)=lower(?) ORDER BY length(id)", text, text)
    if r:
        return r["id"]
    r = q1(f"SELECT t.id FROM {table_}_fts f JOIN {table_} t ON t.id=f.id WHERE {table_}_fts MATCH ? ORDER BY bm25({table_}_fts), length(t.id) LIMIT 1",
           fts_query(text))
    return r["id"] if r else None


# ------------------------------------------------------------------ search
def cmd_search(a):
    text = " ".join(a.query)
    fq = fts_query(text)
    n = a.limit
    sections = []
    want = set(a.type.split(",")) if a.type else {"items", "spells", "mobs", "zones", "loc", "docs"}
    if "items" in want:
        rows = q("SELECT i.id, i.name_en, i.name_ru, i.tier, i.kind, i.shopcat||'/'||COALESCE(i.sub1,'') FROM items_fts f JOIN items i ON i.id=f.id "
                 "WHERE items_fts MATCH ? AND i.enchant=0 ORDER BY bm25(items_fts, 5, 10, 10, 1, 1, 1) LIMIT ?", fq, n)
        sections.append(("Items", rows, ["id", "name", "ru", "T", "kind", "category"]))
    if "spells" in want:
        rows = q("SELECT s.id, s.name_en, s.name_ru, s.kind, s.category, substr(replace(s.desc_en, char(10), ' '),1,90) FROM spells_fts f JOIN spells s ON s.id=f.id "
                 "WHERE spells_fts MATCH ? ORDER BY (s.name_en IS NULL), bm25(spells_fts, 5, 10, 10, 1, 1) LIMIT ?", fq, n)
        sections.append(("Spells", rows, ["id", "name", "ru", "kind", "cat", "desc"]))
    if "mobs" in want:
        rows = q("SELECT m.id, m.name_en, m.name_ru, m.tier, m.category, m.faction, m.hp FROM mobs_fts f JOIN mobs m ON m.id=f.id "
                 "WHERE mobs_fts MATCH ? ORDER BY bm25(mobs_fts, 5, 10, 10, 1, 1) LIMIT ?", fq, n)
        sections.append(("Mobs", rows, ["id", "name", "ru", "T", "cat", "faction", "HP"]))
    if "zones" in want:
        rows = q("SELECT c.idx, c.name, c.type, c.biome, c.tier, c.zone FROM clusters_fts f JOIN clusters c ON c.idx=f.idx "
                 "WHERE clusters_fts MATCH ? ORDER BY bm25(clusters_fts) LIMIT ?", fq, n)
        sections.append(("Zones", rows, ["index", "name", "type", "biome", "T", "zone"]))
    if "loc" in want:
        rows = q("SELECT l.key, substr(replace(l.en,char(10),' '),1,100), substr(replace(l.ru,char(10),' '),1,100) FROM loc_fts f JOIN loc l ON l.rowid=f.rowid "
                 "WHERE loc_fts MATCH ? ORDER BY bm25(loc_fts, 2, 5, 5) LIMIT ?", fq, n)
        sections.append(("Localization strings", rows, ["key", "en", "ru"]))
    if "docs" in want:
        rows = q("SELECT d.file, d.key, d.path, snippet(docs_fts, 2, '**', '**', '…', 12) FROM docs_fts f JOIN docs d ON d.id=f.rowid "
                 "WHERE docs_fts MATCH ? ORDER BY bm25(docs_fts, 1, 5, 1) LIMIT ?", fq, n)
        sections.append(("Raw game data (all files)", rows, ["file", "key", "path", "snippet"]))
    for title, rows, hdr in sections:
        if rows:
            pr(f"### {title}\n" + table([tuple(r) for r in rows], hdr) + "\n")
    if not any(s[1] for s in sections):
        pr(f"Nothing found for: {text}")


# ------------------------------------------------------------------ items
STAT_KEYS = ["itempower", "abilitypower", "attackdamage", "attackspeed", "attackrange", "hitpointsmax", "hitpointsregenerationbonus",
             "energymax", "energyregenerationbonus", "physicalarmor", "magicresistance", "crowdcontrolresistance", "healmodifier",
             "physicalspelldamagebonus", "magicspelldamagebonus", "durability", "weight", "maxstacksize", "itemvalue", "nutrition",
             "maxload", "movespeedbonus", "mountedbuff", "mounthitpointsmax", "mounttime", "focusfireprotectionpenetration",
             "activespellslots", "passivespellslots", "twohanded", "slottype", "attacktype", "maxqualitylevel", "tradable",
             "craftingcategory", "fishingfame", "famebonus", "maxfame", "consumespell", "destinycraftfamefactor"]


def recipes_of(iid):
    out = defaultdict(lambda: {"res": []})
    for r in q("SELECT * FROM recipes WHERE item_id=? ORDER BY recipe_no", iid):
        d = out[r["recipe_no"]]
        d.update(silver=r["silver"], time=r["time"], focus=r["focus"], amount=r["amount"])
        if r["resource_id"]:
            d["res"].append((r["resource_id"], r["count"], r["maxreturn"]))
    return [out[k] for k in sorted(out)]


def drop_sources(iid, limit=25):
    """Loot lists containing item (walk up references), and mobs referencing them."""
    lists = {}
    frontier = [(r["list"], r["chance"]) for r in q("SELECT list, chance FROM loot WHERE target=? AND kind='item'", iid)]
    depth = 0
    while frontier and depth < 6:
        nxt = []
        for name, ch in frontier:
            if name in lists:
                continue
            lists[name] = depth
            for r in q("SELECT list, chance FROM loot WHERE target=? AND kind='ref'", name):
                nxt.append((r["list"], r["chance"]))
        frontier, depth = nxt, depth + 1
    mobs = []
    if lists:
        ph = ",".join("?" * len(lists))
        mobs = q(f"SELECT ml.mob_id, m.name_en, m.name_ru, m.tier, ml.lootlist, ml.chance FROM mob_loot ml LEFT JOIN mobs m ON m.id=ml.mob_id "
                 f"WHERE ml.lootlist IN ({ph}) ORDER BY ml.chance DESC LIMIT ?", *lists.keys(), limit)
    return lists, mobs


def cmd_item(a):
    ids = resolve_item(" ".join(a.item), many=True)
    if not ids:
        sys.exit("Item not found. Try: ao.py search <text>")
    iid = ids[0]
    it = q1("SELECT * FROM items WHERE id=?", iid)
    data = json.loads(it["json"])
    names = json.loads(it["names_json"] or "{}")
    pr(f"## {it['name_en'] or iid}  /  {it['name_ru'] or ''}")
    pr(f"![{iid}]({ICON.format(iid)}?size=128)\n")
    pr(f"- **ID:** `{iid}`  (base `{it['base_id']}`, kind `{it['kind']}`)")
    pr(f"- **Tier:** {it['tier']}.{it['enchant']}  ({TIER_NAMES.get(it['tier'] or 0, '')})")
    pr(f"- **Category:** {it['shopcat']} / {it['sub1']} / {it['sub2'] or ''} {('/ ' + it['sub3']) if it['sub3'] else ''}")
    if it["desc_en"]:
        pr(f"- **Description:** {it['desc_en']}")
    if it["desc_ru"]:
        pr(f"- **Описание:** {it['desc_ru']}")
    pr(f"- **Icon:** {ICON.format(iid)}  ·  quality variants: `?quality=1..5`")
    stats = [(k, data["@" + k]) for k in STAT_KEYS if "@" + k in data]
    if stats:
        pr("\n### Stats\n" + table(stats, ["stat", "value"]))
    if a.all_langs and names:
        pr("\n### Names\n" + table(list(names.items()), ["lang", "name"]))
    recs = recipes_of(iid)
    for n, r in enumerate(recs):
        pr(f"\n### Recipe {n + 1}" + (f" (crafts ×{r['amount']})" if (r.get('amount') or 1) > 1 else "") +
           f" — silver {fmt(r['silver'])}, focus {fmt(r['focus'])}, time {fmt(r['time'])}")
        pr(table([(label(x), c, mr or "") for x, c, mr in r["res"]], ["resource", "count", "max return"]))
    ups = q("SELECT resource_id, count FROM upgrades WHERE item_id=?", iid)
    if ups:
        pr("\n### Upgrade to next enchant\n" + table([(label(u["resource_id"]), u["count"]) for u in ups], ["resource", "count"]))
    sp = q("SELECT s.spell_id, s.slots, s.tag, sp.name_en, sp.name_ru, sp.kind FROM item_spells s LEFT JOIN spells sp ON sp.id=s.spell_id "
           "WHERE s.item_id=?", it["base_id"])
    if sp:
        pr("\n### Spells (craftingspelllist)\n" + table([(r["spell_id"], r["name_en"], r["name_ru"], r["kind"], r["slots"] or "passive", r["tag"] or "") for r in sp],
                                                       ["spell", "name", "ru", "kind", "slot(s)", "tag"]))
    used = q("SELECT DISTINCT item_id FROM recipes WHERE resource_id=? LIMIT 31", iid)
    if used:
        pr(f"\n### Used in ({'30+' if len(used) > 30 else len(used)} recipes)\n" + ", ".join(label(u["item_id"]) for u in used[:30]))
    lists, mobs = drop_sources(iid)
    if lists:
        pr(f"\n### Drops from loot lists ({len(lists)})\n" + ", ".join(f"`{k}`" for k in list(lists)[:30]))
    if mobs:
        pr("\n### Mobs (top by chance)\n" + table([(m["mob_id"], m["name_en"], m["tier"], m["lootlist"], m["chance"]) for m in mobs],
                                                 ["mob", "name", "T", "loot list", "chance"]))
    if len(ids) > 1:
        pr("\n_Other matches:_ " + ", ".join(f"`{x}`" for x in ids[1:15]))
    if a.json:
        pr("\n### Raw\n```json\n" + json.dumps(data, ensure_ascii=False, indent=1) + "\n```")


def cmd_list(a):
    cond, args = ["1=1"], []
    for col, val in (("shopcat", a.cat), ("sub1", a.sub), ("sub2", a.sub2), ("kind", a.kind), ("slot", a.slot), ("craftcat", a.craftcat)):
        if val:
            cond.append(f"{col} LIKE ?")
            args.append(val)
    if a.tier is not None:
        cond.append("tier=?"); args.append(a.tier)
    cond.append("enchant=?"); args.append(a.enchant)
    if a.name:
        cond.append("(name_en LIKE ? OR name_ru LIKE ?)"); args += [f"%{a.name}%"] * 2
    order = {"ip": "itempower DESC", "tier": "tier, id", "name": "name_en", "id": "id"}[a.sort]
    rows = q(f"SELECT id, name_en, name_ru, tier, enchant, shopcat, sub1, sub2, itempower FROM items WHERE {' AND '.join(cond)} ORDER BY {order} LIMIT ?", *args, a.limit)
    pr(table([tuple(r) for r in rows], ["id", "name", "ru", "T", "ench", "cat", "sub1", "sub2", "IP"]))
    pr(f"\n{len(rows)} rows")


def cmd_categories(a):
    rows = q("SELECT shopcat, sub1, COUNT(*) FROM items WHERE enchant=0 GROUP BY 1, 2 ORDER BY 1, 2")
    pr(table([tuple(r) for r in rows], ["shopcat", "sub1", "items"]))


def cmd_compare(a):
    ids = [resolve_item(x) for x in a.items]
    if None in ids:
        sys.exit(f"Not found: {a.items[ids.index(None)]}")
    datas = [json.loads(q1("SELECT json FROM items WHERE id=?", i)["json"]) for i in ids]
    keys = [k for k in STAT_KEYS if any("@" + k in d for d in datas)]
    rows = [(k, *[d.get("@" + k, "") for d in datas]) for k in keys]
    pr(table(rows, ["stat"] + [label(i) for i in ids]))


def craft_tree(iid, qty, depth, maxdepth, totals, lines, recipe_no=0):
    recs = recipes_of(iid)
    pad = "  " * depth
    lines.append(f"{pad}- {qty:g} × {label(iid)}")
    leaf = False
    if not ARGS.full and depth > 0:
        it = q1("SELECT shopcat, sub1 FROM items WHERE id=?", iid)
        leaf = bool(it) and (it["shopcat"] == "artefacts" or it["sub1"] == "resources")
    if not recs or depth >= maxdepth or leaf:
        totals[iid] += qty
        return
    r = recs[min(recipe_no, len(recs) - 1)]
    crafts = qty / (r.get("amount") or 1)
    if not r["res"]:
        totals[iid] += qty
        return
    for rid, cnt, _ in r["res"]:
        if rid == iid:
            continue
        craft_tree(rid, crafts * (cnt or 0), depth + 1, maxdepth, totals, lines)


def cmd_recipe(a):
    iid = resolve_item(" ".join(a.item))
    if not iid:
        sys.exit("Item not found")
    recs = recipes_of(iid)
    if not recs:
        sys.exit(f"{label(iid)} has no crafting recipe")
    totals, lines = defaultdict(float), []
    craft_tree(iid, a.qty, 0, a.depth, totals, lines, a.recipe)
    pr(f"## Crafting tree: {label(iid)}  ×{a.qty:g}\n")
    if len(recs) > 1:
        pr(f"_{len(recs)} alternative recipes; showing #{a.recipe + 1} (use --recipe N)_\n")
    pr("\n".join(lines))
    rr = recs[min(a.recipe, len(recs) - 1)]
    pr(f"\nSilver per craft: {fmt(rr['silver'])} · focus: {fmt(rr['focus'])} · time: {fmt(rr['time'])}")
    pr("\n### Total base materials (no return rate)\n" + table(sorted(((label(k), round(v, 2)) for k, v in totals.items()), key=lambda x: -x[1]),
                                                             ["material", "qty"]))
    if a.rrr:
        pr(f"\n_With resource return rate {a.rrr}%: multiply returnable materials by {1 - a.rrr / 100:.3f}_")


def cmd_usedin(a):
    iid = resolve_item(" ".join(a.item))
    rows = q("SELECT DISTINCT r.item_id, r.count, i.name_en, i.name_ru, i.tier, i.enchant FROM recipes r JOIN items i ON i.id=r.item_id "
             "WHERE r.resource_id=? ORDER BY i.tier, i.id LIMIT ?", iid, a.limit)
    pr(f"## {label(iid)} is used in {len(rows)} recipes\n")
    pr(table([tuple(r) for r in rows], ["item", "count", "name", "ru", "T", "ench"]))


def cmd_drops(a):
    iid = resolve_item(" ".join(a.item))
    lists, mobs = drop_sources(iid, a.limit)
    pr(f"## Where {label(iid)} drops\n")
    direct = q("SELECT list, amount, chance FROM loot WHERE target=? AND kind='item'", iid)
    pr("### Direct loot lists\n" + table([tuple(r) for r in direct], ["list", "amount", "chance/weight"]))
    pr(f"\n### All lists incl. parents ({len(lists)})\n" + ", ".join(f"`{k}`(d{v})" for k, v in list(lists.items())[:40]) + (" …" if len(lists) > 40 else ""))
    pr("\n### Mobs\n" + table([(m["mob_id"], m["name_en"], m["name_ru"], m["tier"], m["lootlist"], m["chance"]) for m in mobs],
                              ["mob", "name", "ru", "T", "list", "chance"]))
    other = q("SELECT d.file, d.key, d.path FROM docs_fts f JOIN docs d ON d.id=f.rowid WHERE docs_fts MATCH ? AND d.file NOT IN ('items.json','loot.json') LIMIT 20",
              f'"{iid}"')
    if other:
        pr("\n### Mentioned in other game files\n" + table([tuple(r) for r in other], ["file", "key", "path"]))


# ------------------------------------------------------------------ loot
def cmd_loot(a):
    name = a.list
    if not q1("SELECT 1 FROM loot WHERE list=?", name):
        cand = q("SELECT DISTINCT list FROM loot WHERE list LIKE ? LIMIT 30", f"%{name}%")
        sys.exit("Unknown list. Candidates: " + ", ".join(r["list"] for r in cand))

    def expand(lst, depth, mult):
        for r in q("SELECT * FROM loot WHERE list=?", lst):
            pad = "  " * depth
            ch = f" chance={fmt(r['chance'])}" if r["chance"] is not None else ""
            if r["kind"] == "ref":
                pr(f"{pad}- ↳ list `{r['target']}`{ch}")
                if depth < a.depth:
                    expand(r["target"], depth + 1, mult)
            else:
                pr(f"{pad}- {label(r['target'])} ×{r['amount'] or 1}{ch}")

    pr(f"## Loot list `{name}`\n")
    expand(name, 0, 1)
    mobs = q("SELECT mob_id, chance FROM mob_loot WHERE lootlist=? LIMIT 20", name)
    if mobs:
        pr("\nUsed by mobs: " + ", ".join(f"`{m['mob_id']}`({fmt(m['chance'])})" for m in mobs))


# ------------------------------------------------------------------ mobs
def cmd_mob(a):
    mid = resolve_generic("mobs", " ".join(a.mob))
    if not mid:
        sys.exit("Mob not found")
    m = q1("SELECT * FROM mobs WHERE id=?", mid)
    d = json.loads(m["json"])
    pr(f"## {m['name_en'] or mid} / {m['name_ru'] or ''}\n\n- **ID:** `{mid}` · tier {m['tier']} · {m['typecat']} · category `{m['category']}` · faction `{m['faction']}`")
    keys = ["hitpointsmax", "hitpointsregeneration", "attackdamage", "attackspeed", "attackrange", "attacktype", "physicalarmor", "magicresistance",
            "crowdcontrolresistance", "movespeed", "fame", "abilitypower", "aggroradius", "respawntimesecondsmin", "respawntimesecondsmax",
            "npchostility", "lootprefab", "dangerstate"]
    pr("\n" + table([(k, d["@" + k]) for k in keys if "@" + k in d], ["stat", "value"]))
    loot = q("SELECT lootlist, chance FROM mob_loot WHERE mob_id=? ORDER BY chance DESC", mid)
    if loot:
        pr("\n### Loot lists\n" + table([tuple(r) for r in loot], ["list", "chance"]))
        pr("_Expand with: ao.py loot <list>_")
    spells = set(re.findall(r'"@(?:name|uniquename|spell)": "([A-Z0-9_]+)"', json.dumps(d.get("Spells") or d.get("spells") or {})))
    if spells:
        pr("\n### Spells\n" + ", ".join(f"`{s}`" for s in sorted(spells)))
    if a.json:
        pr("\n```json\n" + json.dumps(d, ensure_ascii=False, indent=1) + "\n```")


# ------------------------------------------------------------------ spells
def get_path(obj, path):
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
            if nxt is None:  # search one level deeper
                for v in cur.values():
                    if isinstance(v, dict) and (k in v or "@" + k in v):
                        nxt = v.get("@" + k, v.get(k)); break
        if i is not None:
            lst = nxt if isinstance(nxt, list) else [nxt]
            nxt = lst[int(i)] if nxt is not None and int(i) < len(lst) else None
        elif isinstance(nxt, list):
            nxt = nxt[0]
        cur = nxt
    return cur


def resolve_tag(tag):
    m = re.match(r"^\$\$?([A-Z0-9_]+)\.(.+?)\$$", tag)
    if not m:
        return None
    r = q1("SELECT json FROM spells WHERE id=?", m.group(1))
    if not r:
        return None
    return get_path(json.loads(r["json"]), m.group(2))


def spell_desc(s, d):
    desc = (s["desc_ru"] if ARGS.lang == "ru" and s["desc_ru"] else s["desc_en"]) or ""
    refs = [x.get("@tag") for x in (((d.get("locareferences") or {}).get("description") or {}).get("locareference") or [])] \
        if isinstance(((d.get("locareferences") or {}).get("description") or {}).get("locareference"), list) else \
        [(((d.get("locareferences") or {}).get("description") or {}).get("locareference") or {}).get("@tag")]
    vals = [resolve_tag(t) if t else None for t in refs]
    for i, v in enumerate(vals):
        if v is not None and not isinstance(v, (dict, list)):
            desc = desc.replace("{%d}" % i, f"{v}")
    return re.sub(r"\[/?\w+\]", "", desc), list(zip(refs, vals))


def cmd_spell(a):
    sid = resolve_generic("spells", " ".join(a.spell))
    if not sid:
        sys.exit("Spell not found")
    s = q1("SELECT * FROM spells WHERE id=?", sid)
    d = json.loads(s["json"])
    pr(f"## {s['name_en'] or sid} / {s['name_ru'] or ''}\n\n![{sid}]({SPELL_ICON.format(sid)})\n")
    pr(f"- **ID:** `{sid}` · {s['kind']} · category `{s['category']}` · target `{s['target']}`")
    pr(f"- **Cooldown:** {fmt(s['cooldown'])}s · **Energy:** {fmt(s['energy'])} · **Cast:** {fmt(s['casttime'])}s · **Range:** {fmt(s['castrange'])}")
    desc, refs = spell_desc(s, d)
    if desc:
        pr(f"\n{desc}\n")
    if refs and a.verbose:
        pr("Placeholders (raw values, before item-power scaling):\n" + table([(i, t, v) for i, (t, v) in enumerate(refs)], ["#", "tag", "value"]))
    items = q("SELECT DISTINCT s.item_id, i.name_en, i.tier FROM item_spells s LEFT JOIN items i ON i.id=s.item_id WHERE s.spell_id=? LIMIT 40", sid)
    if items:
        pr("\n### Available on items\n" + ", ".join(label(r["item_id"]) for r in items))
    if a.json:
        pr("\n```json\n" + json.dumps(d, ensure_ascii=False, indent=1) + "\n```")


# ------------------------------------------------------------------ zones / loc / docs
def cmd_zone(a):
    text = " ".join(a.zone)
    rows = q("SELECT c.* FROM clusters_fts f JOIN clusters c ON c.idx=f.idx WHERE clusters_fts MATCH ? LIMIT ?", fts_query(text), a.limit)
    pr(table([tuple(r) for r in rows], ["index", "name", "cluster file", "type", "biome", "tier", "zone/flags"]))
    pr("\n_types: CTY city, WRL open world, DNG dungeon, RDS roads, ISL island, HEL hellgate, EXP expedition, TNL tunnel; "
       "biome: SW swamp, FO forest, HL highland, ST steppe, MO mountain; flags: ROY royal, BLK black zone, KPR/MOR/UND/HER/AVA factions..._")


def cmd_loc(a):
    if a.key:
        r = q1("SELECT all_json FROM loc WHERE key=? OR key=?", a.key, "@" + a.key.lstrip("@"))
        if not r:
            sys.exit("No such key")
        pr(table(list(json.loads(r["all_json"]).items()), ["lang", "text"]))
        return
    rows = q("SELECT l.key, l.en, l.ru FROM loc_fts f JOIN loc l ON l.rowid=f.rowid WHERE loc_fts MATCH ? ORDER BY bm25(loc_fts, 2, 5, 5) LIMIT ?",
             fts_query(" ".join(a.text)), a.limit)
    for r in rows:
        pr(f"- `{r['key']}`\n  - EN: {r['en']}\n  - RU: {r['ru']}")


def cmd_files(a):
    rows = q("SELECT file, COUNT(*) n FROM docs GROUP BY file ORDER BY n DESC")
    pr(table([tuple(r) for r in rows], ["file", "records"]))


def cmd_doc(a):
    if a.key:
        rows = q("SELECT * FROM docs WHERE file LIKE ? AND (key=? OR key LIKE ?) LIMIT ?", f"%{a.file}%", a.key, a.key, a.limit)
    else:
        rows = q("SELECT * FROM docs WHERE file LIKE ? LIMIT ?", f"%{a.file}%", a.limit)
    if a.keys:
        pr("\n".join(f"{r['file']}\t{r['path']}\t{r['key']}" for r in rows))
        return
    for r in rows:
        pr(f"### {r['file']} :: {r['path']} :: {r['key']}\n```json\n{json.dumps(json.loads(r['json']), ensure_ascii=False, indent=1)[:a.max]}\n```")


def cmd_sql(a):
    cur = db().execute(" ".join(a.sql))
    hdr = [c[0] for c in cur.description] if cur.description else []
    rows = cur.fetchmany(a.limit)
    pr(table([tuple(r) for r in rows], hdr))


def cmd_info(a):
    for r in q("SELECT * FROM meta"):
        pr(f"- {r['k']}: {r['v']}")
    for t in ["items", "recipes", "spells", "mobs", "loot", "clusters", "loc", "docs"]:
        pr(f"- {t}: {q1(f'SELECT COUNT(*) FROM {t}')[0]}")


# ------------------------------------------------------------------ live prices
def cmd_price(a):
    ids = []
    for x in a.items:
        r = resolve_item(x)
        if not r:
            sys.exit(f"Not found: {x}")
        ids.append(r)
    url = PRICE_API.format(srv=a.server, ids=",".join(ids))
    params = {"qualities": a.quality}
    if a.cities:
        params["locations"] = a.cities
    url += "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as resp:
        data = json.load(resp)
    rows = [(label(d["item_id"]), d["city"], d["quality"], d["sell_price_min"] or "", d["sell_price_min_date"][:16].replace("T", " "),
             d["buy_price_max"] or "", d["buy_price_max_date"][:16].replace("T", " ") if d["buy_price_max"] else "") for d in data if d["sell_price_min"] or d["buy_price_max"]]
    pr(f"## Market prices ({a.server}, source: albion-online-data.com, crowd-sourced)\n")
    pr(table(rows, ["item", "city", "q", "sell min", "updated", "buy max", "updated"]))


# ------------------------------------------------------------------ html cards
def cmd_html(a):
    ids = [resolve_item(x) for x in a.items]
    cards = []
    for iid in filter(None, ids):
        it = q1("SELECT * FROM items WHERE id=?", iid)
        d = json.loads(it["json"])
        stats = "".join(f"<tr><td>{H.escape(k)}</td><td>{H.escape(str(d['@' + k]))}</td></tr>" for k in STAT_KEYS if "@" + k in d)
        rec = ""
        for r in recipes_of(iid)[:2]:
            rec += "<div class=rec>" + "".join(
                f"<span class=res title='{H.escape(x)}'><img src='{ICON.format(x)}?size=48' loading=lazy><b>{c}</b></span>" for x, c, _ in r["res"]) + "</div>"
        sp = q("SELECT s.spell_id, sp.name_en FROM item_spells s LEFT JOIN spells sp ON sp.id=s.spell_id WHERE s.item_id=?", it["base_id"])
        sps = "".join(f"<img class=sp src='{SPELL_ICON.format(s['spell_id'])}' title='{H.escape(s['name_en'] or s['spell_id'])}' loading=lazy>" for s in sp)
        cards.append(f"""<div class=card><div class=head><img src='{ICON.format(iid)}?size=128'><div><h2>{H.escape(it['name_en'] or iid)}</h2>
<div class=ru>{H.escape(it['name_ru'] or '')}</div><code>{iid}</code> · T{it['tier']}.{it['enchant']}</div></div>
<p>{H.escape(it['desc_en'] or '')}</p><table>{stats}</table>{('<h3>Recipe</h3>' + rec) if rec else ''}{('<h3>Spells</h3>' + sps) if sps else ''}</div>""")
    page = f"""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>Albion Items</title>
<style>:root{{--bg:#f6f4ef;--fg:#222;--card:#fff;--mut:#777;--line:#e4e0d6}}@media (prefers-color-scheme:dark){{:root{{--bg:#16181c;--fg:#e8e6e1;--card:#202329;--mut:#999;--line:#333}}}}
body{{background:var(--bg);color:var(--fg);font:14px system-ui;margin:0;padding:16px;display:flex;flex-wrap:wrap;gap:16px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;width:min(380px,100%);box-sizing:border-box}}
.head{{display:flex;gap:10px;align-items:center}}.head img{{width:96px}}h2{{margin:0;font-size:18px}}.ru{{color:var(--mut)}}
table{{width:100%;border-collapse:collapse;font-size:13px}}td{{border-top:1px solid var(--line);padding:3px}}td:last-child{{text-align:right}}
.rec{{display:flex;gap:6px;flex-wrap:wrap}}.res{{position:relative}}.res img{{width:48px}}.res b{{position:absolute;right:2px;bottom:2px;font-size:11px;background:#000a;color:#fff;padding:0 3px;border-radius:3px}}
.sp{{width:40px;margin:2px;border-radius:6px}}code{{font-size:12px}}</style>{''.join(cards)}"""
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(page)
    pr(f"wrote {a.out} ({len(cards)} cards)")


# ------------------------------------------------------------------ main
def main():
    global ARGS
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lang", choices=["en", "ru"], default="en", help="preferred display language for names")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn, help_):
        p = sub.add_parser(name, help=help_)
        p.set_defaults(fn=fn)
        return p

    p = add("search", cmd_search, "full-text search across items, spells, mobs, zones, localization and all raw files")
    p.add_argument("query", nargs="+"); p.add_argument("-n", "--limit", type=int, default=10)
    p.add_argument("-t", "--type", help="comma list: items,spells,mobs,zones,loc,docs")
    p = add("item", cmd_item, "item card: stats, recipe, spells, usage, drop sources")
    p.add_argument("item", nargs="+"); p.add_argument("--json", action="store_true"); p.add_argument("--all-langs", action="store_true")
    p = add("list", cmd_list, "filter items by category/tier")
    p.add_argument("--cat"); p.add_argument("--sub"); p.add_argument("--sub2"); p.add_argument("--kind"); p.add_argument("--slot")
    p.add_argument("--craftcat"); p.add_argument("--name"); p.add_argument("--tier", type=int); p.add_argument("--enchant", type=int, default=0)
    p.add_argument("--sort", choices=["ip", "tier", "name", "id"], default="tier"); p.add_argument("-n", "--limit", type=int, default=100)
    add("categories", cmd_categories, "list shop categories / subcategories")
    p = add("compare", cmd_compare, "compare stats of several items"); p.add_argument("items", nargs="+")
    p = add("recipe", cmd_recipe, "recursive crafting tree with total materials")
    p.add_argument("item", nargs="+"); p.add_argument("-q", "--qty", type=float, default=1); p.add_argument("-d", "--depth", type=int, default=5)
    p.add_argument("--recipe", type=int, default=0); p.add_argument("--rrr", type=float)
    p.add_argument("--full", action="store_true", help="also expand raw resources/artefacts (transmutation, shard crafting)")
    p = add("usedin", cmd_usedin, "what recipes use this item"); p.add_argument("item", nargs="+"); p.add_argument("-n", "--limit", type=int, default=200)
    p = add("drops", cmd_drops, "where an item drops (loot lists, mobs)"); p.add_argument("item", nargs="+"); p.add_argument("-n", "--limit", type=int, default=40)
    p = add("loot", cmd_loot, "expand a loot list"); p.add_argument("list"); p.add_argument("-d", "--depth", type=int, default=1)
    p = add("mob", cmd_mob, "mob card"); p.add_argument("mob", nargs="+"); p.add_argument("--json", action="store_true")
    p = add("spell", cmd_spell, "spell card"); p.add_argument("spell", nargs="+"); p.add_argument("--json", action="store_true")
    p.add_argument("-v", "--verbose", action="store_true")
    p = add("zone", cmd_zone, "find zones/clusters"); p.add_argument("zone", nargs="+"); p.add_argument("-n", "--limit", type=int, default=30)
    p = add("loc", cmd_loc, "search localization strings (all game text)"); p.add_argument("text", nargs="*")
    p.add_argument("--key"); p.add_argument("-n", "--limit", type=int, default=15)
    add("files", cmd_files, "list indexed game data files")
    p = add("doc", cmd_doc, "show raw records from any game file"); p.add_argument("file"); p.add_argument("key", nargs="?")
    p.add_argument("-n", "--limit", type=int, default=5); p.add_argument("--keys", action="store_true", help="only list keys")
    p.add_argument("--max", type=int, default=8000)
    p = add("sql", cmd_sql, "run raw SQL"); p.add_argument("sql", nargs="+"); p.add_argument("-n", "--limit", type=int, default=200)
    add("info", cmd_info, "database info")
    p = add("price", cmd_price, "live market prices (albion-online-data.com)"); p.add_argument("items", nargs="+")
    p.add_argument("--server", choices=["west", "east", "europe"], default="europe"); p.add_argument("--cities", help="comma list, e.g. Caerleon,Martlock")
    p.add_argument("--quality", default="1")
    p = add("html", cmd_html, "render item cards with icons to an HTML file"); p.add_argument("items", nargs="+"); p.add_argument("-o", "--out", default="cards.html")
    ARGS = ap.parse_args()
    ARGS.fn(ARGS)


if __name__ == "__main__":
    main()
