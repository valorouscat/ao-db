"""Build optimizer for PvPvE content: every weapon of the chosen classes × armor kits × item-power levels, each scored on
the content's monsters (encounter simulation) and against the killboard meta at the content's fight size (duel model),
priced with the cheapest tier/enchant reaching each IP level, ranked by score and by score per silver within budget bands.
"""
import json, math, statistics
from collections import Counter, defaultdict
from . import advisor, core, combat, encounter, gearcheck, market, pvp
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
PROFILES = {  # what the score rewards: camp safety, fame/h, winning fights, getting away from lost ones
    "balanced": WEIGHTS,
    "farm": {"pve_safe": 0.45, "pve_speed": 0.25, "pvp_win": 0.10, "pvp_live": 0.20},     # clear camps fast, escape players
    "hunter": {"pve_safe": 0.15, "pve_speed": 0.05, "pvp_win": 0.60, "pvp_live": 0.20},   # look for fights
    "survivor": {"pve_safe": 0.35, "pve_speed": 0.05, "pvp_win": 0.20, "pvp_live": 0.40},  # never lose the bag
}


PASSIVE_PREF = ("PASSIVE_INCREASED_DAMAGE", "PASSIVE_ARMOR_INCREASED_DAMAGE", "PASSIVE_ARMOR_BALANCE", "PASSIVE_BALANCE",
                "PASSIVE_MR_AR", "PASSIVE_ARMOR_MR_AR")


def armor_spells(fam):
    """(active, passive) for an armor piece the killboard shows without spells: the active with the best PvP value, the
    passive by preference (damage, then balance, then resistances)."""
    kit = combat.weapon_spells(q1("SELECT base_id FROM items WHERE id GLOB ?", f"T[4-8]_{fam}")["base_id"])
    ids = list(dict.fromkeys(o[0] for opts in kit.values() for o in opts))
    acts = [i for i in ids if not i.startswith("PASSIVE_") and i != "OUTOFCOMBATHEAL"]
    pas = [i for i in ids if i.startswith("PASSIVE_")]
    act = max(acts, key=pvp.pvp_value) if acts else None
    pa = next((x for x in PASSIVE_PREF if x in pas), pas[0] if pas else None)
    return act, pa


def meta_kits(scale, server="europe", pages=20, n=3, fixed=KITS):
    """The n most common head · armor · shoes sets of killers at a fight scale on the killboard (not already a fixed kit),
    with the cape most worn with each: [(name, [(family, active, passive)], cape family, kills)]."""
    sets, capes = Counter(), defaultdict(Counter)
    for e in advisor._events(server, max(1, min(pages, 20))):
        if pvp._fight_scale(e) != scale:
            continue
        eq = (e.get("Killer") or {}).get("Equipment") or {}
        fams = tuple(advisor._family((eq.get(s_) or {}).get("Type") or "") for s_ in ("Head", "Armor", "Shoes"))
        if all(fams):
            sets[fams] += 1
            cape = advisor._family((eq.get("Cape") or {}).get("Type") or "")
            if cape:
                capes[fams][cape] += 1
    known = {tuple(f for f, _, _ in k[1]) for k in fixed}
    out = []
    for fams, kills in sets.most_common():
        if len(out) >= n or kills < 2:
            break
        if fams in known or not all(q1("SELECT 1 FROM items WHERE id GLOB ?", f"T[4-8]_{f}") for f in fams):
            continue
        pieces = [(f, *armor_spells(f)) for f in fams]
        name = " · ".join(advisor._fam_name(f) for f in fams) + " (killboard)"
        cape = capes[fams].most_common(1)[0][0] if capes[fams] else "CAPE"
        out.append((name, pieces, cape, kills))
    return out


ESCAPE_POTION = ("T8_POTION_CLEANSE", 1)  # invisibility potion in the bag: kept in every set (the killboard shows only the slots)


