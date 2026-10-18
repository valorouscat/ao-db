"""Higher-level analysis for general questions: chest value, build cost, killboard meta, official mechanics texts, notes."""
import datetime, functools, glob, json, os, re, sqlite3, time, urllib.request
from collections import Counter, defaultdict
from . import core
from .core import AOError, q, q1, label, money, fmt, table, resolve_item, item_value, ROOT
from . import market

KNOWLEDGE = os.path.join(ROOT, "knowledge")
QUALITY_IP = {1: 0, 2: 20, 3: 40, 4: 60, 5: 100}
EQUIP_SLOTS = ("mainhand", "offhand", "head", "armor", "shoes", "cape", "bag", "mount")


def _aslist(x):
    return x if isinstance(x, list) else ([] if x is None else [x])


# ------------------------------------------------------------------ loot expected value
@functools.lru_cache(maxsize=None)
def _item_id(t, lvl):
    if not lvl:
        return t
    for cand in (f"{t}@{lvl}", f"{t}_LEVEL{lvl}@{lvl}"):
        if q1("SELECT 1 FROM items WHERE id=?", cand):
            return cand
    return f"{t}@{lvl}"


def _p(node):
    """Roll probability of an entry. `chance` is read as a percentage (999 = always); ignored when evaluateChance=false."""
    c = core.num(node.get("@chance"))
    if c is None or node.get("@evaluateChance") == "false":
        return 1.0
    return min(c, 100.0) / 100.0


def _amount(node):
    a = core.num(node.get("@amount"))
    if a is None and node.get("@minamount"):
        a = (core.num(node["@minamount"]) + core.num(node.get("@maxamount") or node["@minamount"])) / 2
    return a or 1.0


class LootEV:
    def __init__(self):
        self.cache = {}

    def raw(self, name):
        if name not in self.cache:
            r = q1("SELECT json FROM loot_raw WHERE name=?", name)
            self.cache[name] = json.loads(r["json"]) if r else None
        return self.cache[name]

    def entry(self, key, node, mult, acc, depth):
        if depth > 14 or mult < 1e-9:
            return
        if key == "Item":
            t = node.get("@type") or node.get("@uniquename")
            if t:
                acc[_item_id(t, int(core.num(node.get("@enchantmentlevel")) or 0))] += mult * _amount(node)
        elif key in ("LootListReference", "LootList"):
            sub = self.raw(node.get("@name"))
            if sub:
                self.all_of(sub, mult, acc, depth + 1)
        elif key == "OR":
            self.one_of(node, mult, acc, depth + 1)
        elif key == "AND":
            self.all_of(node, mult, acc, depth + 1)

    def all_of(self, node, mult, acc, depth=0):
        for key, val in node.items():
            if not key.startswith("@"):
                for ch in _aslist(val):
                    if isinstance(ch, dict):
                        self.entry(key, ch, mult * _p(ch), acc, depth)

    def one_of(self, node, mult, acc, depth):
        entries = [(k, ch) for k, v in node.items() if not k.startswith("@") for ch in _aslist(v) if isinstance(ch, dict)]
        total = sum(core.num(ch.get("@weight")) or 1.0 for _, ch in entries)
        for k, ch in entries:
            self.entry(k, ch, mult * (core.num(ch.get("@weight")) or 1.0) / total, acc, depth)

    def expected(self, listname, mult=1.0):
        acc = defaultdict(float)
        sub = self.raw(listname)
        if sub:
            self.all_of(sub, mult, acc)
        return acc


def _offline_value(iid):
    v = item_value(iid)
    return v or 0.0


def _chest_lists(chest, tier):
    """[(rarity, weight, listname)] for the requested tier."""
    out = []
    states = _aslist((chest.get("RareStates") or {}).get("RareState")) or [{"@state": "-", "@weight": "1", "Loot": chest.get("Loot") or {}}]
    for st in states:
        lootn = st.get("Loot") or {}
        refs = []
        by_tier = _aslist(lootn.get("LootByTier"))
        if by_tier:
            tiers = sorted(by_tier, key=lambda x: core.num(x.get("@tier")) or 0)
            best = [x for x in tiers if (core.num(x.get("@tier")) or 0) <= tier] or tiers[:1]
            refs = _aslist(best[-1].get("LootListReference"))
        refs += _aslist(lootn.get("LootListReference"))
        for r in refs:
            out.append((st.get("@state"), core.num(st.get("@weight")) or 1.0, r.get("@name")))
    return out


