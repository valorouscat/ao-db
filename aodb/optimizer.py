"""Build optimizer for PvPvE content: every weapon of the chosen classes × armor kits × item-power levels, each scored on
the content's monsters (encounter simulation) and against the killboard meta at the content's fight size (duel model),
priced with the cheapest tier/enchant reaching each IP level, ranked by score and by score per silver within budget bands.
"""
import math, statistics
from . import core, combat, encounter, gearcheck, market, pvp
from .core import AOError, q, q1, label, money, table

# armor kits: (name, [(slot item family, active spell, passive spell)])
KITS = [
    ("Hunter Hood · Assassin Jacket · Mercenary Shoes", [("HEAD_LEATHER_SET2", "SELF_CLEANSE", "PASSIVE_BALANCE"),
                                                         ("ARMOR_LEATHER_SET3", "AMBUSH", "PASSIVE_ARMOR_BALANCE"),
                                                         ("SHOES_LEATHER_SET1", "CLEANSE_DASH", "PASSIVE_BALANCE")]),
    ("Mage Cowl · Assassin Jacket · Knight Boots", [("HEAD_CLOTH_SET3", "ENERGY_BARRIER", "PASSIVE_INCREASED_DAMAGE"),
                                                    ("ARMOR_LEATHER_SET3", "AMBUSH", "PASSIVE_ARMOR_BALANCE"),
                                                    ("SHOES_PLATE_SET2", "DODGE", "PASSIVE_MR_AR")]),
    ("Hunter Hood · Mercenary Jacket · Mercenary Shoes", [("HEAD_LEATHER_SET2", "SELF_CLEANSE", "PASSIVE_BALANCE"),
                                                          ("ARMOR_LEATHER_SET1", "BLOODLUST", "PASSIVE_ARMOR_BALANCE"),
                                                          ("SHOES_LEATHER_SET1", "CLEANSE_DASH", "PASSIVE_BALANCE")]),
    ("Mage Cowl · Cleric Robe · Knight Boots", [("HEAD_CLOTH_SET3", "ENERGY_BARRIER", "PASSIVE_INCREASED_DAMAGE"),
                                                ("ARMOR_CLOTH_SET2", "LIFESAVIOR", "PASSIVE_ARMOR_INCREASED_DAMAGE"),
                                                ("SHOES_PLATE_SET2", "DODGE", "PASSIVE_MR_AR")]),
    ("Soldier Helmet · Assassin Jacket · Mercenary Shoes", [("HEAD_PLATE_SET1", "BLOCK", "PASSIVE_MR_AR"),
                                                            ("ARMOR_LEATHER_SET3", "AMBUSH", "PASSIVE_ARMOR_BALANCE"),
                                                            ("SHOES_LEATHER_SET1", "CLEANSE_DASH", "PASSIVE_BALANCE")]),
]
CONSUMABLES = [("T7_MEAL_ROAST", 3), ("T6_POTION_HEAL", 3), ("T8_POTION_CLEANSE", 1)]
ARTIFACT_TAGS = ("_HELL", "_UNDEAD", "_KEEPER", "_AVALON", "_MORGANA", "_CRYSTAL")
LEVELS = (800, 900, 1000, 1100, 1200)       # base item power of the gear
BANDS = ((0, 150_000), (150_000, 300_000), (300_000, 600_000), (600_000, 1_200_000), (1_200_000, 10 ** 12))
WEIGHTS = {"pve_safe": 0.35, "pve_speed": 0.10, "pvp_win": 0.40, "pvp_live": 0.15}


def weapon_families(classes):
    rows = q(f"SELECT id FROM items WHERE shopcat='weapons' AND sub1 IN ({','.join('?' * len(classes))}) AND tier=4 AND enchant=0 "
             "AND slot='mainhand' ORDER BY id", *classes)
    return [r["id"][3:] for r in rows]