def meta_consumables(scale, server="europe", pages=20, n=3):
    """The n food + potion pairs most used by killers at a fight scale (2+ kills, not the default set):
    [(label, [(item, stack)], kills)]; each set also carries the invisibility potion."""
    pairs = Counter()
    for e in advisor._events(server, max(1, min(pages, 20))):
        if pvp._fight_scale(e) != scale:
            continue
        eq = (e.get("Killer") or {}).get("Equipment") or {}
        f, p = ((eq.get(s_) or {}).get("Type") for s_ in ("Food", "Potion"))
        if f and p and q1("SELECT 1 FROM items WHERE id=?", f) and q1("SELECT 1 FROM items WHERE id=?", p):
            pairs[(f, p)] += 1
    default = tuple(i for i, _ in CONSUMABLES[:2])
    out = []
    for (f, p), kills in pairs.most_common():
        if len(out) >= n or kills < 2:
            break
        if (f, p) == default:
            continue
        out.append((f"{_short(f)} + {_short(p)}", [(f, 3), (p, 3)] + ([ESCAPE_POTION] if p != ESCAPE_POTION[0] else []), kills))
    return out


def _short(item):
    """'Beef Stew 8.0', 'Healing Potion 6.1' — the label without its ID and Minor/Major prefix."""
    n = label(item).split(" (`")[0]
    return n.split(" ", 1)[1] if n.split(" ", 1)[0] in ("Minor", "Major") else n


def _weights(profile, weights):
    """Score weights of a profile, overridden by 'pvp_win=0.6,pve_safe=0.2', normalised to sum 1."""
    if profile not in PROFILES:
        raise AOError(f"profile must be one of {', '.join(PROFILES)}")
    w = dict(PROFILES[profile])
    for part in (weights or "").replace(";", ",").split(","):
        if part.strip():
            k, _, v = part.partition("=")
            k = k.strip()
            if k not in w:
                raise AOError(f"Unknown weight {k!r}; use {', '.join(w)}")
            try:
                w[k] = max(float(v), 0.0)
            except ValueError:
                raise AOError(f"Weight {k} needs a number: {part!r}")
    tot = sum(w.values())
    if not tot:
        raise AOError("Weights sum to 0")
    return {k: v / tot for k, v in w.items()}


def weapon_families(classes):
    rows = q(f"SELECT id FROM items WHERE shopcat='weapons' AND sub1 IN ({','.join('?' * len(classes))}) AND tier=4 AND enchant=0 "
             "AND slot='mainhand' ORDER BY id", *classes)
    return [r["id"][3:] for r in rows]


def _variant_at(fam, level):
    """Item ids of a family whose base IP falls in the level's band [level, level+99] (e.g. 1000 = 4.3 / 5.2 / 6.1 / 7.0;
    artifact weapons carry +25…+100 IP, e.g. Bow of Badon 6.0 = 975 → band 900)."""
    return [r["id"] for r in q("SELECT id FROM items WHERE id GLOB ? AND itempower>=? AND itempower<?", f"T[0-9]_{fam}*", level, level + 100)
            if gearcheck.advisor._family(r["id"]) == fam]


def _loadout(wfam, kit, level, cheap, cons=None):
    """Concrete loadout at a base IP level, using the cheapest priced variant of every item."""
    pick = lambda fam: cheap.get((fam, level)) or (_variant_at(fam, level) or [f"T6_{fam}"])[0]
    w = pick(wfam)
    eq = [{"item": w}]
    if q1("SELECT json FROM items WHERE id=?", w) and core.item_json(w).get("@twohanded") != "true":
        eq.append({"item": pick("OFF_TORCH")})
    for fam, act, pas in kit[1]:
        eq.append({"item": pick(fam), "activeSpells": [act] if act else [], "passiveSpells": [pas] if pas else []})
    eq.append({"item": pick(kit[2] if len(kit) > 2 else "CAPE")})
    eq += [{"item": i, "stack": n} for i, n in (cons or CONSUMABLES)]
    return {"name": f"{core.q1('SELECT name_en FROM items WHERE id=?', 'T4_' + wfam)['name_en'].replace('Adept' + chr(39) + 's ', '')} · {kit[0]}",
            "equipment": eq}