def chest_value(query, tier=8, live=False, server="europe", city="Caerleon", top=8):
    rows = q("SELECT * FROM chests WHERE name LIKE ? OR chesttype = ? ORDER BY name", f"%{query}%", query)
    if not rows:
        types = ", ".join(r["chesttype"] for r in q("SELECT DISTINCT chesttype FROM chests WHERE chesttype IS NOT NULL"))
        raise AOError(f"No chests match {query!r}. Chest types: {types}")
    ev = LootEV()
    results, all_items = [], set()
    for ch in rows[:40]:
        d = json.loads(ch["json"])
        lists = _chest_lists(d, tier)
        if not lists:
            continue
        wsum = sum(w for _, w, _ in lists)
        per_state = []
        for state, w, ln in lists:
            exp = ev.expected(ln)
            all_items.update(exp)
            per_state.append((state, w / wsum, ln, exp))
        results.append((ch["name"], ch["chesttype"], d, per_state))
    prices = {}
    if live:
        offline_rank = Counter()
        for _, _, _, ps in results:
            for _, share, _, exp in ps:
                for i, n in exp.items():
                    offline_rank[i] += share * n * (_offline_value(i) or 1)
        cands = [i for i, _ in offline_rank.most_common(150)]
        prices = market.price_map(cands, server, city, use_history=False)

    def val(i):
        if live:
            p = prices.get(i, (None,))[0]
            return p or 0.0
        return _offline_value(i)

    o = [f"## Chest value: `{query}` at tier {tier}", "",
         f"Value basis: **{'live market prices, ' + city + ' (' + server + ')' if live else 'game item value (offline proxy: crafting value, not market price)'}**. "
         "Expected items per chest = Σ (roll chance × amount) through nested loot lists (OR = weighted pick).", ""]
    summary = []
    for name, ctype, d, ps in results:
        total = sum(share * sum(n * val(i) for i, n in exp.items()) for _, share, _, exp in ps)
        nitems = sum(share * sum(exp.values()) for _, share, _, exp in ps)
        summary.append((name, ctype, total, nitems, d.get("@triggermobspawn") == "true", ps))
    summary.sort(key=lambda r: -r[2])
    best = summary[0][2] if summary and summary[0][2] else 1
    o.append(table([(n, t, f"{100 * v / best:.0f}", money(v), f"{c:.2f}", "yes" if m else "") for n, t, v, c, m, _ in summary],
                   ["chest", "type", "value index (best=100)", "model value", "model items", "spawns mobs"]))
    for name, ctype, total, _, _, ps in summary[:6]:
        o.append(f"\n### {name}")
        o.append(table([(st, f"{share:.0%}", ln, money(sum(n * val(i) for i, n in exp.items()))) for st, share, ln, exp in ps],
                       ["rarity", "spawn share", "loot list", "value"]))
        contrib = Counter()
        for _, share, _, exp in ps:
            for i, n in exp.items():
                contrib[i] += share * n * val(i)
        tops = [(label(i), f"{sum(share * exp.get(i, 0) for _, share, _, exp in ps):.3f}", money(v)) for i, v in contrib.most_common(top) if v > 0]
        if tops:
            o.append("Top value drivers:\n" + table(tops, ["item", "expected count", "value"]))
    if live and market.WARNINGS:
        o.append("\n⚠ " + "; ".join(market.WARNINGS) + " — values without prices count as 0; rerun later or use live=False.")
    o.append("\n_Model notes: `chance` in loot.xml is treated as a percentage (values ≥ 100 = guaranteed); this is an interpretation of the "
             "dump, so trust the ranking between chests more than the absolute numbers. Silver bags have no item value and are excluded "
             "offline. Fame, time-to-clear and PvP risk are not included._")
    return "\n".join(o)


# ------------------------------------------------------------------ build cost
def _parse_entry(s):
    m = re.match(r"^\s*(\d+)\s*[x×]\s*(.+)$", s) or re.match(r"^(.+?)\s*[x×]\s*(\d+)\s*$", s)
    if m:
        a, b = m.groups()
        return (b, int(a)) if a.isdigit() else (a, int(b))
    return s, 1


