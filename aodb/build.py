#!/usr/bin/env python3
"""Build the Albion Online knowledge base (SQLite + FTS5) from ao-bin-dumps.

Usage: python3 -m aodb.build [--repo PATH] [--db PATH] [--regions]
"""
import argparse, json, os, re, sqlite3, sys, time, glob

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
LANGS = ["EN-US", "RU-RU", "DE-DE", "FR-FR", "PL-PL", "ES-ES", "PT-BR", "IT-IT",
         "ZH-CN", "KO-KR", "JA-JP", "ZH-TW", "ID-ID", "TR-TR", "AR-SA"]

SCHEMA = """
CREATE TABLE meta(k TEXT PRIMARY KEY, v TEXT);
CREATE TABLE loc(key TEXT PRIMARY KEY, en TEXT, ru TEXT, all_json TEXT);
CREATE VIRTUAL TABLE loc_fts USING fts5(key, en, ru, content='loc', content_rowid='rowid', tokenize='unicode61 remove_diacritics 2');

CREATE TABLE items(id TEXT PRIMARY KEY, base_id TEXT, enchant INT, kind TEXT, tier INT,
  name_en TEXT, name_ru TEXT, desc_en TEXT, desc_ru TEXT, names_json TEXT,
  shopcat TEXT, sub1 TEXT, sub2 TEXT, sub3 TEXT, slot TEXT, itempower INT, weight REAL,
  itemvalue REAL, craftcat TEXT, json TEXT);
CREATE INDEX items_base ON items(base_id);
CREATE VIRTUAL TABLE items_fts USING fts5(id, name_en, name_ru, desc_en, desc_ru, tags, tokenize='unicode61 remove_diacritics 2');

CREATE TABLE recipes(item_id TEXT, recipe_no INT, silver REAL, time REAL, focus REAL, amount INT,
  resource_id TEXT, count INT, maxreturn INT, artifact INT);
CREATE INDEX recipes_item ON recipes(item_id);
CREATE INDEX recipes_res ON recipes(resource_id);
CREATE TABLE upgrades(item_id TEXT, resource_id TEXT, count INT);
CREATE TABLE item_spells(item_id TEXT, spell_id TEXT, slots TEXT, tag TEXT);
CREATE INDEX item_spells_spell ON item_spells(spell_id);
CREATE INDEX item_spells_item ON item_spells(item_id);

CREATE TABLE spells(id TEXT PRIMARY KEY, kind TEXT, name_en TEXT, name_ru TEXT, desc_en TEXT, desc_ru TEXT,
  category TEXT, target TEXT, cooldown REAL, energy REAL, casttime REAL, castrange REAL, json TEXT);
CREATE VIRTUAL TABLE spells_fts USING fts5(id, name_en, name_ru, desc_en, desc_ru, tokenize='unicode61 remove_diacritics 2');

CREATE TABLE mobs(id TEXT PRIMARY KEY, name_en TEXT, name_ru TEXT, tier INT, category TEXT, typecat TEXT,
  faction TEXT, hp REAL, damage REAL, fame REAL, armor REAL, mres REAL, json TEXT);
CREATE VIRTUAL TABLE mobs_fts USING fts5(id, name_en, name_ru, faction, category, tokenize='unicode61 remove_diacritics 2');
CREATE TABLE mob_loot(mob_id TEXT, lootlist TEXT, chance REAL);
CREATE INDEX mob_loot_list ON mob_loot(lootlist);

CREATE TABLE loot(list TEXT, kind TEXT, target TEXT, amount TEXT, chance REAL, extra TEXT);
CREATE INDEX loot_list ON loot(list);
CREATE INDEX loot_target ON loot(target);

CREATE TABLE loot_raw(name TEXT PRIMARY KEY, json TEXT);
CREATE TABLE chests(name TEXT PRIMARY KEY, chesttype TEXT, faction TEXT, json TEXT);
CREATE TABLE modifiers(source TEXT, grp TEXT, level TEXT, mobbuff TEXT, loot REAL, silver REAL, fame REAL, extra TEXT);
CREATE TABLE clusters(idx TEXT PRIMARY KEY, name TEXT, file TEXT, type TEXT, biome TEXT, tier INT, zone TEXT);
CREATE VIRTUAL TABLE clusters_fts USING fts5(idx, name, file, tokenize='unicode61');

CREATE TABLE docs(id INTEGER PRIMARY KEY, file TEXT, path TEXT, key TEXT, json TEXT);
CREATE VIRTUAL TABLE docs_fts USING fts5(file, key, text, tokenize='unicode61 remove_diacritics 2');
"""