def build_optimizer(content="mists", tier=6, classes="bow,crossbow", spec_ip=100, server="europe", city="Caerleon", pages=20,
                    shortlist=10, levels=None, budget=None, top=4, profile="balanced", weights=None, distinct=False, kits="both",
                    meta_kit_count=3, meta_consumable_count=3):
    """Rank builds for a PvPvE content by score and by score per silver, in budget bands."""
    W = _weights(profile, weights)
    key = encounter.resolve(content)
    title, kind, dtier, zone, continent = encounter.CONTENT[key]
    tier = int(tier or dtier)
    rules = pvp.zone_rules(zone)
    cls = [c.strip() for c in (classes.split(",") if isinstance(classes, str) else classes) if c.strip()]
    wfams = weapon_families(cls)
    if not wfams:
        raise AOError(f"No weapons for classes {cls}")
    levels = [int(x) for x in (levels.split(",") if isinstance(levels, str) else (levels or LEVELS))]
    if kits not in ("both", "fixed", "meta"):
        raise AOError("kits must be both, fixed or meta")
    meta = meta_kits(rules["scale"], server, pages, meta_kit_count) if kits != "fixed" else []
    if kits == "meta" and not meta:
        raise AOError("No head · armor · shoes set with 2+ kills at this fight size on the killboard; use kits=both")
    kitlist = (KITS if kits != "meta" else []) + meta
    conslist = [(f"{_short(CONSUMABLES[0][0])} + {_short(CONSUMABLES[1][0])}", CONSUMABLES, None)] + (
        meta_consumables(rules["scale"], server, pages, meta_consumable_count) if meta_consumable_count else [])
    # prices: every variant of every item at every level, in one request
    fams = set(wfams) | {f for k in kitlist for f, _, _ in k[1]} | {k[2] for k in meta} | {"OFF_TORCH", "CAPE"}
    var = {(f, lv): _variant_at(f, lv) for f in fams for lv in levels}
    prices = market.price_map(sorted({v for vs in var.values() for v in vs} | {i for c in conslist for i, _ in c[1]}), server, city, estimate=True)
    is_est = lambda i: prices.get(i, (None, ""))[1].startswith("≈") or market.is_thin(prices.get(i, (None, ""))[1])  # guesses
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
    opp_labels = [pvp.opponent_label(r) for r in rows[:8]]
    if not field:
        raise AOError("Empty killboard field; raise pages")

    def evaluate(wfam, kit, level, cons=conslist[0]):
        lo = _loadout(wfam, kit, level, cheap, cons[1])
        spec = {"spec_ip": spec_ip}  # IP from the actual items (artifact bonus included) + mastery
        pve = encounter.pve_summary(lo, key, ip_spec=spec, maps=4) or {"low": 0, "low_pess": 0, "elite": 1, "fame_h": 0, "minutes": 99}
        me = pvp.build_pvp_player(lo, spec, rules)
        tw = sum(w for _, w in field)
        duels = [(pvp.duel(me, o), w) for o, w in field]
        win, win_ci = pvp.weighted_ci([d["win"] for d, _ in duels], [w for _, w in duels])
        live = 1 - sum(d["lose"] * w for d, w in duels) / tw
        est = [price_of(e["item"]) + (e.get("stack") or 1,) for e in lo["equipment"]]
        missing = sum(1 for pr, _, _ in est if pr is None)
        estimated = sum(1 for pr, flag, _ in est if pr is not None and flag)
        cost = sum((pr or 0) * n for pr, _, n in est)
        return {"wfam": wfam, "kit": kit[0], "level": level, "loadout": lo, "cons": cons, "pve": pve, "win": win, "live": live, "cost": cost,
                "missing": missing, "estimated": estimated, "win_ci": win_ci, "duels": [d for d, _ in duels], "spells": [s for sl, s in me["spells"] if sl == "mainhand"]}

    # stage 1: every weapon × kit at the middle level; stage 2: the shortlist at every level
    mid = levels[len(levels) // 2]
    stage1 = [evaluate(w, k, mid) for w in wfams for k in kitlist]
    fame_max = max(r["pve"]["fame_h"] for r in stage1) or 1

    def score(r):
        p = r["pve"]
        safe = 0.55 * p["low"] + 0.30 * p["low_pess"] + 0.15 * (1 - p["elite"])
        return W["pve_safe"] * safe + W["pve_speed"] * min(p["fame_h"] / fame_max, 1) + W["pvp_win"] * r["win"] + W["pvp_live"] * r["live"]
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
        kit = next(k for k in kitlist if k[0] == r["kit"])
        best_c = r
        for c in conslist[1:]:  # food + potion sets from the killboard, tried at the middle level; the best one is kept
            x = evaluate(r["wfam"], kit, mid, c)
            x["score"] = score(x)
            results.append(x)
            best_c = max(best_c, x, key=lambda y: y["score"])
        for lv in levels:
            if lv != mid:
                x = evaluate(r["wfam"], kit, lv, best_c["cons"])
                x["score"] = score(x)
                results.append(x)
    priced = [r for r in results if r["cost"] and not r["missing"] and (not budget or r["cost"] <= budget)]
    for r in priced:
        r["eff"] = r["score"] / (r["cost"] / 100_000)

    def pick(rows, key, n):
        """Best n rows by key; with distinct, only each weapon's best row (its best armor kit and IP level)."""
        out, seen = [], set()
        for r in sorted(rows, key=key):
            if distinct and r["wfam"] in seen:
                continue
            seen.add(r["wfam"])
            out.append(r)
            if len(out) >= n:
                break
        return out

    def row(r):
        p = r["pve"]
        names = ", ".join((q1("SELECT name_en FROM spells WHERE id=?", s) or {"name_en": s})["name_en"] for s in r["spells"])
        return (r["loadout"]["name"].split(" · ")[0], r["kit"], r["cons"][0], f"{r['level']} (+{spec_ip})", ("~" if r.get("estimated") else "") + money(r["cost"]),
                f"{p['low']:.0%} / {p['low_pess']:.0%}", f"{p['elite']:.0%}", f"{p['fame_h'] / 1e6:.2f}M", pvp.pct_ci(r["win"], r["win_ci"]),
                f"{1 - r['live']:.0%}", f"{r['score']:.2f}", f"{r.get('eff', 0):.2f}", names)
    hdr = ["weapon", "armor kit", "food + potion", "base IP", "cost", "camps lowest HP @90/@50", "elite kills (worst camp)", "fame/h", "PvP win", "PvP die",
           "score", "score / 100k", "Q / W / E"]
    o = [f"## Build optimizer — {title} T{tier} · {', '.join(cls)} · {len(wfams)} weapons × {len(kitlist)} armor kits × "
         f"{len(levels)} IP levels", "",
         f"Each build: camps simulated second by second (encounter_sim, 4 maps), duels vs the {rules['scale']}-fight killboard "
         f"meta ({nev} recent open-world kills, {len(field)} builds at their own IP"
         + (f", capped at {rules['cap']:.0f}" if rules["cap"] else "") + "), priced with the cheapest tier/enchant of every item "
         f"at the level ({city}) + consumables ({conslist[0][0]} + invisibility potion: {money(cons_cost)}). Score ({profile}) = {W['pve_safe']:.0%} camp safety + "
         f"{W['pve_speed']:.0%} fame/h + {W['pvp_win']:.0%} PvP win + {W['pvp_live']:.0%} PvP survival."]
    if len(conslist) > 1:
        o.append("Killboard food + potion sets (tried on the shortlist, each with an invisibility potion in the bag): " + "; ".join(
            f"{c[0]} — {c[2]} kills" for c in conslist[1:]))
    if meta:
        o.append("Killboard kits (most worn by " + rules["scale"] + "-fight killers; spells picked for PvP): " + "; ".join(
            f"{k[0].replace(' (killboard)', '')} + {advisor._fam_name(k[2])} — {k[3]} kills, "
            + "/".join(core.q1('SELECT name_en FROM spells WHERE id=?', a)["name_en"] if a and core.q1('SELECT name_en FROM spells WHERE id=?', a)
                       else (a or "—") for _, a, _ in k[1]) for k in meta))
    if warn:
        o.append(f"_Prices incomplete: {'; '.join(warn)}_")
    for lo_b, hi_b in [(0, budget + 1)] if budget else BANDS:
        band = [r for r in priced if lo_b <= r["cost"] < hi_b]
        if not band:
            if budget:
                cheapest_ = min((r for r in results if r["cost"] and not r["missing"]), key=lambda r: r["cost"], default=None)
                o.append(f"\n### Budget ≤ {money(budget)}\nNo build fits the budget" + (
                    f"; the cheapest is {cheapest_['loadout']['name']} at {cheapest_['level']} IP for {money(cheapest_['cost'])}"
                    if cheapest_ else "") + ".")
            continue
        best_band = pick(band, lambda r: -r["score"], top)
        rng = (f"≤ {money(budget)}" if budget else f"{money(lo_b)}–{money(hi_b)}") if hi_b < 10 ** 12 else f"{money(lo_b)}+"
        o.append(f"\n### Budget {rng}\n" + table([row(r) for r in best_band], hdr))
        o.append("Buy (leader): " + ", ".join(f"`{e['item']}`" + (f" ×{e['stack']}" if e.get("stack", 1) > 1 else "")
                                               for e in best_band[0]["loadout"]["equipment"]))
    eff = pick(priced, lambda r: -r["eff"], 5)
    if eff:
        o.append(f"\n### Best value (score per 100k silver, {'within the budget' if budget else 'any budget'})\n"
                 + table([row(r) for r in eff], hdr))
    seen_w = set()  # the five best weapons, each in its best build
    lead = [r for r in sorted(priced, key=lambda r: -r["score"]) if not (r["wfam"] in seen_w or seen_w.add(r["wfam"]))][:5]
    if lead:
        o.append("\n### Matchups of the leaders (model win / die % vs each killboard build at its own IP; ✅ win ≥ 60, ⚠ die ≥ 40)\n"
                 + pvp.matchup_matrix([(f"{r['loadout']['name'].split(' · ')[0]} {r['level']}", r["duels"]) for r in lead], opp_labels))
    top = max(priced, key=lambda r: r["score"]) if priced else None
    if top:
        o.append("\n**Strongest overall:** " + ", ".join(label(e["item"]) for e in top["loadout"]["equipment"][:6]))
    unp = sorted({r["loadout"]["name"].split(" · ")[0] for r in results if r["missing"]})
    if unp:
        o.append(f"_Skipped for missing prices: {', '.join(unp)}_")
    n_est = sum(1 for v in {v for vs in var.values() for v in vs} if is_est(v))
    o.append("_~ = some item prices are estimates or thin markets (one or two listings, no sales history): last known price, craft "
             "cost (artifact gear), the same item's other IP levels, or game item value × the market ratio of priced items" + (f" ({n_est} item variants estimated this run" + (" — the market API was rate limited" if warn else ": no market data")
                + ")" if n_est else "") + "._")
    o.append(f"\n_IP = base item power of the gear + {spec_ip} assumed from mastery (pass spec_ip). Camp numbers are calibrated on "
             "the real-outcome journal; PvP is the duel model vs open-world killboard builds — skill, positioning and cooldown "
             "timing are not modelled. Spells: picked for PvP per slot (damage, CC, escapes)._")
    cal = encounter.sim_calibration(key)
    if cal["borrowed"]:
        o.append(f"⚠ {encounter.cal_warning(cal)}")
    o.append(advisor.kb_line())
    return "\n".join(o)


# ------------------------------------------------------------------ budget-constrained search over every item
SEARCH_SLOTS = ("mainhand", "offhand", "head", "armor", "shoes", "cape", "potion", "food")
SEARCH_WEIGHTS_PVE = {"pve_safe": 0.35, "pve_speed": 0.10, "pvp": 0.55}
MIN_GAIN = 0.002  # smaller score differences are model noise: keep the current pick
START = {"head": "HEAD_LEATHER_SET2", "armor": "ARMOR_LEATHER_SET1", "shoes": "SHOES_LEATHER_SET1", "cape": "CAPE",
         "offhand": "OFF_TORCH"}


def _gear_families(slot):
    rows = q("SELECT DISTINCT base_id FROM items WHERE slot=? AND id GLOB 'T[4-8]_*' AND id NOT LIKE '%GATHERER%' "
             "AND id NOT LIKE '%BACKPACK%' AND shopcat NOT IN ('skins', 'vanity') AND itempower>0", slot)
    return sorted({gearcheck.advisor._family(r["base_id"]) for r in rows})


def _consumables(slot):
    return [r["id"] for r in q("SELECT id FROM items WHERE slot=? AND id GLOB 'T[4-8]_*' ORDER BY id", slot)]


def build_search(content="corrupted_stalker", budget=300000, classes=None, weapons=3, levels=None, spec_ip=100, server="europe",
                 city="Caerleon", pages=10, passes=2, maps=4, pvp_weight=None, pvp_content=None):
    """Best builds for a content within a re-gear budget: for the top weapons, every item family of every slot at every IP level
    (cheapest priced tier/enchant), then every active/passive spell of the chosen item, Q/W/E of the weapon, offhands, capes,
    potions and food — coordinate search that keeps the total price ≤ budget."""
    budget = float(budget)
    try:
        pve_key = encounter.resolve(content)
        zone = encounter.CONTENT[pve_key][3]
    except AOError:
        pve_key, zone = None, pvp.resolve_zone(content)
    if pvp_content:  # fight rules of another zone (farm Mists camps, fight by black-zone rules…)
        zone = pvp.resolve_zone(pvp_content) or zone
    if not zone:
        raise AOError(f"Unknown content {content!r}")
    rules = pvp.zone_rules(zone)
    wp = SEARCH_WEIGHTS_PVE["pvp"] if pvp_weight is None else min(max(float(pvp_weight), 0.0), 1.0)
    weights = {"pvp": wp, "pve_safe": (1 - wp) * 0.78, "pve_speed": (1 - wp) * 0.22} if pve_key else {"pvp": 1.0}
    levels = [int(x) for x in (levels.split(",") if isinstance(levels, str) else (levels or LEVELS))]
    cls = [c.strip() for c in (classes.split(",") if isinstance(classes, str) else (classes or [])) if c.strip()]
    wfams = weapon_families(cls) if cls else [r["id"][3:] for r in q("SELECT id FROM items WHERE shopcat='weapons' AND slot='mainhand' "
                                                                       "AND tier=4 AND enchant=0 ORDER BY id")]
    if not wfams:
        raise AOError(f"No weapons for classes {cls}")
    fams = {"mainhand": wfams, **{s: _gear_families(s) for s in ("offhand", "head", "armor", "shoes", "cape")}}
    var = {(f, lv): _variant_at(f, lv) for s, fl in fams.items() for f in fl for lv in levels}
    cons = {s: _consumables(s) for s in ("potion", "food")}
    prices = market.price_map(sorted({v for vs in var.values() for v in vs} | {i for c in cons.values() for i in c}), server, city,
                              estimate=True)
    price = lambda i: prices.get(i, (None,))[0]
    cheap = {}
    for k_, vs in var.items():
        pr = sorted((price(v), v) for v in vs if price(v))
        if pr:
            cheap[k_] = pr[0][1]
    rows_f, fips, nev = pvp.field(rules["scale"], server, pages)
    field = [(pvp.build_pvp_player(r["loadout"], {"avg_ip": r["ip"] or pvp._pct(fips, 0.5) or 1100}, rules), r["n"]) for r in rows_f[:8]]
    if not field:
        raise AOError("Empty killboard field; raise pages")
    tw = sum(w for _, w in field)
    cache, n_eval = {}, [0]
    fame_ref = [1.0]

    def cost(eq):
        return sum((price(e["item"]) or float("inf")) * (e.get("stack") or 1) for e in eq.values())

    def evaluate(eq):
        key_ = json.dumps(eq, sort_keys=True)
        if key_ in cache:
            return cache[key_]
        c = cost(eq)
        if c > budget:
            cache[key_] = (-1e9, None)
            return cache[key_]
        n_eval[0] += 1
        lo = {"name": "search", "equipment": [eq[s] for s in SEARCH_SLOTS if s in eq]}
        try:
            me = pvp.build_pvp_player(lo, {"spec_ip": spec_ip}, rules)
            duels = [(pvp.duel(me, o), w) for o, w in field]
        except (AOError, KeyError, TypeError, ValueError, ZeroDivisionError):
            cache[key_] = (-1e9, None)
            return cache[key_]
        win = sum(d["win"] * w for d, w in duels) / tw
        die = sum(d["lose"] * w for d, w in duels) / tw
        res = {"cost": c, "win": win, "die": die, "ip": me["avg"], "eff": me["eff_avg"], "spells": me["spells"], "pve": None}
        s_pvp = (win - die + 1) / 2
        if pve_key:
            p = encounter.pve_summary(lo, pve_key, ip_spec={"spec_ip": spec_ip}, maps=maps) or \
                {"low": 0, "low_pess": 0, "elite": 1, "fame_h": 0, "minutes": 99}
            res["pve"] = p
            # share of pulls survived (smooth), lowest HP, elite risk — lowest HP alone saturates at 0 after one failed pull
            safe = 0.35 * (1 - p.get("failed", 1)) + 0.20 * (1 - p.get("failed_pess", 1)) + 0.15 * p["low"] + 0.15 * p["low_pess"] \
                + 0.15 * (1 - p["elite"])
            sc = weights["pve_safe"] * safe + weights["pve_speed"] * min(p["fame_h"] / fame_ref[0], 1) + weights["pvp"] * s_pvp
        else:
            sc = s_pvp
        res["score"] = sc
        cache[key_] = (sc, res)
        return cache[key_]

    def gear(fam, lv):
        i = cheap.get((fam, lv))
        return {"item": i} if i else None

    def two_handed(eq):
        return core.item_json(eq["mainhand"]["item"]).get("@twohanded") == "true"

    def start(wfam):
        lv = levels[0]
        eq = {"mainhand": gear(wfam, lv)}
        if not eq["mainhand"]:
            return None
        if not two_handed(eq) and gear(START["offhand"], lv):
            eq["offhand"] = gear(START["offhand"], lv)
        for s_ in ("head", "armor", "shoes", "cape"):
            g_ = gear(START[s_], lv)
            if g_:
                eq[s_] = g_
        for s_, iid in (("potion", "T4_POTION_HEAL"), ("food", "T4_MEAL_SOUP")):
            if price(iid):
                eq[s_] = {"item": iid}
        return eq if cost(eq) <= budget else None

    def spell_options(slot, iid):
        if slot == "mainhand":
            kit = combat.weapon_spells(q1("SELECT base_id FROM items WHERE id=?", iid)["base_id"])
            opts = [[o[0] for o in kit.get(s) or []] or [None] for s in ("1", "2", "3")]
            pas = [o[0] for o in kit.get("passive") or []] or [None]
            return [([x for x in (a, b, c) if x], [p_] if p_ else []) for a in opts[0] for b in opts[1] for c in opts[2] for p_ in pas]
        actives, passives = gearcheck._slot_spells(iid)
        return [([a[0]] if a else [], [p_[0]] if p_ else []) for a in ((actives[0] if actives else []) or [None])
                for p_ in (passives or [None])]

    def improve(eq, slot):
        best_sc = evaluate(eq)[0]
        best = eq
        if slot in ("potion", "food"):
            cands = [dict(eq, **{slot: {"item": i}}) for i in cons[slot] if price(i)]
            cands.append({k: v for k, v in eq.items() if k != slot})
        else:
            if slot == "offhand" and two_handed(eq):
                return eq
            fl = fams[slot] if slot != "mainhand" else [gearcheck.advisor._family(eq["mainhand"]["item"])]
            cands = []
            for f in fl:
                for lv in levels:
                    g_ = gear(f, lv)
                    if g_:
                        cands.append(dict(eq, **{slot: g_}))
            # no "drop the cape" candidate: the IP average runs over worn slots, so removing a cheap low-IP cape looks like
            # an IP gain while the game simply loses the cape's stats and passive
        for c in cands:
            sc = evaluate(c)[0]
            if sc > best_sc + MIN_GAIN:
                best_sc, best = sc, c
        if slot in ("mainhand", "head", "armor", "shoes") and slot in best:  # every spell combination of the chosen item
            iid = best[slot]["item"]
            for act, pas in spell_options(slot, iid):
                e = {"item": iid}
                if act:
                    e["activeSpells"] = act
                if pas:
                    e["passiveSpells"] = pas
                c = dict(best, **{slot: e})
                sc = evaluate(c)[0]
                if sc > best_sc + MIN_GAIN:
                    best_sc, best = sc, c
        return best

    # stage 1: every weapon family on the starting kit → fame reference and the weapon shortlist
    starts = {w: start(w) for w in wfams}
    starts = {w: e for w, e in starts.items() if e}
    if not starts:
        raise AOError(f"No weapon fits {money(budget)} with the cheapest kit at {levels[0]} IP")
    if pve_key:
        fames = [encounter.pve_summary({"name": "s", "equipment": list(e.values())}, pve_key, ip_spec={"spec_ip": spec_ip}, maps=maps)
                 for e in starts.values()]
        fame_ref[0] = max([f["fame_h"] for f in fames if f] or [1]) or 1
    ranked = sorted(starts, key=lambda w: -evaluate(starts[w])[0])
    results = []
    for w in ranked[:max(1, min(int(weapons), 10))]:
        eq = starts[w]
        for _ in range(max(1, min(int(passes), 4))):
            before = evaluate(eq)[0]
            for s_ in SEARCH_SLOTS:
                eq = improve(eq, s_)
            if evaluate(eq)[0] <= before + 1e-9:
                break
        results.append((evaluate(eq), eq))
    results.sort(key=lambda r: -r[0][0])

    def desc(e):
        sp = ", ".join(pvp._spell_name(x) for x in (e.get("activeSpells") or []) + (e.get("passiveSpells") or []))
        return label(e["item"]) + (f" — {sp}" if sp else "")
    o = [f"## Build search — {rules['title']} · budget {money(budget)}", "",
         f"{len(starts)} weapons screened, top {len(results)} searched: every item family of every slot × IP levels "
         f"{', '.join(map(str, levels))} (+{spec_ip} mastery) × every active/passive spell, offhands, capes, potions, food; "
         f"{n_eval[0]} builds simulated. PvP: calibrated duel model vs {len(field)} killboard builds ({rules['scale']} fights, "
         f"{nev} kills)" + (f"; PvE: encounter simulation of {encounter.CONTENT[pve_key][0]} ({maps} maps)" if pve_key else "")
         + ". Score = " + (f"{weights['pve_safe']:.0%} camp safety + {weights['pve_speed']:.0%} fame/h + "
                           f"{weights['pvp']:.0%} PvP (win − death, {rules['title']})" if pve_key else "PvP (win − death) vs the field") + "."]
    if market.WARNINGS:
        o.append(f"_Prices incomplete: {'; '.join(market.WARNINGS)}_")
    rows = []
    for (sc, r), eq in results:
        p = r["pve"]
        rows.append((label(eq["mainhand"]["item"]), money(r["cost"]), f"{r['ip']:.0f} → {r['eff']:.0f}", f"{r['win']:.0%}", f"{r['die']:.0%}",
                     f"{p['failed']:.0%} / {p['failed_pess']:.0%}" if p else "—", f"{p['fame_h'] / 1e6:.2f}M" if p else "—", f"{sc:.3f}"))
    o.append(table(rows, ["weapon", "cost", "IP (→ cap)", "PvP win", "PvP die", "pulls failed @90/@50 dodge", "fame/h", "score"]))
    def with_spells(slot, e):
        e = dict(e)
        if slot == "mainhand" and not e.get("activeSpells"):
            e["activeSpells"] = pvp.pick_pvp_spells(e["item"])
        elif slot in ("head", "armor", "shoes") and not e.get("activeSpells"):
            act, pas = pvp.pick_armor_spells(e["item"])
            if act:
                e["activeSpells"] = [act]
            if pas and not e.get("passiveSpells"):
                e["passiveSpells"] = [pas]
        return e
    results = [(r, {s: with_spells(s, e) for s, e in eq.items()}) for r, eq in results]
    for i, ((sc, r), eq) in enumerate(results[:3]):
        lo = {"version": 1, "name": f"build search {i + 1}", "icon": 20, "color": 10,
              "equipment": [dict(eq[s], **({"stack": 2} if s == "potion" else {})) for s in SEARCH_SLOTS if s in eq]}
        o.append(f"\n### #{i + 1} {label(eq['mainhand']['item'])} — {money(r['cost'])}\n"
                 + "\n".join(f"- {s}: {desc(eq[s])} · {money(price(eq[s]['item']) or 0)}" for s in SEARCH_SLOTS if s in eq)
                 + "\n```json\n" + json.dumps(lo, ensure_ascii=False, separators=(",", ":")) + "\n```")
    o.append("\n_Search: coordinate ascent per weapon (each slot fully enumerated given the others, repeated until no slot "
             "improves) — a local optimum of the full ~10¹² combination space, not a proof of the global one. Win chances: "
             "the PvP model is calibrated on killboard kills (IP + item families, 79.5% held-out; spells and consumables are not "
             "validated by data). Prices: cheapest listed tier/enchant per IP level, estimates where the market had none._")
    return "\n".join(o)