def build_cost(items, server="europe", city="Caerleon", quality=1, compare_enchants=True):
    if not items:
        raise AOError("Give the build as a list of items, e.g. ['T8_2H_BOW', 'T8_HEAD_LEATHER_SET1', '10x T8_MEAL_STEW']")
    entries = []
    for s in items:
        name, n = _parse_entry(s)
        iid = resolve_item(name)
        it = q1("SELECT * FROM items WHERE id=?", iid)
        entries.append((iid, n, it))
    ids = {e[0] for e in entries}
    variants = {}
    if compare_enchants:
        for iid, _, it in entries:
            if it["slot"] in EQUIP_SLOTS and it["kind"] in ("weapon", "equipmentitem", "transformationweapon"):
                variants[iid] = [f"{it['base_id']}@{e}" if e else it["base_id"] for e in range(0, 4)]
                ids.update(variants[iid])
    prices = market.price_map(sorted(ids), server, city, quality)
    rows, total, missing = [], 0.0, []
    ip_sum, ip_n = 0, 0
    for iid, n, it in entries:
        p, src = prices.get(iid, (None, "no data"))
        line = p * n if p else None
        total += line or 0
        if p is None:
            missing.append(iid)
        ip = it["itempower"]
        if ip and it["slot"] in ("mainhand", "offhand", "head", "armor", "shoes", "cape"):
            w = 2 if (it["slot"] == "mainhand" and core.item_json(iid).get("@twohanded") == "true") else 1
            ip_sum += (ip + QUALITY_IP.get(quality, 0)) * w
            ip_n += w
        rows.append((it["slot"] or it["kind"], f"![]({core.ICON.format(iid)}?size=32) {label(iid)}", n, ip or "", money(p), src, money(line)))
    o = [f"## Build cost — {city} ({server}), quality {quality} ({core.QUALITY_NAMES.get(quality)})", "",
         table(rows, ["slot", "item", "qty", "IP", "unit price", "source", "total"]),
         f"\n**Estimated total: {money(total)} silver**" + (f" (+ unknown: {', '.join(f'`{m}`' for m in missing)})" if missing else "")]
    if ip_n:
        o.append(f"Base item power ≈ **{ip_sum / ip_n:.0f}** (gear slots, quality bonus included; mastery/spec not included).")
    if variants:
        cols = []
        for e in range(4):
            s, unknown = 0.0, 0
            for iid, n, it in entries:
                vid = variants.get(iid, [iid] * 4)[e]
                p = prices.get(vid, (None,))[0] or (prices.get(iid, (None,))[0] if iid not in variants else None)
                if p is None:
                    unknown += 1
                s += (p or 0) * n
            cols.append((f".{e}", ("≥ " if unknown else "") + money(s), unknown or ""))
        o.append("\n### Same build at other enchantments\n" + table(cols, ["enchant", "total", "items w/o price"]) +
                 "\n_Consumables stay as listed; '≥' = some items had no price, so the total is a lower bound._")
    if market.WARNINGS:
        o.append("\n⚠ " + "; ".join(market.WARNINGS))
    o.append("\n_Prices: albion-online-data.com (crowd-sourced). Re-gear cost = this total minus items you keep on death (none in full-loot zones)._")
    return "\n".join(o)


# ------------------------------------------------------------------ killboard meta
GAMEINFO = {"europe": "gameinfo-ams", "west": "gameinfo", "east": "gameinfo-sgp"}
_kb_cache = {}


def _events(server, pages):
    host = GAMEINFO.get(server)
    if not host:
        raise AOError(f"server must be one of {list(GAMEINFO)}")
    out = []
    for i in range(pages):
        url = f"https://{host}.albiononline.com/api/gameinfo/events?limit=51&offset={i * 51}"
        hit = _kb_cache.get(url)
        if hit and time.time() - hit[0] < 300:
            out += hit[1]
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ao-db (github.com/valorouscat/ao-db)"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.load(r)
        except Exception as e:
            if out:
                break
            raise AOError(f"Killboard API failed: {e}")
        _kb_cache[url] = (time.time(), data)
        out += data
    return out


def _family(t):
    return re.sub(r"@\d$", "", re.sub(r"^T\d_", "", t or ""))