def aslist(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def num(x, f=float):
    try:
        return f(x)
    except (TypeError, ValueError):
        try:
            return f(float(x))
        except (TypeError, ValueError):
            return None


def load(repo, name):
    with open(os.path.join(repo, name), encoding="utf-8") as fh:
        return json.load(fh)


class Builder:
    def __init__(self, repo, db, regions):
        if not os.path.exists(os.path.join(repo, "items.json")):
            sys.exit(f"ao-bin-dumps not found at {repo}. Run ./setup.sh or pass --repo")
        self.repo, self.dbpath, self.regions = repo, db, regions
        self.tmppath = db + ".tmp"  # build aside, then atomically swap in
        if os.path.exists(self.tmppath):
            os.remove(self.tmppath)
        self.db = sqlite3.connect(self.tmppath)
        self.db.executescript("PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;" + SCHEMA)
        self.loc = {}

    def log(self, *a):
        print(f"[{time.strftime('%H:%M:%S')}]", *a, file=sys.stderr, flush=True)

    def L(self, key, lang="EN-US"):
        if not key:
            return None
        k = key if key.startswith("@") else "@" + key
        e = self.loc.get(k)
        return e.get(lang) if e else None

    # ---------------------------------------------------------------- localization
    def build_loc(self):
        tus = load(self.repo, "localization.json")["tmx"]["body"]["tu"]
        rows = []
        for tu in tus:
            d = {}
            for v in aslist(tu.get("tuv")):
                seg = v.get("seg")
                if isinstance(seg, dict):
                    seg = seg.get("#text", "")
                d[v.get("@xml:lang")] = seg
            self.loc[tu["@tuid"]] = d
            rows.append((tu["@tuid"], d.get("EN-US"), d.get("RU-RU"), json.dumps(d, ensure_ascii=False)))
        self.db.executemany("INSERT INTO loc VALUES(?,?,?,?)", rows)
        self.db.execute("INSERT INTO loc_fts(loc_fts) VALUES('rebuild')")
        self.log("loc", len(rows))

    # ---------------------------------------------------------------- items
    def build_items(self):
        raw = load(self.repo, "items.json")["items"]
        byid = {}
        for kind, lst in raw.items():
            if kind.startswith("@") or kind == "shopcategories":
                continue
            for it in aslist(lst):
                if isinstance(it, dict) and "@uniquename" in it:
                    byid[it["@uniquename"]] = (kind, it)
        self.raw_items = byid
        # shop category names
        formatted = load(self.repo, "formatted/items.json")
        names = {f["UniqueName"]: f for f in formatted}
        ids = list(names.keys())
        # include raw items missing from formatted
        for k in byid:  # raw-only items (skins, test items); *_LEVELn bases only exist as @n variants
            if k not in names and not re.search(r"_LEVEL\d$", k):
                ids.append(k)

        irows, frows, rrows, urows, srows = [], [], [], [], []
        for iid in ids:
            base, ench = iid, 0
            m = re.match(r"^(.*)@(\d+)$", iid)
            if m:
                base, ench = m.group(1), int(m.group(2))
            rawbase = base
            if rawbase not in byid:
                rawbase = re.sub(r"_LEVEL\d+$", "", base)
            kind, it = byid.get(rawbase, (None, {}))
            data = dict(it)
            enc = None
            if ench:
                for e in aslist((it.get("enchantments") or {}).get("enchantment")):
                    if num(e.get("@enchantmentlevel"), int) == ench:
                        enc = e
                        break
                if enc:
                    data.update({k: v for k, v in enc.items() if k.startswith("@")})
                    for k in ("craftingrequirements", "upgraderequirements"):
                        if k in enc:
                            data[k] = enc[k]
            data.pop("enchantments", None) if ench else None
            f = names.get(iid, {})
            ln = f.get("LocalizedNames") or {}
            ld = f.get("LocalizedDescriptions") or {}
            if not ln:
                ln = self.loc.get(it.get("@namelocatag") or f"@ITEMS_{base}", {}) or {}
            if not ld:
                ld = self.loc.get(it.get("@descriptionlocatag") or f"@ITEMS_{base}_DESC", {}) or {}
            tier = num(data.get("@tier"), int)
            if tier is None:
                mt = re.match(r"^T(\d+)_", iid)
                tier = int(mt.group(1)) if mt else None
            irows.append((iid, base, ench, kind, tier, ln.get("EN-US"), ln.get("RU-RU"), ld.get("EN-US"), ld.get("RU-RU"),
                          json.dumps(ln, ensure_ascii=False), data.get("@shopcategory"), data.get("@shopsubcategory1"),
                          data.get("@shopsubcategory2"), data.get("@shopsubcategory3"), data.get("@slottype"),
                          num(data.get("@itempower"), int), num(data.get("@weight")), num(data.get("@itemvalue")),
                          data.get("@craftingcategory"), json.dumps(data, ensure_ascii=False)))
            tags = " ".join(filter(None, [kind, data.get("@shopcategory"), data.get("@shopsubcategory1"),
                                          data.get("@shopsubcategory2"), data.get("@slottype"), f"T{tier}" if tier else None,
                                          f"T{tier}.{ench}" if tier else None]
                            + [v for k, v in ln.items() if k not in ("EN-US", "RU-RU")]))
            frows.append((iid, ln.get("EN-US"), ln.get("RU-RU"), ld.get("EN-US"), ld.get("RU-RU"), tags))
            for n, cr in enumerate(aslist(data.get("craftingrequirements"))):
                if not isinstance(cr, dict):
                    continue
                res = aslist(cr.get("craftresource"))
                if not res:
                    res = [{}]
                for r in res:
                    rid = r.get("@uniquename")
                    rl = num(r.get("@enchantmentlevel"), int)
                    if rid and rl:
                        rid = f"{rid}@{rl}"
                    rrows.append((iid, n, num(cr.get("@silver")), num(cr.get("@time")), num(cr.get("@craftingfocus")),
                                  num(cr.get("@amountcrafted"), int) or 1, rid, num(r.get("@count"), int),
                                  num(r.get("@maxreturnamount"), int), 1 if r.get("@enchantmentlevel") is None and "ARTEFACT" in (rid or "") else 0))
            for u in aslist((data.get("upgraderequirements") or {}).get("upgraderesource")):
                urows.append((iid, u.get("@uniquename"), num(u.get("@count"), int)))
            if not ench:
                csl, seen = it.get("craftingspelllist") or {}, set()
                while isinstance(csl, dict) and csl.get("@reference") and csl["@reference"] not in seen:
                    seen.add(csl["@reference"])
                    csl = byid.get(csl["@reference"], (None, {}))[1].get("craftingspelllist") or {}
                for s in aslist(csl.get("craftspell") if isinstance(csl, dict) else None):
                    srows.append((iid, s.get("@uniquename"), s.get("@slots"), s.get("@tag")))
        self.db.executemany(f"INSERT OR REPLACE INTO items VALUES({','.join('?'*20)})", irows)
        self.db.executemany("INSERT INTO items_fts VALUES(?,?,?,?,?,?)", frows)
        self.db.executemany("INSERT INTO recipes VALUES(?,?,?,?,?,?,?,?,?,?)", rrows)
        self.db.executemany("INSERT INTO upgrades VALUES(?,?,?)", urows)
        self.db.executemany("INSERT INTO item_spells VALUES(?,?,?,?)", srows)
        self.log("items", len(irows), "recipes", len(rrows), "item_spells", len(srows))

    # ---------------------------------------------------------------- spells
    def build_spells(self):
        raw = load(self.repo, "spells.json")["spells"]
        rows, frows = [], []
        for kind in ("passivespell", "activespell", "togglespell"):
            for s in aslist(raw.get(kind)):
                sid = s["@uniquename"]
                nk = s.get("@namelocatag") or f"@SPELLS_{sid}"
                dk = s.get("@descriptionlocatag") or f"@SPELLS_{sid}_DESC"
                n = self.loc.get(nk, {})
                d = self.loc.get(dk, {})
                rows.append((sid, kind, n.get("EN-US"), n.get("RU-RU"), d.get("EN-US"), d.get("RU-RU"), s.get("@category"),
                             s.get("@target"), num(s.get("@recastdelay")), num(s.get("@energyusage")),
                             num(s.get("@castingtime")), num(s.get("@castrange")), json.dumps(s, ensure_ascii=False)))
                frows.append((sid, n.get("EN-US"), n.get("RU-RU"), d.get("EN-US"), d.get("RU-RU")))
        self.db.executemany(f"INSERT OR REPLACE INTO spells VALUES({','.join('?'*13)})", rows)
        self.db.executemany("INSERT INTO spells_fts VALUES(?,?,?,?,?)", frows)
        self.log("spells", len(rows))

    # ---------------------------------------------------------------- mobs
    def build_mobs(self):
        raw = load(self.repo, "mobs.json")["Mobs"]["Mob"]
        rows, frows, lrows = [], [], []
        for m in aslist(raw):
            mid = m["@uniquename"]
            n = self.loc.get(m.get("@namelocatag") or f"@MOB_{mid}", {})
            rows.append((mid, n.get("EN-US"), n.get("RU-RU"), num(m.get("@tier"), int), m.get("@category"),
                         m.get("@mobtypecategory"), m.get("@faction"), num(m.get("@hitpointsmax")),
                         num(m.get("@attackdamage")), num(m.get("@fame")), num(m.get("@physicalarmor")),
                         num(m.get("@magicresistance")), json.dumps(m, ensure_ascii=False)))
            frows.append((mid, n.get("EN-US"), n.get("RU-RU"), m.get("@faction"), m.get("@category")))
            loot = m.get("Loot") or {}
            for r in aslist(loot.get("LootListReference")):
                lrows.append((mid, r.get("@name"), num(r.get("@chance"))))
        self.db.executemany(f"INSERT OR REPLACE INTO mobs VALUES({','.join('?'*13)})", rows)
        self.db.executemany("INSERT INTO mobs_fts VALUES(?,?,?,?,?)", frows)
        self.db.executemany("INSERT INTO mob_loot VALUES(?,?,?)", lrows)
        self.log("mobs", len(rows), "mob_loot", len(lrows))

    # ---------------------------------------------------------------- loot
    def build_loot(self):
        rows = []

        def walk(listname, node, chance=None):
            if not isinstance(node, dict):
                return
            for key, val in node.items():
                if key.startswith("@"):
                    continue
                for ch in aslist(val):
                    if not isinstance(ch, dict):
                        continue
                    c = num(ch.get("@chance"))
                    if c is None:
                        c = num(ch.get("@weight"))
                    if key == "Item":
                        rows.append((listname, "item", ch.get("@type") or ch.get("@uniquename"),
                                     ch.get("@amount") or (f"{ch.get('@minamount')}-{ch.get('@maxamount')}" if ch.get("@minamount") else None),
                                     c, json.dumps({k: v for k, v in ch.items() if k.startswith("@")})))
                    elif key in ("LootListReference", "LootList"):
                        rows.append((listname, "ref", ch.get("@name"), None, c, None))
                    elif key == "Silver":
                        rows.append((listname, "silver", "SILVER", ch.get("@amount") or ch.get("@maxamount"), c, None))
                    walk(listname, ch, c)

        raws = []
        for fname in ("loot.json",):
            d = load(self.repo, fname)["LootDefinition"]
            for ll in aslist(d.get("Lootlist")):
                walk(ll["@name"], ll)
                raws.append((ll["@name"], json.dumps(ll, ensure_ascii=False)))
        self.db.executemany("INSERT INTO loot VALUES(?,?,?,?,?,?)", rows)
        self.db.executemany("INSERT OR REPLACE INTO loot_raw VALUES(?,?)", raws)
        lc = load(self.repo, "lootchests.json")["LootChests"]
        self.db.executemany("INSERT OR REPLACE INTO chests VALUES(?,?,?,?)",
                            [(c["@uniquename"], c.get("@chesttype"), c.get("@faction"), json.dumps(c, ensure_ascii=False))
                             for c in aslist(lc.get("LootChest")) if isinstance(c, dict) and "@uniquename" in c])
        self.log("loot rows", len(rows))

    # ---------------------------------------------------------------- reward / difficulty modifiers
    def build_modifiers(self):
        rows = []

        def extra(d, skip):
            return json.dumps({k.lstrip("@"): v for k, v in d.items() if k.startswith("@") and k not in skip}, ensure_ascii=False)

        g = load(self.repo, "gamedata.json")["AO-GameData"]
        for z in aslist((g.get("ClusterDangerBonusTypes") or {}).get("ClusterDangerBonus")):
            rows.append(("zone", z.get("@type"), "", z.get("@mobbuff"), num(z.get("@moblootfactor")), num(z.get("@mobsilverlootfactor")),
                         num(z.get("@famefactor")), extra(z, {"@type", "@icon", "@mobbuff", "@moblootfactor", "@mobsilverlootfactor", "@famefactor"})))
        for t in aslist((g.get("QuestScalingByClusterTier") or {}).get("Tier")):
            rows.append(("tier", "quest scaling", t.get("@tier"), None, None, None, num(t.get("@scalingfactor")), "{}"))
        mp = (g.get("MarketPlace") or {}).get("TaxValues") or {}
        for t in aslist(mp.get("TaxFactor")):
            rows.append(("market", "tax", t.get("@name"), None, None, None, None, json.dumps({"value": t.get("@value")})))
        rd = load(self.repo, "randomdungeons.json")["randomdungeons"]
        for grp in aslist((rd.get("DifficultyLevels") or {}).get("difficultygroup")):
            for d in aslist(grp.get("difficulty")):
                rows.append(("difficulty", grp.get("@name"), d.get("@level"), d.get("@mobmodifier"), num(d.get("@lootfactor")),
                             num(d.get("@silverfactor")), num(d.get("@mobfamefactor")),
                             extra(d, {"@level", "@mobmodifier", "@lootfactor", "@silverfactor", "@mobfamefactor"})))
        for cat in aslist(load(self.repo, "expeditioncategories.json")["expeditioncategories"].get("expeditioncategory")):
            for d in aslist((cat.get("difficultylevels") or {}).get("difficulty")):
                rows.append(("expedition", f"{cat.get('@uniquename')} (T{cat.get('@tier')} {cat.get('@grouptype')})", d.get("@level"),
                             d.get("@mobmodifier"), num(d.get("@lootfactor")), num(d.get("@silverfactor")), num(d.get("@mobfamefactor")),
                             extra(d, {"@level", "@mobmodifier", "@lootfactor", "@silverfactor", "@mobfamefactor"})))
        cd = load(self.repo, "corrupteddungeons.json")["corrupteddungeons"]
        for d in aslist((cd.get("difficulty") or {}).get("difficultylevel")):
            rows.append(("corrupted", d.get("@name"), d.get("@tier"), None, None, None, None,
                         extra(d, {"@name", "@tier", "@displayname", "@clustertype"})))
        hg = load(self.repo, "hellgate.json")["hellgates"]
        for m in aslist((hg.get("hellgatemodes") or {}).get("hellgatemode")):
            rows.append(("hellgate", m.get("@name"), m.get("@teamsize"), None, None, None, None,
                         extra(m, {"@name", "@teamsize"})))
        self.db.executemany("INSERT INTO modifiers VALUES(?,?,?,?,?,?,?,?)", rows)
        self.log("modifiers", len(rows))

    # ---------------------------------------------------------------- clusters
    def build_clusters(self):
        world = load(self.repo, "formatted/world.json")
        files = {}
        for p in glob.glob(os.path.join(self.repo, "cluster", "*.cluster.xml")):
            fn = os.path.basename(p)
            files.setdefault(fn.split("_")[0], fn)
        rows = []
        for w in world:
            idx, name = w["Index"], w["UniqueName"]
            fn = files.get(idx)
            typ = biome = zone = None
            tier = None
            src = fn or name
            mm = re.search(r"_(CTY|WRL|STT|HBS|ISL|TNL|DNG|SD|PSG|RD|ARENA|[A-Z]{2,4})_([A-Z]{2})_[A-Z_]*?T(\d+)_?([A-Z]*)", src)
            if mm:
                typ, biome, tier, zone = mm.group(1), mm.group(2), int(mm.group(3)), mm.group(4) or None
            rows.append((idx, name, fn, typ, biome, tier, zone))
        self.db.executemany("INSERT OR REPLACE INTO clusters VALUES(?,?,?,?,?,?,?)", rows)
        self.db.executemany("INSERT INTO clusters_fts VALUES(?,?,?)", [(r[0], r[1], r[2] or "") for r in rows])
        self.log("clusters", len(rows))

    # ---------------------------------------------------------------- generic docs (all files)
    def flatten(self, obj, prefix="", out=None, depth=0):
        if out is None:
            out = []
        if depth > 6 or len(out) > 400:
            return out
        if isinstance(obj, dict):
            for k, v in obj.items():
                self.flatten(v, f"{prefix}.{k.lstrip('@')}" if prefix else k.lstrip("@"), out, depth + 1)
        elif isinstance(obj, list):
            for v in obj[:50]:
                self.flatten(v, prefix, out, depth + 1)
        else:
            s = str(obj)
            out.append(f"{prefix.split('.')[-1]}={s}")
            if s.startswith("@") and s in self.loc:
                t = self.loc[s]
                out.append(" ".join(filter(None, [t.get("EN-US"), t.get("RU-RU")])))
        return out

    def records(self, node, path, depth=0):
        """Yield (path, record) for 'entity-like' dicts (with an id-ish attribute)."""
        if isinstance(node, list):
            for i, v in enumerate(node):
                yield from self.records(v, path, depth)
            return
        if not isinstance(node, dict):
            return
        key = None
        for k in ("@uniquename", "@name", "@id", "@type", "@tuid", "UniqueName", "@key", "@index"):
            if k in node and isinstance(node[k], str):
                key = node[k]
                break
        if key and depth >= 1:
            yield path, key, node
            return
        if depth > 4:
            return
        for k, v in node.items():
            if isinstance(v, (dict, list)):
                yield from self.records(v, f"{path}/{k}", depth + 1)

    def build_docs(self):
        skip = {"localization.json"}
        files = sorted(f for f in os.listdir(self.repo) if f.endswith(".json"))
        if not self.regions:
            files = [f for f in files if not re.search(r"_(asia|europe)(_patch)?\.json$", f)]
        n = 0
        for fname in files:
            if fname in skip:
                continue
            try:
                d = load(self.repo, fname)
            except Exception as e:
                self.log("skip", fname, e)
                continue
            d.pop("?xml", None)
            rows, frows = [], []
            got = False
            for path, key, rec in self.records(d, ""):
                got = True
                js = json.dumps(rec, ensure_ascii=False)
                if len(js) > 200000:
                    js = js[:200000]
                text = " ".join(self.flatten(rec))
                rows.append((fname, path, key, js))
                frows.append((fname, key, f"{key} {path} {text}"))
            if not got:
                js = json.dumps(d, ensure_ascii=False)
                rows.append((fname, "/", fname, js[:500000]))
                frows.append((fname, fname, " ".join(self.flatten(d))))
            cur = self.db.execute("SELECT COALESCE(MAX(id),0) FROM docs").fetchone()[0]
            self.db.executemany("INSERT INTO docs(file,path,key,json) VALUES(?,?,?,?)", rows)
            self.db.executemany("INSERT INTO docs_fts(rowid,file,key,text) VALUES(?,?,?,?)",
                                [(cur + i + 1,) + fr for i, fr in enumerate(frows)])
            n += len(rows)
        self.log("docs", n, "from", len(files), "files")

    def run(self):
        t = time.time()
        self.build_loc()
        self.build_items()
        self.build_spells()
        self.build_mobs()
        self.build_loot()
        self.build_modifiers()
        self.build_clusters()
        self.build_docs()
        rev = os.popen(f"git -C '{self.repo}' log -1 --format='%h %cs %s' 2>/dev/null").read().strip()
        self.db.executemany("INSERT INTO meta VALUES(?,?)", [("built", time.strftime("%Y-%m-%d %H:%M")), ("repo_rev", rev)])
        self.db.commit()
        self.db.execute("VACUUM")
        self.db.close()
        os.replace(self.tmppath, self.dbpath)
        self.log(f"done in {time.time()-t:.0f}s ->", self.dbpath, f"{os.path.getsize(self.dbpath)/1e6:.0f} MB")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    default_repo = os.environ.get("AO_DUMPS") or next(
        (p for p in (os.path.join(HERE, "ao-bin-dumps"), os.path.join(os.path.dirname(HERE), "ao-bin-dumps"))
         if os.path.exists(os.path.join(p, "items.json"))), os.path.join(HERE, "ao-bin-dumps"))
    ap.add_argument("--repo", default=default_repo, help="path to an ao-bin-dumps checkout (env AO_DUMPS)")
    ap.add_argument("--db", default=os.path.join(HERE, "ao.db"))
    ap.add_argument("--regions", action="store_true", help="also index *_asia/*_europe variant files")
    a = ap.parse_args()
    Builder(a.repo, a.db, a.regions).run()