def _variant_at(fam, level):
    """Item ids of a family whose base IP falls in the level's band [level, level+99] (e.g. 1000 = 4.3 / 5.2 / 6.1 / 7.0;
    artifact weapons carry +25…+100 IP, e.g. Bow of Badon 6.0 = 975 → band 900)."""
    return [r["id"] for r in q("SELECT id FROM items WHERE id GLOB ? AND itempower>=? AND itempower<?", f"T[0-9]_{fam}*", level, level + 100)
            if gearcheck.advisor._family(r["id"]) == fam]


def _loadout(wfam, kit, level, cheap):
    """Concrete loadout at a base IP level, using the cheapest priced variant of every item."""
    pick = lambda fam: cheap.get((fam, level)) or (_variant_at(fam, level) or [f"T6_{fam}"])[0]
    w = pick(wfam)
    eq = [{"item": w}]
    if q1("SELECT json FROM items WHERE id=?", w) and core.item_json(w).get("@twohanded") != "true":
        eq.append({"item": pick("OFF_TORCH")})
    for fam, act, pas in kit[1]:
        eq.append({"item": pick(fam), "activeSpells": [act], "passiveSpells": [pas]})
    eq.append({"item": pick("CAPE")})
    eq += [{"item": i, "stack": n} for i, n in CONSUMABLES]
    return {"name": f"{core.q1('SELECT name_en FROM items WHERE id=?', 'T4_' + wfam)['name_en'].replace('Adept' + chr(39) + 's ', '')} · {kit[0]}",
            "equipment": eq}