def _fam_name(fam):
    r = q1("SELECT name_en FROM items WHERE base_id IN (" + ",".join("?" * 8) + ") ORDER BY tier DESC", *[f"T{t}_{fam}" for t in range(1, 9)])
    return re.sub(r"^\S+'s ", "", r["name_en"]) if r and r["name_en"] else fam


def meta_builds(weapon=None, server="europe", pages=10, min_ip=0, top=12):
    evs = _events(server, max(1, min(pages, 20)))
    wfam = _family(resolve_item(weapon)) if weapon else None
    kills, deaths, ips = Counter(), Counter(), defaultdict(list)
    slots = defaultdict(Counter)
    for e in evs:
        for side, counter in (("Killer", kills), ("Victim", deaths)):
            p = e.get(side) or {}
            eq = p.get("Equipment") or {}
            mh = (eq.get("MainHand") or {}).get("Type")
            if not mh or (p.get("AverageItemPower") or 0) < min_ip:
                continue
            f = _family(mh)
            counter[f] += 1
            if side == "Killer":
                ips[f].append(p.get("AverageItemPower") or 0)
                if wfam and f == wfam:
                    for s in ("OffHand", "Head", "Armor", "Shoes", "Cape", "Mount", "Food", "Potion"):
                        t = (eq.get(s) or {}).get("Type")
                        if t:
                            slots[s][_family(t)] += 1
    o = [f"## Killboard meta — {server}, last {len(evs)} kill events (open world PvP, official API)", ""]
    fams = [f for f, _ in kills.most_common(top)]
    if wfam and wfam not in fams and wfam in kills:
        fams.append(wfam)
    rows = [(("➤ " if f == wfam else "") + _fam_name(f), f, kills[f], deaths.get(f, 0), f"{kills[f] / max(deaths.get(f, 0), 1):.2f}",
             f"{sum(ips[f]) / len(ips[f]):.0f}") for f in fams]
    o.append(table(rows, ["weapon", "family", "kills", "deaths", "K/D", "avg IP"]))
    if wfam:
        o.append(f"\n### What {_fam_name(wfam)} players wear (killers)")
        for s, c in slots.items():
            n = sum(c.values())
            o.append(f"- **{s}:** " + ", ".join(f"{_fam_name(f)} {v / n:.0%}" for f, v in c.most_common(4)))
        if not slots:
            o.append("_No kills with this weapon in the sample; raise pages (max 20)._")
    o.append("\n_Killboard covers PvP deaths only (mostly open world); it shows what wins fights, not PvE clear speed. "
             "Small samples are noisy._")
    return "\n".join(o)


# ------------------------------------------------------------------ official mechanics texts
TOPICS = {
    "corrupted": (["%CORRUPTED%", "%CORRUPT%DUNGEON%", "%INFAMY%"], ["corrupteddungeons.json"], ["cdboss", "cdsecondary", "cdbook"]),
    "hellgate": (["%HELLGATE%"], ["hellgate.json"], ["hellchest2l", "hellboss2l"]),
    "mists": (["%MISTS%", "%MIST\\_%"], ["mists.json", "miststemplatemetadata.json"], ["mediummistscamp", "treasurechestmists"]),
    "depths": (["%HELLDUNGEON%", "%DEPTHS%", "%ABYSSAL%"], ["helldungeons.json"], ["hdboss", "hdroomreward"]),
    "avalon": (["%AVALON%", "%ROADS%", "%PORTAL%TRAVEL%"], ["randomdungeons.json", "tunnelsystem.json"], ["avaroadloot", "rdsololoot", "rdgrouploot"]),
    "dungeon": (["%RANDOMDUNGEON%", "%DUNGEON%"], ["randomdungeons.json", "staticdungeons.json"], ["rdsololoot", "rdgrouploot", "staticboss"]),
    "expedition": (["%EXPEDITION%"], ["expeditions.json"], []),
    "faction": (["%FACTIONWARFARE%", "%FACTION\\_%"], ["factionwarfare.json", "factionfortress.json"], ["factionchestsmall", "factionchestmedium"]),
    "arena": (["%ARENA%", "%CRYSTAL%LEAGUE%"], ["arena.json", "crystalleague.json"], []),
    "territory": (["%TERRITORY%", "%CASTLE%", "%OUTPOST%"], ["territorytypes.json", "castles.json", "outpost.json"], ["treasurecastle"]),
    "worldboss": (["%WORLDBOSS%", "%DRAGON%"], ["worldbosses.json", "dragonarea.json"], ["dragonareasolo", "treasuredragonred"]),
    "gathering": (["%GATHER%", "%HARVEST%"], ["harvestables.json", "resources.json"], []),
    "fishing": (["%FISHING%"], [], []),
    "farming": (["%FARMING%", "%ISLAND%", "%LABOURER%"], ["farmingmodifiers.json"], []),
    "crafting": (["%CRAFT%", "%REFIN%", "%FOCUS%"], ["craftingmodifiers.json"], []),
    "treasure": (["%TREASURE%"], ["treasures.json", "treasuredistribution.json"], ["treasurechestsmall", "treasurechestlarge"]),
}


def mechanics(topic, limit=25):
    key = next((k for k in TOPICS if topic.lower().startswith(k) or k in topic.lower()), None)
    if not key:
        return f"Unknown topic {topic!r}. Topics: {', '.join(TOPICS)}. For anything else use search / loc."
    pats, files, chests = TOPICS[key]
    cond = " OR ".join("key LIKE ? ESCAPE '\\'" for _ in pats)
    rows = q(f"SELECT key, en, ru FROM loc WHERE ({cond}) AND length(en) > 70 AND key NOT LIKE '%ACHIEVEMENT%' AND key NOT LIKE '@SPELLS%' "
             f"ORDER BY (key LIKE '%TUTORIAL%' OR key LIKE '%INFO%' OR key LIKE '%DESC%') DESC, length(en) DESC LIMIT ?", *pats, limit)
    strip = re.compile(r"\[/?[^\]]+\]")
    o = [f"## Official game texts: {key}", ""] + [f"- `{r['key']}`: " + strip.sub("", r["en"]) for r in rows]
    for f in files:
        keys = q("SELECT path, key FROM docs WHERE file=? LIMIT 40", f)
        if keys:
            o.append(f"\n### Data file `{f}`\n" + ", ".join(f"`{r['key']}`" for r in keys) + "\n_Read with doc(file, key)._")
    if chests:
        o.append("\n### Related chest types (value analysis: chest_value)\n" + ", ".join(f"`{c}`" for c in chests))
    o.append("\n_These are the game's own descriptions; tutorial texts can lag behind balance changes (e.g. corrupted dungeon IP "
             "requirements). Cross-check numbers with difficulty (game data) and patchnotes; for strategy combine with notes, "
             "meta_builds and a recent web search._")
    return "\n".join(o)


# ------------------------------------------------------------------ reward / difficulty modifiers
# content alias -> [(source, grp LIKE pattern)]
DIFFICULTY = {
    "dungeon": [("difficulty", "default"), ("difficulty", "bossroom%")],
    "mists": [("difficulty", "mists"), ("zone", "mists%")],
    "depths": [("difficulty", "helldungeons%"), ("zone", "helldungeon%")],
    "dragon": [("difficulty", "dragonarea"), ("zone", "dragonarea%")],
    "expedition": [("expedition", "%"), ("zone", "expedition")],
    "zone": [("zone", "safe"), ("zone", "yellow"), ("zone", "orange"), ("zone", "red"), ("zone", "black%"), ("zone", "tunnel")],
    "corrupted": [("corrupted", "%"), ("zone", "corrupted%")],
    "hellgate": [("hellgate", "%"), ("zone", "hell%")],
    "tier": [("tier", "%")],
    "market": [("market", "%")],
}
ALIASES = {"solo": "dungeon", "group": "dungeon", "random": "dungeon", "подзем": "dungeon", "мист": "mists", "туман": "mists",
           "helldungeon": "depths", "abyss": "depths", "глуб": "depths", "ancient": "dragon", "дракон": "dragon",
           "экспед": "expedition", "region": "zone", "outlands": "zone", "black": "zone", "red": "zone", "зон": "zone",
           "запредел": "zone", "коррап": "corrupted", "прокля": "corrupted", "хелл": "hellgate", "тир": "tier",
           "tax": "market", "налог": "market", "рын": "market"}


BUFF_NAMES = {"hitpointsmaxbonus": "HP", "bonusdamagevsplayers": "dmg vs players", "mobdamagemodifier": "dmg",
              "mobhealthmodifier": "HP", "damagebonus": "dmg", "physicalarmor": "armor", "magicresistance": "mres"}