def build_optimizer(content="mists", tier=6, classes="bow,crossbow", spec_ip=100, server="europe", city="Caerleon", pages=20,
                    shortlist=10, levels=None):
    """Rank builds for a PvPvE content by score and by score per silver, in budget bands."""
    key = encounter.resolve(content)
    title, kind, dtier, zone, continent = encounter.CONTENT[key]
    tier = int(tier or dtier)
    rules = pvp.zone_rules(zone)
    cls = [c.strip() for c in (classes.split(",") if isinstance(classes, str) else classes) if c.strip()]
    wfams = weapon_families(cls)
    if not wfams:
        raise AOError(f"No weapons for classes {cls}")
    levels = [int(x) for x in (levels.split(",") if isinstance(levels, str) else (levels or LEVELS))]
    # prices: every variant of every item at every level, in one request
    fams = set(wfams) | {f for _, k in KITS for f, _, _ in k} | {"OFF_TORCH", "CAPE"}
    var = {(f, lv): _variant_at(f, lv) for f in fams for lv in levels}
    prices = market.price_map(sorted({v for vs in var.values() for v in vs} | {i for i, _ in CONSUMABLES}), server, city, estimate=True)
    is_est = lambda i: prices.get(i, (None, ""))[1].startswith("≈")
    warn = list(market.WARNINGS)
    cheap = {}
    for k_, vs in var.items():
        priced = sorted((is_est(v), prices[v][0], v) for v in vs if prices.get(v, (None,))[0])  # real prices first
        if priced:
            cheap[k_] = priced[0][2]
    cons_cost = sum((prices.get(i, (None,))[0] or 0) * n for i, n in CONSUMABLES)
    lvl_price = {k_: prices[v][0] for k_, v in cheap.items()}

    def price_of(item):
        """Market price, or an estimate from the same item's priced neighbouring IP levels (geometric), flagged."""
        pr = prices.get(item, (None,))[0]
        if pr:
            return pr, is_est(item)
        fam, lv = gearcheck.advisor._family(item), q1("SELECT itempower FROM items WHERE id=?", item)
        lv = (lv["itempower"] // 100 * 100) if lv and lv["itempower"] else None  # level band
        known = sorted((l_, p_) for (f_, l_), p_ in lvl_price.items() if f_ == fam)
        if lv is None:
            return None, True
        if not known:  # never listed (rare artifacts): median of other artifact weapons of the same class at this IP
            art = lambda f: any(t in f for t in ARTIFACT_TAGS)
            peers = [p_ for (f_, l_), p_ in lvl_price.items() if l_ == lv and f_ in wfams and art(f_) == art(fam) and f_ != fam]
            return (statistics.median(peers), True) if peers else (None, True)
        lower = [x for x in known if x[0] < lv]
        upper = [x for x in known if x[0] > lv]
        if lower and upper:
            (l1, p1), (l2, p2) = lower[-1], upper[0]
            return p1 * (p2 / p1) ** ((lv - l1) / (l2 - l1)), True
        (l1, p1) = (lower or upper)[-1 if lower else 0]
        return p1 * 1.6 ** ((lv - l1) / 100), True  # ~+60% per 100 IP step (typical market ratio)
    # killboard field at the content's fight size (opponents at their own IP, after the zone cap)
    rows, fips, nev = pvp.field(rules["scale"], server, pages)
    field = [(pvp.build_pvp_player(r["loadout"], {"avg_ip": r["ip"] or pvp._pct(fips, 0.5) or 1100}, rules), r["n"]) for r in rows[:8]]
    if not field:
        raise AOError("Empty killboard field; raise pages")

    def evaluate(wfam, kit, level):
        lo = _loadout(wfam, kit, level, cheap)
        spec = {"spec_ip": spec_ip}  # IP from the actual items (artifact bonus included) + mastery
        pve = encounter.pve_summary(lo, key, ip_spec=spec, maps=4) or {"low": 0, "low_pess": 0, "elite": 1, "fame_h": 0, "minutes": 99}
        me = pvp.build_pvp_player(lo, spec, rules)
        tw = sum(w for _, w in field)
        duels = [(pvp.duel(me, o), w) for o, w in field]
        win = sum(d["win"] * w for d, w in duels) / tw
        live = 1 - sum(d["lose"] * w for d, w in duels) / tw
        est = [price_of(e["item"]) + (e.get("stack") or 1,) for e in lo["equipment"]]
        missing = sum(1 for pr, _, _ in est if pr is None)
        estimated = sum(1 for pr, flag, _ in est if pr is not None and flag)
        cost = sum((pr or 0) * n for pr, _, n in est)
        return {"wfam": wfam, "kit": kit[0], "level": level, "loadout": lo, "pve": pve, "win": win, "live": live, "cost": cost,
                "missing": missing, "estimated": estimated, "spells": [s for sl, s in me["spells"] if sl == "mainhand"]}

    # stage 1: every weapon × kit at the middle level; stage 2: the shortlist at every level
    mid = levels[len(levels) // 2]
    stage1 = [evaluate(w, k, mid) for w in wfams for k in KITS]
    fame_max = max(r["pve"]["fame_h"] for r in stage1) or 1

    def score(r):
        p = r["pve"]
        safe = 0.55 * p["low"] + 0.30 * p["low_pess"] + 0.15 * (1 - p["elite"])
        return (WEIGHTS["pve_safe"] * safe + WEIGHTS["pve_speed"] * min(p["fame_h"] / fame_max, 1)
                + WEIGHTS["pvp_win"] * r["win"] + WEIGHTS["pvp_live"] * r["live"])
    for r in stage1:
        r["score"] = score(r)
    best = sorted(stage1, key=lambda r: -r["score"])
    seen, short = set(), []
    for r in best:  # diversity: at most two kits per weapon in the shortlist
        if sum(1 for s in short if s["wfam"] == r["wfam"]) < 2:
            short.append(r)
        if len(short) >= shortlist:
            break
    results = list(stage1)
    for r in short:
        for lv in levels:
            if lv != mid:
                x = evaluate(r["wfam"], next(k for k in KITS if k[0] == r["kit"]), lv)
                x["score"] = score(x)
                results.append(x)
    priced = [r for r in results if r["cost"] and not r["missing"]]
    for r in priced:
        r["eff"] = r["score"] / (r["cost"] / 100_000)

    def row(r):
        p = r["pve"]
        names = ", ".join((q1("SELECT name_en FROM spells WHERE id=?", s) or {"name_en": s})["name_en"] for s in r["spells"])
        return (r["loadout"]["name"].split(" · ")[0], r["kit"], f"{r['level']} (+{spec_ip})", ("~" if r.get("estimated") else "") + money(r["cost"]),
                f"{p['low']:.0%} / {p['low_pess']:.0%}", f"{p['elite']:.0%}", f"{p['fame_h'] / 1e6:.2f}M", f"{r['win']:.0%}",
                f"{1 - r['live']:.0%}", f"{r['score']:.2f}", f"{r.get('eff', 0):.2f}", names)
    hdr = ["weapon", "armor kit", "base IP", "cost", "camps lowest HP @90/@50", "elite kills", "fame/h", "PvP win", "PvP die",
           "score", "score / 100k", "Q / W / E"]
    o = [f"## Build optimizer — {title} T{tier} · {', '.join(cls)} · {len(wfams)} weapons × {len(KITS)} armor kits × "
         f"{len(levels)} IP levels", "",
         f"Each build: camps simulated second by second (encounter_sim, 4 maps), duels vs the {rules['scale']}-fight killboard "
         f"meta ({nev} recent open-world kills, {len(field)} builds at their own IP"
         + (f", capped at {rules['cap']:.0f}" if rules["cap"] else "") + "), priced with the cheapest tier/enchant of every item "
         f"at the level ({city}) + consumables {money(cons_cost)}. Score = {WEIGHTS['pve_safe']:.0%} camp safety + "
         f"{WEIGHTS['pve_speed']:.0%} fame/h + {WEIGHTS['pvp_win']:.0%} PvP win + {WEIGHTS['pvp_live']:.0%} PvP survival."]
    if warn:
        o.append(f"_Prices incomplete: {'; '.join(warn)}_")
    for lo_b, hi_b in BANDS:
        band = [r for r in priced if lo_b <= r["cost"] < hi_b]
        if not band:
            continue
        top = sorted(band, key=lambda r: -r["score"])[:4]
        rng = f"{money(lo_b)}–{money(hi_b)}" if hi_b < 10 ** 12 else f"{money(lo_b)}+"
        o.append(f"\n### Budget {rng}\n" + table([row(r) for r in top], hdr))
        o.append("Buy (leader): " + ", ".join(f"`{e['item']}`" + (f" ×{e['stack']}" if e.get("stack", 1) > 1 else "")
                                               for e in top[0]["loadout"]["equipment"]))
    eff = sorted(priced, key=lambda r: -r["eff"])[:5]
    o.append("\n### Best value (score per 100k silver, any budget)\n" + table([row(r) for r in eff], hdr))
    top = max(priced, key=lambda r: r["score"]) if priced else None
    if top:
        o.append("\n**Strongest overall:** " + ", ".join(label(e["item"]) for e in top["loadout"]["equipment"][:6]))
    unp = sorted({r["loadout"]["name"].split(" · ")[0] for r in results if r["missing"]})
    if unp:
        o.append(f"_Skipped for missing prices: {', '.join(unp)}_")
    n_est = sum(1 for v in {v for vs in var.values() for v in vs} if is_est(v))
    o.append("_~ = some item prices are estimates: last known price, the same item's other IP levels, or game item value × the "
             "market ratio of priced items" + (f" ({n_est} item variants estimated this run — the market API was rate limited)" if n_est else "") + "._")
    o.append(f"\n_IP = base item power of the gear + {spec_ip} assumed from mastery (pass spec_ip). Camp numbers are calibrated on "
             "the real-outcome journal; PvP is the duel model vs open-world killboard builds — skill, positioning and cooldown "
             "timing are not modelled. Spells: picked for PvP per slot (damage, CC, escapes)._")
    return "\n".join(o)