def _buff_text(spell_id):
    """'HP +16%, dmg vs players +16%' from a mob buff spell (buffovertime entries and mob*modifier multipliers)."""
    if not spell_id:
        return ""
    r = q1("SELECT json FROM spells WHERE id=?", spell_id)
    if not r:
        return spell_id
    d = json.loads(r["json"])
    parts = []
    for b in _aslist(d.get("buffovertime")):
        v = core.num(b.get("@value"))
        if v is not None:
            parts.append(f"{BUFF_NAMES.get(b.get('@type'), b.get('@type'))} {v:+.0%}")
    for k in ("mobdamagemodifier", "mobhealthmodifier"):
        for b in _aslist(d.get(k)):
            v = core.num(b.get("@value"))
            if v is not None:
                parts.append(f"{BUFF_NAMES[k]} {v - 1:+.0%}")
    return ", ".join(parts) or spell_id


def _content_key(content):
    c = (content or "").lower()
    if c in DIFFICULTY:
        return c
    return next((k for k in DIFFICULTY if k in c), None) or next((v for a, v in ALIASES.items() if a in c), None)


def difficulty(content=None):
    """Reward multipliers (loot, silver, fame), mob buffs and entry rules per content type and level, straight from the game files."""
    key = _content_key(content)
    if not key:
        rows = q("SELECT source, COUNT(*) n, GROUP_CONCAT(DISTINCT grp) g FROM modifiers GROUP BY source")
        return ("## Difficulty / reward modifiers — pick a content type\n\n" + table([(r["source"], r["n"], r["g"][:120]) for r in rows],
                                                                                    ["source", "rows", "groups"]) +
                f"\n\nContent keys: {', '.join(DIFFICULTY)} (aliases in RU/EN work, e.g. 'соло подземелья', 'black zone').")
    o = [f"## Reward / difficulty modifiers: {key}", ""]
    by_source = {}
    for source, pat in DIFFICULTY[key]:
        by_source.setdefault(source, []).extend(
            q("SELECT * FROM modifiers WHERE source=? AND grp LIKE ? ORDER BY grp, CAST(level AS REAL), rowid", source, pat))
    for source, rows in by_source.items():
        if not rows:
            continue
        if source in ("difficulty", "expedition", "zone"):
            title = {"difficulty": "Instance difficulty levels (randomdungeons.json)", "expedition": "Expedition difficulty (expeditioncategories.json)",
                     "zone": "Zone / region multipliers (gamedata.json ClusterDangerBonus)"}[source]
            t = [(r["grp"], r["level"], fmt(r["loot"]), fmt(r["silver"]), fmt(r["fame"]), _buff_text(r["mobbuff"]),
                  ", ".join(f"{k.replace('factor', '')} ×{v}" for k, v in json.loads(r["extra"] or "{}").items()
                            if k in ("gatheringfamefactor", "fishingfamefactor") and v not in ("1", None)) or
                  json.loads(r["extra"] or "{}").get("tokenlootlist", "")) for r in rows]
            o.append(f"### {title}\n" + table(t, ["group", "level", "loot ×", "silver ×", "fame ×", "mob buff", "other"]))
            if source == "zone" and any(r["grp"] == "black1" for r in rows):
                o.append("_safe = blue zone; black1–black6 = Outlands region quality (Q1–Q6, higher towards the centre)._")
        elif source in ("corrupted", "hellgate"):
            t = []
            for r in rows:
                ex = json.loads(r["extra"] or "{}")
                t.append((r["grp"], r["level"], ex.get("itempowerrequirement", ""),
                          "yes" if ex.get("playersarelethalinentranceclusterrequirement") == "true" or "_lethal" in r["grp"].replace("non_lethal", "") else "",
                          ex.get("infamykillbonus", ""), ex.get("percentbosslootonkill", ""), str(ex.get("rewardconstant", ""))[:7], ex.get("mightreward", "")))
            o.append(f"### {source.title()} levels\n" + table(t, ["level", "tier" if source == "corrupted" else "team size", "IP required",
                                                                 "lethal", "infamy/kill bonus", "boss loot % on kill", "reward constant", "might reward"]))
        elif source == "tier":
            o.append("### Quest / activity scaling by region tier (gamedata.json)\n" + table([(r["level"], fmt(r["fame"])) for r in rows], ["tier", "scaling ×"]))
        elif source == "market":
            o.append("### Marketplace taxes (gamedata.json)\n" + table([(r["level"], json.loads(r["extra"])["value"]) for r in rows], ["tax", "value"]) +
                     "\n_Premium halves the transaction tax (8% → 4%)._")
    pn = ""
    try:
        from . import patchnotes
        term = {"dungeon": "randomized dungeon", "zone": "region quality", "depths": "the depths", "dragon": "ancient lands",
                "market": "marketplace tax", "corrupted": "corrupted dungeon", "hellgate": "hellgate", "mists": "mists",
                "expedition": "expedition", "tier": "tier"}.get(key, key)
        pn = patchnotes.top_lines(term, limit=4)
    except Exception:
        pass
    if pn:
        o.append("\n### Recent patch notes on this content\n" + pn)
    o.append("\n_Multipliers are relative to the content's base rewards; they stack with tier, chest rarity and zone bonuses where the game applies "
             "them. Values come from the current data dump (see info for its date)._")
    return "\n".join(o)


# ------------------------------------------------------------------ knowledge notes
def _notes():
    out = []
    for p in sorted(glob.glob(os.path.join(KNOWLEDGE, "*.md"))):
        with open(p, encoding="utf-8") as fh:
            out.append((os.path.basename(p), fh.read()))
    return out


def notes(query=None, limit=5):
    docs = _notes()
    if not docs:
        return "No notes yet. Add verified findings with save_note."
    if not query:
        return "\n".join(f"- `{n}` — {t.splitlines()[0].lstrip('# ')}" for n, t in docs)
    db = sqlite3.connect(":memory:")
    db.execute("CREATE VIRTUAL TABLE n USING fts5(name, body, tokenize='unicode61 remove_diacritics 2')")
    db.executemany("INSERT INTO n VALUES(?,?)", docs)
    hits = db.execute("SELECT name, body FROM n WHERE n MATCH ? ORDER BY bm25(n) LIMIT ?", (core.fts_query(query), limit)).fetchall()
    if not hits:
        hits = db.execute("SELECT name, body FROM n WHERE n MATCH ? ORDER BY bm25(n) LIMIT ?",
                          (" OR ".join(core.fts_query(query).split()), limit)).fetchall()
    return "\n\n---\n\n".join(f"<!-- {n} -->\n{_staleness(b)}{b}" for n, b in hits) or f"No notes match {query!r}"


def _staleness(body):
    """Warn when a note predates the latest major update / patch."""
    from . import patchnotes
    m = re.search(r"_updated: (\d{4}-\d{2}-\d{2})", body)
    if not m:
        return "⚠ undated note — verify against patchnotes.\n\n"
    try:
        mdate, mtitle = patchnotes.last_major()
        pdate, ptitle = patchnotes.current_patch()
    except AOError:
        return ""
    if mdate and m.group(1) < mdate:
        return f"⚠ written before the last major update ({mtitle}, {mdate}) — re-verify with patchnotes before relying on it.\n\n"
    if pdate and m.group(1) < pdate:
        return f"ℹ newer patch since this note: {ptitle} ({pdate}) — check patchnotes(<topic>, since={m.group(1)}).\n\n"
    return ""


def save_note(title, body, sources, tags=None):
    if not sources:
        raise AOError("A note needs at least one source (URL, game file/ID, or tool output it was derived from).")
    os.makedirs(KNOWLEDGE, exist_ok=True)
    slug = re.sub(r"[^\w]+", "-", title.lower(), flags=re.U).strip("-")[:60] or "note"
    path = os.path.join(KNOWLEDGE, f"{slug}.md")
    today = datetime.date.today().isoformat()
    from . import patchnotes
    text = (f"# {title}\n\n_updated: {today}" + (f" · tags: {', '.join(tags)}" if tags else "") +
            f" · data: {core.q1('SELECT v FROM meta WHERE k=?', 'repo_rev')['v'][:7]} · patch: {patchnotes.latest_title()}_\n\n"
            f"{body.strip()}\n\n## Sources\n" + "\n".join(f"- {s}" for s in sources) + "\n")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return f"saved {os.path.relpath(path, ROOT)}"
