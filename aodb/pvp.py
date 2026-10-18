"""PvP / PvPvE: zone rules and item-power soft caps (worldsettings.json), a player's kit against players (burst, sustained
damage, crowd control, escapes, defenses, purge/cleanse), a duel model between two loadouts, the open-world killboard meta
split by fight size, build search and a farm plan (reward multipliers vs death risk and re-gear cost).

Everything combat-related is a model on top of spells.json / items.json: compare options, don't read it as a guarantee.
"""
import functools, json, math, statistics
from collections import Counter, defaultdict
from . import core, combat, gearcheck, market, advisor
from .core import AOError, q1, label, money, table

# content key -> (title, worldsettings archetype, team size, killboard fight scale, entry requirement doc, modifier group)
ZONES = {
    "mists_yellow": ("Mists — yellow (solo, non-lethal)", "MISTS_SOLO_YELLOW", 1, "solo", None, "mistsyellow"),
    "mists_black": ("Mists — black (solo, full loot)", "MISTS_SOLO_BLACK", 1, "solo", None, "mistsblack"),
    "mists_duo": ("Mists — black (duo, full loot)", "MISTS_DUO_BLACK", 2, "small", None, "mistsblack"),
    "mists_dungeon": ("Mists dungeon — black (solo)", "MISTS_DUNGEON_SOLO_BLACK", 1, "solo", None, "mistsdungeonblack"),
    "corrupted_hunter": ("Corrupted Dungeon — Hunter (non-lethal)", "CORRUPTED_DUNGEON_BEGINNER", 1, "solo",
                         ("corrupteddungeons.json", "beginner"), "corrupted_beginner"),
    "corrupted_stalker": ("Corrupted Dungeon — Stalker (full loot)", "CORRUPTED_DUNGEON_INTERMEDIATE", 1, "solo",
                          ("corrupteddungeons.json", "intermediate"), "corrupted_intermediate"),
    "corrupted_slayer": ("Corrupted Dungeon — Slayer (full loot)", "CORRUPTED_DUNGEON_PRO", 1, "solo",
                         ("corrupteddungeons.json", "pro"), "corrupted_pro"),
    "hellgate_2v2": ("Hellgate 2v2 (lethal)", "HELL_2V2_LETHAL", 2, "small", ("hellgate.json", "hellgate_2v2"), "hell_lethal_2v2"),
    "hellgate_5v5": ("Hellgate 5v5 (lethal)", "HELL_5V5_LETHAL", 5, "group", ("hellgate.json", "hellgate_5v5"), "hell_lethal_5v5"),
    "hellgate_10v10": ("Hellgate 10v10 (lethal)", "HELL_10V10_LETHAL", 10, "group", None, "hell_lethal_10v10"),
    "hellgate_2v2_nl": ("Hellgate 2v2 (non-lethal)", "HELL_2V2_NON_LETHAL", 2, "small", ("hellgate.json", "hellgate_2v2_non_lethal"),
                        "hell_nonlethal_2v2"),
    "arena_1v1": ("Arena 1v1", "ARENA_1V1", 1, "solo", None, None),
    "crystal_5v5": ("Crystal arena 5v5", "ARENA_CRYSTAL", 5, "group", None, None),
    "yellow": ("Open world — yellow zone", "YELLOW", 1, "solo", None, "yellow"),
    "red": ("Open world — red zone (full loot)", "RED", 1, "solo", None, "red"),
    "black": ("Open world — black zone (full loot)", "BLACK", 1, "solo", None, "black"),
    "roads": ("Roads of Avalon (full loot)", "RD_TUNNEL", 1, "solo", None, "tunnel"),
}
ALIASES = [("slayer", "corrupted_slayer"), ("слеер", "corrupted_slayer"), ("stalker", "corrupted_stalker"), ("сталкер", "corrupted_stalker"),
           ("hunter", "corrupted_hunter"), ("хантер", "corrupted_hunter"), ("corrupt", "corrupted_stalker"), ("проклят", "corrupted_stalker"),
           ("mists_duo", "mists_duo"), ("duo", "mists_duo"), ("дуо", "mists_duo"), ("yellow mist", "mists_yellow"), ("жёлт", "mists_yellow"),
           ("желт", "mists_yellow"), ("mist dungeon", "mists_dungeon"), ("mist", "mists_black"), ("мист", "mists_black"),
           ("туман", "mists_black"), ("2v2", "hellgate_2v2"), ("5v5", "hellgate_5v5"), ("10v10", "hellgate_10v10"), ("hellgate", "hellgate_2v2"),
           ("адск", "hellgate_2v2"), ("врата", "hellgate_2v2"), ("arena", "arena_1v1"), ("арен", "arena_1v1"), ("crystal", "crystal_5v5"),
           ("road", "roads"), ("авалон", "roads"), ("avalon", "roads"), ("black", "black"), ("чёрн", "black"), ("черн", "black"),
           ("red", "red"), ("красн", "red"), ("yellow", "yellow")]
SCALES = {"solo": (1, 1), "small": (2, 3), "group": (4, 99)}
# Encounters with hostile players per hour of farming — ASSUMPTIONS (no public data); override with encounters_per_hour.
ENCOUNTERS = {"mists_black": 1.5, "mists_duo": 1.5, "mists_dungeon": 1.0, "mists_yellow": 1.5, "corrupted_hunter": 2.0,
              "corrupted_stalker": 2.0, "corrupted_slayer": 2.0, "roads": 1.0, "black": 1.0, "red": 0.7, "yellow": 0.5,
              "hellgate_2v2": 4.0, "hellgate_5v5": 4.0, "hellgate_10v10": 4.0, "hellgate_2v2_nl": 4.0, "arena_1v1": 6.0, "crystal_5v5": 4.0}
OPENING = 2.0       # seconds before damage lands (approach / first casts)
CC_CAP = 0.45       # one player keeps the other disabled at most 45% of the fight
DUEL_K = 3.0        # steepness of win probability vs time-to-kill ratio
CC_CYCLE = 10.0     # CC from spells with shorter cooldowns is conditional (stacks/charges): count at most once per 10 s
ESCAPE_CYCLE = 8.0  # same for dashes/immunities on charge or sequence spells (recast 0)
CC_MAX30 = 8.0      # hard CC (and roots) per 30 s on one target, after diminishing returns


def resolve_zone(content):
    s = (content or "").lower().strip()
    if s in ZONES:
        return s
    for a, k in ALIASES:
        if a in s:
            return k
    raise AOError(f"Unknown PvP content {content!r}. Known: {', '.join(ZONES)}")


@functools.lru_cache(maxsize=None)
def zone_rules(key):
    title, arch, team, scale, entry, mod = ZONES[key]
    r = q1("SELECT json FROM docs WHERE file='worldsettings.json' AND key=?", arch)
    if not r:
        raise AOError(f"Archetype {arch} not in worldsettings.json (data dump changed?)")
    a = json.loads(r["json"])
    out = {"key": key, "title": title, "archetype": arch, "team": team, "scale": scale,
           "lethal": a.get("@playersarelethal") == "true", "pvprule": a.get("@pvprule"),
           "cap": core.num(a.get("@itempowersoftcap")) or 0, "factor": core.num(a.get("@itempowerscalingfactor")) or 0,
           "knockdown": core.num(a.get("@knockdowngetuptimeseconds_pvp")), "entry_ip": None, "loot": 1.0, "silver": 1.0, "fame": 1.0}
    if arch.startswith("ARENA"):  # 'lethal' there means dying ends your match; arena gear is never dropped
        out["lethal"] = False
    if entry:
        e = q1("SELECT json FROM docs WHERE file=? AND key=?", *entry)
        if e:
            out["entry_ip"] = core.num(json.loads(e["json"]).get("@itempowerrequirement"))
    if mod:
        m = q1("SELECT loot, silver, fame FROM modifiers WHERE grp=? ORDER BY source='zone' DESC LIMIT 1", mod)
        if m:
            out.update(loot=m["loot"] or 1.0, silver=m["silver"] or 1.0, fame=m["fame"] or 1.0)
    return out


def effective_ip(ip, rules):
    """Item power after the zone's soft cap: IP above the cap counts at `factor` (0 = hard cap)."""
    cap, f = rules["cap"], rules["factor"]
    return ip if not cap or ip <= cap else cap + (ip - cap) * f


# ------------------------------------------------------------------ spells vs players
class PvpWalk:
    """PvP-relevant effects of one cast: CC on enemies, escapes, defenses, purge/cleanse, anti-heal, armor shred."""
    HARD = ("stun", "silence", "fear", "sleep", "imprison", "cannotattack")

    def __init__(self):
        self.v = defaultdict(float)
        self.seen = set()

    def spell(self, sid, depth=0):
        d = combat.spell_json(sid)
        if not d or sid in self.seen or depth > 6:
            return
        self.seen.add(sid)
        self.walk(d, depth)

    def walk(self, n, depth):
        if not isinstance(n, dict) or depth > 10:
            return
        v = self.v
        for k, val in n.items():
            if k.startswith("@") or k in combat.SKIP_KEYS:
                continue
            for ch in combat._aslist(val):
                if not isinstance(ch, dict):
                    continue
                t = (ch.get("@target") or "").lower()
                enemy, own = "enemy" in t, t in ("self", "", "caster")
                sec = core.num(ch.get("@time")) or 0
                if k in self.HARD and enemy:
                    v["cc_hard"] += sec
                elif k == "knockback" and enemy:
                    v["cc_hard"] += 0.5
                elif k == "root" and enemy:
                    v["root"] += sec
                elif k == "dash":
                    v["dash"] += 1
                elif k == "buffovertime":
                    typ, value = ch.get("@type"), core.num(ch.get("@value")) or 0
                    if typ == "movespeedbonus" and enemy and value < 0:
                        v["slow"] += -value * sec
                    elif typ == "movespeedbonus" and own and value > 0:
                        v["speed"] += value * sec
                    elif typ in ("physicalarmor", "magicresistance") and own and value > 0:
                        v["resist"] += value * sec / 2
                    elif typ in ("physicalarmor", "magicresistance") and enemy and value < 0:
                        v["shred"] += -value * sec / 2
                    elif typ == "healmodifier" and enemy and value < 0:
                        v["antiheal"] += -value * sec
                    elif typ == "crowdcontrolresistance" and own and value > 0:
                        v["ccres"] += value * sec
                elif k in ("invincibility", "nothittable", "notselectable") and own:
                    v["invuln"] += sec
                elif k == "spellimmunity" and own:
                    v["invuln"] += sec * 0.5  # immune to one category only
                elif k == "invisibility" and own:
                    v["invis"] += sec
                elif k == "cceffectimmunity" and own:
                    v["ccimmune"] = max(v["ccimmune"], sec)
                elif k == "removeactiveeffects":
                    cat = (ch.get("@category") or "").lower()
                    if enemy and cat in ("buff", "buff_damageshield", "heal", "movementbuff", "invisibility"):
                        v["purge"] += 1
                    elif t in ("self", "all") and cat in ("crowdcontrol", "debuff"):
                        v["cleanse"] += 1
                for a in ("@spell", "@effect"):
                    ref = ch.get(a)
                    if ref and ref != "none":
                        self.spell(ref, depth + 1)
                self.walk(ch, depth + 1)


@functools.lru_cache(maxsize=None)
def pvp_spell(sid):
    """Per-cast PvP profile of a spell (base values, before item-power scaling)."""
    d = combat.spell_json(sid)
    if not d:
        return None
    w = PvpWalk()
    w.spell(sid)
    p = combat.spell_profile(sid, "players") or {"dmg": 0.0, "cycle": core.num(d.get("@recastdelay")) or 1.0, "aoe": False, "types": {}}
    dfn = combat.spell_defense(sid) or {}
    cycle = max(p["cycle"] or 1.0, combat.GCD)
    out = {} if len(w.seen) > combat.FANOUT else dict(w.v)  # copy/random spells: effects of every copied spell are not ours
    out.update(dmg=p["dmg"], cycle=cycle, aoe=p["aoe"], types=p.get("types") or {},
               shield=dfn.get("shield_ps", 0) * cycle, heal=dfn.get("heal_self_ps", 0) * cycle, lifesteal=dfn.get("lifesteal", 0))
    return out


def pvp_value(sid):
    """Single number to pick a spell for PvP: damage + crowd control + escapes + defenses (base units)."""
    p = pvp_spell(sid) or {}
    if not p:
        return 0.0
    c = p["cycle"]
    per = lambda x, floor=0.0: x * 30 / max(c, floor)  # per 30 s (conditional CC / charge escapes floored like the kit)
    return (min(p["dmg"] / c, combat.MAX_SPELL_DPS) * 3 + per(p.get("cc_hard", 0), CC_CYCLE) * 25 + per(p.get("root", 0), CC_CYCLE) * 8
            + per(p.get("slow", 0)) * 4 + per(min(p.get("dash", 0), 1), ESCAPE_CYCLE) * 10 + per(p.get("invuln", 0), ESCAPE_CYCLE) * 20
            + per(p.get("invis", 0), ESCAPE_CYCLE) * 4 + per(p.get("shield", 0) + p.get("heal", 0)) / 15
            + per(p.get("purge", 0)) * 15 + per(p.get("cleanse", 0)) * 15 + per(p.get("ccimmune", 0), ESCAPE_CYCLE) * 10)


def pick_pvp_spells(item_id):
    """Q/W/E for PvP when a loadout (or killboard build) has no spells selected."""
    base = q1("SELECT base_id FROM items WHERE id=?", item_id)
    if not base:
        return []
    kit = combat.weapon_spells(base["base_id"])
    return [max(kit[s], key=lambda o: pvp_value(o[0]))[0] for s in ("1", "2", "3") if kit.get(s)]


# ------------------------------------------------------------------ players
COMBAT_SPELL_SLOTS = ("mainhand", "head", "armor", "shoes")


def build_pvp_player(lo, ip_spec=None, rules=None, intents=None):
    """Loadout -> PvP player: per-slot IP after the zone soft cap, item stats, kit metrics vs players."""
    name, entries = gearcheck.parse_loadout(lo)
    raw = gearcheck._raw_loadout(lo)
    ip_spec = ip_spec or {}
    gearcheck.apply_intents(entries, gearcheck.parse_intents(intents or raw.get("intents")))
    weapon = next((e for e in entries if e["row"]["slot"] == "mainhand" and not e["inventory"]), None)
    if weapon and not weapon["active"]:
        weapon["active"], weapon["auto_slots"] = pick_pvp_spells(weapon["id"]), ["1", "2", "3"]
    avg, rows = gearcheck.loadout_ip(entries, ip_spec.get("spec_ip", 0), ip_spec.get("weapon_ip"),
                                     ip_spec.get("slot_ip") or raw.get("slot_ip"), ip_spec.get("avg_ip") or raw.get("avg_ip"))
    eff_rows = [[r[0], effective_ip(r[1], rules) if rules else r[1], *r[2:]] for r in rows]
    eff_avg = sum(r[1] * r[2] for r in eff_rows) / max(sum(r[2] for r in eff_rows), 1)
    hp_given = ip_spec.get("hp") or raw.get("hp")
    stats = gearcheck.player_stats(entries, eff_rows, hp_given if not (rules and rules["cap"]) else None)
    wip = next((r[1] for r in eff_rows if r[0] == "mainhand"), eff_avg)
    k = {"burst": 0.0, "dps": 0.0, "cc30": 0.0, "root30": 0.0, "slow30": 0.0, "dash30": 0.0, "speed30": 0.0, "invis30": 0.0,
         "invuln30": 0.0, "ccimmune30": 0.0, "sustain30": 0.0, "resist30": 0.0, "purge": 0, "cleanse": 0, "antiheal": 0.0,
         "shred30": 0.0, "lifesteal": 0.0}
    types = Counter()
    spells = []
    if weapon:
        aa = combat._autoattack_dps(weapon["id"])
        k["burst"] += aa * 3
        k["dps"] += aa
        types["physical"] += aa
    for e in entries:
        if e["inventory"] or e["row"]["slot"] not in COMBAT_SPELL_SLOTS:
            continue
        for sid in e["active"]:
            p = pvp_spell(sid)
            if not p:
                continue
            spells.append((e["row"]["slot"], sid))
            if p["cycle"] <= 30:
                k["burst"] += p["dmg"]
            sp_dps = min(p["dmg"] / p["cycle"], combat.MAX_SPELL_DPS)
            k["dps"] += sp_dps
            for t, share in p["types"].items():
                types[t] += sp_dps * share
            for src, dst, floor in (("cc_hard", "cc30", CC_CYCLE), ("root", "root30", CC_CYCLE), ("slow", "slow30", 0),
                                    ("dash", "dash30", ESCAPE_CYCLE), ("speed", "speed30", ESCAPE_CYCLE), ("invis", "invis30", ESCAPE_CYCLE),
                                    ("invuln", "invuln30", ESCAPE_CYCLE), ("ccimmune", "ccimmune30", ESCAPE_CYCLE),
                                    ("resist", "resist30", 0), ("shred", "shred30", 0)):
                k[dst] += min(p.get(src, 0), 1 if src == "dash" else 1e9) * 30 / max(p["cycle"], floor)
            k["sustain30"] += (p["shield"] + p["heal"]) * 30 / p["cycle"]
            k["purge"] += p.get("purge", 0) > 0
            k["cleanse"] += p.get("cleanse", 0) > 0
            k["antiheal"] = max(k["antiheal"], p.get("antiheal", 0))
            k["lifesteal"] += p["lifesteal"]
    for e in entries:  # potions / food (lifesteal, cleanse, heal, invisibility)
        cs = core.item_json(e["id"]).get("@consumespell")
        if cs and (e["row"]["slot"] in ("food", "potion") or e["inventory"]):
            p = pvp_spell(cs)
            if p:
                k["sustain30"] += (p["shield"] + p["heal"]) * min(30 / max(p["cycle"], 30), 1)
                k["lifesteal"] += p["lifesteal"]
                k["cleanse"] += p.get("cleanse", 0) > 0
                k["invis30"] += p.get("invis", 0) * min(30 / max(p["cycle"], 30), 1)
    k["cc30"], k["root30"] = min(k["cc30"], CC_MAX30), min(k["root30"], CC_MAX30)  # diminishing returns on repeated CC
    tot = sum(types.values()) or 1
    mix = {t: v / tot for t, v in types.items()} or {"physical": 1.0}
    ap = ((core.num(core.item_json(weapon["id"]).get("@abilitypower")) or 100) / 100) if weapon else 1.0
    ranged = bool(weapon) and (core.num(core.item_json(weapon["id"]).get("@attackrange")) or 3) >= 8
    bonus = mix.get("physical", 0) * (stats["physicalspelldamagebonus"] + stats["physicalattackdamagebonus"]) / 2 \
        + mix.get("magic", 0) * (stats["magicspelldamagebonus"] + stats["magicattackdamagebonus"]) / 2
    return {"name": name, "entries": entries, "weapon": weapon, "rows": rows, "eff_rows": eff_rows, "avg": avg, "eff_avg": eff_avg,
            "wip": wip, "stats": stats, "kit": k, "mix": mix, "ap": ap, "ranged": ranged, "spells": spells,
            "scale": combat.PER_IP ** ((wip - 1000) / 100) * (1 + bonus)}


def _mit(attacker, target, shred30=0.0):
    st = target["stats"]
    arm = max(st["physicalarmor"] - shred30 / 30, 0)
    mres = max(st["magicresistance"] - shred30 / 30, 0)
    m = attacker["mix"].get("physical", 0) * combat.mitigation(arm) + attacker["mix"].get("magic", 0) * combat.mitigation(mres)
    return m * (1 - min(st.get("bonusdefensevsplayers", 0) or 0, 0.5))


def _ttk(a, b):
    """Seconds for `a` to kill `b`: burst, then sustained damage minus b's sustain; b's CC on a and b's immunity windows."""
    ka, kb = a["kit"], b["kit"]
    m = _mit(a, b, ka["shred30"])
    burst = ka["burst"] * a["scale"] * m
    dps = ka["dps"] * a["scale"] * m
    cc_on_a = min(kb["cc30"] / 30 * (0.5 if ka["cleanse"] else 1) * max(0.0, 1 - ka["ccimmune30"] / 30), CC_CAP)
    dps *= (1 - cc_on_a) * max(0.0, 1 - min(kb["invuln30"] / 30, 0.4))
    heal_mult = 1 - min(ka["antiheal"], 0.5)
    sustain = (kb["sustain30"] / 30) * b["scale"] / max(b["ap"], 0.01) * heal_mult + kb["lifesteal"] * kb["dps"] * b["scale"] * 0.3
    sustain += kb["resist30"] / 30 * 0  # resist buffs act through mitigation below
    ehp = b["stats"]["hp"] * (1 + kb["resist30"] / 30 / 200)
    net = max(dps - sustain, 0.15 * dps, 1e-6)
    return OPENING + max(ehp - burst, 0) / net


def duel(a, b):
    """{'win', 'lose', 'disengage', 'ttk_ab', 'ttk_ba'} for player a against player b (model)."""
    t_ab, t_ba = _ttk(a, b), _ttk(b, a)
    p = 1 / (1 + (t_ab / t_ba) ** DUEL_K)
    loser, winner = (b, a) if p >= 0.5 else (a, b)
    lk, wk = loser["kit"], winner["kit"]
    esc = 0.1 + 0.08 * lk["dash30"] + 0.04 * lk["speed30"] + 0.02 * lk["invis30"] + 0.02 * lk["invuln30"] \
        - 0.02 * wk["slow30"] - 0.03 * wk["cc30"] - 0.02 * wk["root30"] - (0.05 if winner["ranged"] else 0)
    esc = min(max(esc, 0.0), 0.6)
    if p >= 0.5:  # b may get away
        return {"win": p * (1 - esc), "lose": 1 - p, "disengage": p * esc, "ttk_ab": t_ab, "ttk_ba": t_ba}
    return {"win": p, "lose": (1 - p) * (1 - esc), "disengage": (1 - p) * esc, "ttk_ab": t_ab, "ttk_ba": t_ba}


# ------------------------------------------------------------------ killboard field
def _fight_scale(e):
    n = e.get("numberOfParticipants") or len(e.get("Participants") or []) or 1
    return next(s for s, (lo, hi) in SCALES.items() if lo <= n <= hi) if n <= 99 else "group"


def _build_sig(eq):
    fam = lambda s: advisor._family((eq.get(s) or {}).get("Type") or "")
    return (fam("MainHand"), fam("OffHand"), fam("Head"), fam("Armor"), fam("Shoes"))


def _eq_loadout(eq, name):
    slots = ("MainHand", "OffHand", "Head", "Armor", "Shoes", "Cape", "Potion", "Food")
    return {"name": name, "equipment": [{"item": eq[s]["Type"], "quality": eq[s].get("Quality") or 1} for s in slots
                                        if (eq.get(s) or {}).get("Type") and q1("SELECT 1 FROM items WHERE id=?", eq[s]["Type"])]}


def field(scale, server="europe", pages=10, ip_range=None, top=10):
    """Killboard builds at a fight scale: [{sig, kills, deaths, kd, ip, loadout (representative killer gear)}], opponent IPs."""
    evs = advisor._events(server, max(1, min(pages, 20)))
    stats = defaultdict(lambda: {"kills": 0, "deaths": 0, "ips": [], "eq": None})
    ips = []
    for e in evs:
        if _fight_scale(e) != scale:
            continue
        for side in ("Killer", "Victim"):
            p = e.get(side) or {}
            eq = p.get("Equipment") or {}
            ip = p.get("AverageItemPower") or 0
            if not (eq.get("MainHand") or {}).get("Type") or (ip_range and not ip_range[0] <= ip <= ip_range[1]):
                continue
            ips.append(ip)
            s = stats[_build_sig(eq)]
            s["kills" if side == "Killer" else "deaths"] += 1
            if side == "Killer":
                s["ips"].append(ip)
                s["eq"] = s["eq"] or eq
            elif not s["eq"]:
                s["eq"] = eq
    rows = []
    for sig, s in stats.items():
        n = s["kills"] + s["deaths"]
        if n < 2 or not s["eq"]:
            continue
        rows.append({"sig": sig, "kills": s["kills"], "deaths": s["deaths"], "n": n, "kd": s["kills"] / max(s["deaths"], 1),
                     "ip": statistics.median(s["ips"]) if s["ips"] else None, "loadout": _eq_loadout(s["eq"], advisor._fam_name(sig[0]))})
    rows.sort(key=lambda r: (-r["n"], -r["kd"]))
    return rows[:top], ips, len(evs)


def _sig_text(sig):
    return " + ".join(advisor._fam_name(x) for x in sig if x)


def _pct(ips, p):
    s = sorted(ips)
    return s[min(int(p * len(s)), len(s) - 1)] if s else None


# ------------------------------------------------------------------ tools
def pvp_rules(content=None):
    """Rules of PvP / PvPvE content from the game data: lethality, soft cap, entry IP, team size, reward multipliers."""
    keys = [resolve_zone(content)] if content else list(ZONES)
    rows = []
    for k in keys:
        r = zone_rules(k)
        cap = f"{r['cap']:.0f} (above: ×{r['factor']:g})" if r["cap"] else "none"
        rows.append((k, r["title"], "full loot" if r["lethal"] else "no item loss", r["pvprule"], cap,
                     f"{r['entry_ip']:.0f}" if r["entry_ip"] else "", r["team"], f"×{r['loot']:g} / ×{r['silver']:g} / ×{r['fame']:g}"))
    o = ["## PvP / PvPvE content rules (worldsettings.json archetypes, entry requirements, ClusterDangerBonus)", "",
         table(rows, ["key", "content", "death", "PvP rule", "IP soft cap", "entry IP", "team", "loot / silver / fame"])]
    o.append("\n_Soft cap: item power above the cap counts at the factor (×0 = hard cap), applied per item here. Effective IP = "
             "cap + (IP − cap) × factor. Entry IP is the base requirement to queue/enter._")
    if content:
        from . import patchnotes
        topic = {"corrupted": "corrupted dungeon", "mists": "mists", "hellgate": "hellgate", "arena": "arena", "crystal": "crystal",
                 "roads": "roads of avalon"}.get(keys[0].split("_")[0], keys[0].replace("_", " "))
        pn = patchnotes.top_lines(topic, 4)
        if pn:
            o.append(f"\n### Recent patch notes ({topic})\n" + pn)
    return "\n".join(o)


def _player_rows(players, rules):
    rows = []
    for p in players:
        k = p["kit"]
        sp = ", ".join(f"{(q1('SELECT name_en FROM spells WHERE id=?', s) or {'name_en': s})['name_en']}" for _, s in p["spells"])
        rows.append((p["name"], f"{p['avg']:.0f} → {p['eff_avg']:.0f}" if rules["cap"] else f"{p['avg']:.0f}",
                     f"{p['stats']['hp']:,.0f}", f"{k['burst'] * p['scale']:,.0f}", f"{k['dps'] * p['scale']:,.0f}",
                     ", ".join(x for x in (f"hard {k['cc30']:.1f}s" if k["cc30"] else "", f"root {k['root30']:.1f}s" if k["root30"] else "",
                                           f"slow {k['slow30']:.1f}" if k["slow30"] else "") if x) or "—",
                     ", ".join(x for x in (f"{k['dash30']:.1f} dash" if k["dash30"] else "", f"speed {k['speed30']:.1f}" if k["speed30"] else "",
                                           f"invis {k['invis30']:.0f}s" if k["invis30"] else "") if x) or "—",
                     f"{k['sustain30'] * p['scale']:,.0f}" + (f", immune {k['invuln30']:.1f}s" if k["invuln30"] else ""),
                     ", ".join(x for x in ("cleanse" if k["cleanse"] else "", "purge" if k["purge"] else "",
                                           f"anti-heal {k['antiheal']:.0%}" if k["antiheal"] else "") if x) or "—", sp))
    return table(rows, ["build", "IP (→ after cap)", "HP", "burst", "DPS", "CC /30s", "escape /30s", "shield+heal /30s", "utility",
                        "spells used"])


def pvp_check(loadout, content="mists_black", ips=None, intents=None, opponent=None, server="europe", city="Caerleon",
              pages=10, price=True):
    """PvP readiness of a loadout for a content: effective IP after the soft cap, kit vs players, matchups vs the killboard meta
    at that fight size (or a given opponent loadout), and re-gear cost."""
    key = resolve_zone(content)
    rules = zone_rules(key)
    ip_spec = gearcheck._parse_ips(ips, 1)[0] if ips else {}
    me = build_pvp_player(loadout, ip_spec, rules, intents)
    o = [f"## PvP check: “{me['name']}” → {rules['title']}", "",
         f"**Rules:** {'full loot' if rules['lethal'] else 'no item loss'}, PvP {rules['pvprule']}, "
         + (f"IP soft cap {rules['cap']:.0f} (above ×{rules['factor']:g})" if rules["cap"] else "no IP cap")
         + (f", entry {rules['entry_ip']:.0f} IP" if rules["entry_ip"] else "") + f", team {rules['team']}."]
    if rules["entry_ip"] and me["avg"] < rules["entry_ip"]:
        o.append(f"⛔ Average IP {me['avg']:.0f} is below the entry requirement {rules['entry_ip']:.0f}.")
    if rules["cap"] and me["avg"] > rules["cap"]:
        wasted = me["avg"] - me["eff_avg"]
        o.append(f"💸 {wasted:.0f} IP above the soft cap is lost (effective {me['eff_avg']:.0f}): gear beyond ~{rules['cap']:.0f} IP "
                 "buys little here — a cheaper set near the cap performs almost the same.")
    o += ["", _player_rows([me], rules)]
    gaps = []
    k = me["kit"]
    if not k["cleanse"] and not k["ccimmune30"]:
        gaps.append("no cleanse / CC immunity (a stun-lock decides 1v1s)")
    if not k["dash30"] and not k["invis30"] and not k["invuln30"]:
        gaps.append("no escape (dash, invisibility or immunity)")
    if not k["cc30"] and not k["root30"]:
        gaps.append("no crowd control to secure kills")
    if gaps:
        o.append("⚠ " + "; ".join(gaps))
    opps, field_note = [], ""
    if opponent:
        opps = [(build_pvp_player(opponent, None, rules), 1, "given opponent")]
    else:
        try:
            rows, fips, nev = field(rules["scale"], server, pages)
            for r in rows[:8]:
                opp_ip = r["ip"] or _pct(fips, 0.5) or 1100
                opps.append((build_pvp_player(r["loadout"], {"avg_ip": opp_ip}, rules), r["n"],
                             f"{r['kills']}/{r['deaths']} K/D {r['kd']:.2f}"))
            field_note = (f"killboard {server}: {nev} recent open-world kills, fights of scale '{rules['scale']}' "
                          f"(opponent IP median {_pct(fips, 0.5) or 0:.0f}, 75th pct {_pct(fips, 0.75) or 0:.0f})")
        except AOError as e:
            o.append(f"\n_Killboard unavailable ({e}); pass `opponent` to compare with a specific build._")
    if opps:
        mrows, tot, wsum = [], 0.0, 0.0
        for op, w, note in opps:
            d = duel(me, op)
            mrows.append((op["name"] + " — " + _sig_text(_build_sig_from_entries(op)), f"{op['avg']:.0f}", note,
                          f"{d['win']:.0%}", f"{d['disengage']:.0%}", f"{d['lose']:.0%}", f"{d['ttk_ab']:.0f}s / {d['ttk_ba']:.0f}s"))
            tot += w
            wsum += w * d["win"]
        o.append(f"\n### Matchups ({field_note or 'given opponent'})\n" + table(mrows, ["opponent build", "IP", "killboard",
                 "you win", "disengage", "you die", "time to kill: you→them / them→you"]))
        o.append(f"Field-weighted win rate: **{wsum / tot:.0%}**")
    if price:
        base = market.price_map([e["id"] for e in me["entries"]], server, city, estimate=True)
        v = sum((base.get(e["id"], (None,))[0] or 0) * e["stack"] for e in me["entries"])
        o.append(f"\n**Re-gear cost** (quality 1 prices, {city}): ≈ {money(v)}" + (" — lost on death here" if rules["lethal"] else
                 " — not at risk here (no item loss)") + (f" · {'; '.join(market.WARNINGS)}" if market.WARNINGS else ""))
    o.append("\n" + PVP_NOTE)
    return "\n".join(o)


def _build_sig_from_entries(p):
    by = {e["row"]["slot"]: advisor._family(e["id"]) for e in p["entries"] if not e["inventory"]}
    return (by.get("mainhand"), by.get("offhand"), by.get("head"), by.get("armor"), by.get("shoes"))


def ip_variants(item_ids, target_ip):
    """{combat item: [variants of the same item whose base IP equals the 100-step level reaching target_ip]}
    (e.g. 1000 = 4.3 / 5.2 / 6.1 / 7.0)."""
    level = math.ceil(max(target_ip, 700) / 100) * 100
    cands = {}
    for iid in item_ids:
        it = q1("SELECT slot, itempower FROM items WHERE id=?", iid)
        if not it or it["slot"] not in ("mainhand", "offhand", "head", "armor", "shoes", "cape") or not it["itempower"]:
            continue
        fam = advisor._family(iid)
        rows = core.q("SELECT id FROM items WHERE id GLOB ? AND itempower=?", f"T[0-9]_{fam}*", level)
        cands[iid] = [r["id"] for r in rows if advisor._family(r["id"]) == fam] or [iid]
    return cands


def cheapest(cands, prices):
    """({orig_id: (variant_id, price)}, total, missing) — the cheapest priced variant of each item."""
    out, total, missing = {}, 0.0, 0
    for iid, vs in cands.items():
        priced = sorted((prices[v][0], v) for v in vs if prices.get(v, (None,))[0])
        if priced:
            out[iid] = (priced[0][1], priced[0][0])
            total += priced[0][0]
        else:
            missing += 1
    return out, total, missing


def pvp_builds(content="mists_black", server="europe", pages=10, budget=None, weapon=None, city="Caerleon", top=8, spec_ip=100):
    """Build search for a PvP/PvPvE content: killboard builds at the content's fight size, each simulated against the rest of
    the field at the content's effective IP, ranked by model win rate and killboard K/D, with the cost of reaching the cap."""
    key = resolve_zone(content)
    rules = zone_rules(key)
    rows, fips, nev = field(rules["scale"], server, pages, top=max(top * 2, 12))
    if not rows:
        raise AOError(f"No killboard builds at scale '{rules['scale']}' in the sample; raise pages (max 20).")
    ref_ip = rules["cap"] or _pct(fips, 0.5) or 1100
    ref_ip = max(ref_ip, rules["entry_ip"] or 0)
    players = [build_pvp_player(r["loadout"], {"avg_ip": ref_ip}, rules) for r in rows]
    out = []
    for i, (r, p) in enumerate(zip(rows, players)):
        if weapon and advisor._family(core.resolve_item(weapon)) != r["sig"][0]:
            continue
        others = [(players[j], rows[j]["n"]) for j in range(len(rows)) if j != i]
        wr = sum(w * duel(p, o)["win"] for o, w in others) / max(sum(w for _, w in others), 1)
        ids = [e["id"] for e in p["entries"]]
        out.append((r, p, wr, ids))
    if not out:
        raise AOError("No build with that weapon in the killboard sample; raise pages or drop the weapon filter.")
    # cost of reaching the reference IP with the cheapest tier/enchant of each item (mastery adds spec_ip on top of base IP);
    # one price request for every candidate of every build
    cands = {id(p): ip_variants(ids, ref_ip - spec_ip) for r, p, wr, ids in out}
    prices = market.price_map(sorted({v for c in cands.values() for vs in c.values() for v in vs}), server, city, estimate=True)
    warn = list(market.WARNINGS)
    ranked = []
    for r, p, wr, ids in out:
        cheap, cost, missing = cheapest(cands[id(p)], prices)
        p["cheap"], p["missing"] = cheap, missing
        if budget and cost and cost > budget:
            continue
        score = 0.6 * wr + 0.4 * min(r["kd"] / (1 + r["kd"]), 1)  # model vs empirical
        ranked.append((score, r, p, wr, cost))
    ranked.sort(key=lambda x: -x[0])
    trs = [(i + 1, _sig_text(r["sig"]), f"{r['kills']}/{r['deaths']}", f"{r['kd']:.2f}", f"{r['ip'] or 0:.0f}", f"{wr:.0%}",
            (money(cost) + (f" (+{p['missing']} unpriced)" if p.get("missing") else "")) if cost else "n/a", f"{s:.2f}") for i, (s, r, p, wr, cost) in enumerate(ranked[:top])]
    o = [f"## PvP builds for {rules['title']}", "",
         f"Killboard {server}: {nev} recent open-world kills, fights of scale **{rules['scale']}**; builds simulated against each "
         f"other at **{ref_ip:.0f} IP** " + (f"(the soft cap — more IP is worth ×{rules['factor']:g})" if rules["cap"] else
                                            "(median opponent IP; no cap here)") + ".", "",
         table(trs, ["#", "build (weapon + offhand + head + armor + shoes)", "kills/deaths", "K/D", "killer IP", "model win rate",
                     f"cost at {ref_ip:.0f} IP", "score"])]
    if ranked:
        s, r, p, wr, cost = ranked[0]
        o.append(f"\n**Top pick:** {_sig_text(r['sig'])} — spells (auto-picked for PvP): " +
                 ", ".join((q1("SELECT name_en FROM spells WHERE id=?", sid) or {"name_en": sid})["name_en"] for _, sid in p["spells"]))
        cheap = p.get("cheap") or {}
        o.append(f"Cheapest way to {ref_ip:.0f} IP (base IP {math.ceil((ref_ip - spec_ip) / 100) * 100:.0f} + ~{spec_ip} from mastery): " +
                 ", ".join(f"{label(v)} ≈ {money(pr)}" for v, pr in cheap.values()))
        o.append("Seen on the killboard: " + ", ".join(label(e["id"]) for e in p["entries"]))
    if warn:
        o.append(f"_Prices incomplete: {'; '.join(warn)}_")
    if budget:
        o.append(f"_Budget filter: ≤ {money(budget)} (re-gear at quality 1, {city})._")
    o.append("\n_Score = 0.6 × model win rate vs the field + 0.4 × killboard K/D share. Killboard = open-world deaths only "
             "(instanced corrupted dungeons / hellgates are not in the public feed): use it as the meta proxy for the fight size._\n"
             + PVP_NOTE)
    return "\n".join(o)


def farm_plan(loadout, contents=None, ips=None, silver_per_hour=None, encounters_per_hour=None, server="europe", city="Caerleon",
              pages=10):
    """Where to farm with this build: per content — effective IP, win rate vs that fight size's meta, reward multipliers,
    expected re-gear loss per hour, and the silver/hour needed to break even (or net profit if silver_per_hour is given)."""
    keys = [resolve_zone(c) for c in (contents or ["mists_yellow", "mists_black", "corrupted_hunter", "corrupted_stalker",
                                                   "corrupted_slayer", "roads", "black"])]
    sph = _per_content(silver_per_hour, keys)
    enc = _per_content(encounters_per_hour, keys)
    ip_spec = gearcheck._parse_ips(ips, 1)[0] if ips else {}
    base_player = build_pvp_player(loadout, ip_spec, None)
    prices = market.price_map([e["id"] for e in base_player["entries"]], server, city, estimate=True)
    regear = sum((prices.get(e["id"], (None,))[0] or 0) * e["stack"] for e in base_player["entries"])
    fields = {}
    rows = []
    for k in keys:
        r = zone_rules(k)
        me = build_pvp_player(loadout, ip_spec, r)
        if r["scale"] not in fields:
            try:
                f, fips, _ = field(r["scale"], server, pages)
                fields[r["scale"]] = (f[:6], fips)
            except AOError:
                fields[r["scale"]] = ([], [])
        f, fips = fields[r["scale"]]
        win = lose = None
        if f:
            ws, ls, tw = 0.0, 0.0, 0.0
            for b in f:
                op = build_pvp_player(b["loadout"], {"avg_ip": b["ip"] or _pct(fips, 0.5) or 1100}, r)
                d = duel(me, op)
                ws += b["n"] * d["win"]
                ls += b["n"] * d["lose"]
                tw += b["n"]
            win, lose = ws / tw, ls / tw
        e_h = enc.get(k, ENCOUNTERS.get(k, 1.0))
        loss_h = e_h * (lose or 0.5) * regear if r["lethal"] else 0.0
        entry_ok = not r["entry_ip"] or me["avg"] >= r["entry_ip"]
        net = f"{money(sph[k] - loss_h)}" if k in sph else "—"
        from . import encounter
        pve = encounter.pve_summary(loadout, k, ips) if k.startswith(("corrupted", "mists")) else None
        pve_txt = (f"T{pve['tier']}: {pve['low']:.0%} / {pve['low_pess']:.0%} HP, {pve['fame_h']:,.0f} fame/h"
                   + (f", elite risk {pve['elite']:.0%} at {pve['worst_map']}" if pve["elite"] >= 0.05 else "")) if pve else "—"
        rows.append((k, r["title"], "✅" if entry_ok else f"⛔ <{r['entry_ip']:.0f}", f"{me['eff_avg']:.0f}",
                     f"{win:.0%}" if win is not None else "n/a", f"{lose:.0%}" if lose is not None else "n/a", f"{e_h:g}",
                     f"×{r['loot']:g} / ×{r['silver']:g} / ×{r['fame']:g}", money(loss_h) if r["lethal"] else "0 (no loss)",
                     money(loss_h) if r["lethal"] else "any", net, pve_txt))
    o = [f"## Farm plan for “{base_player['name']}”", "",
         f"Re-gear cost ≈ **{money(regear)}** ({city}, quality 1)" + (f" · {'; '.join(market.WARNINGS)}" if market.WARNINGS else ""), "",
         table(rows, ["key", "content", "entry", "eff. IP", "win vs meta", "die vs meta", "fights/h (assumed)",
                      "loot / silver / fame", "expected loss /h", "break-even silver/h", "net /h (your silver/h)",
                      "monsters (lowest HP @90% / @50% dodge, fame/h)"]),
         "\n_Expected loss/h = fights per hour × chance to die × re-gear (full-loot zones only). A content is worth it when its "
         "silver/hour beats the break-even. Fights per hour are assumptions (override `encounters_per_hour`, e.g. "
         "'mists_black=2,corrupted_stalker=1'); give your measured `silver_per_hour` to get net profit. Reward multipliers come "
         "from ClusterDangerBonus and stack with tier and chest rarity. Monsters column: encounter_sim over the content's maps "
         "(corrupted dungeons / Mists camps) — run it for details._\n" + PVP_NOTE]
    return "\n".join(o)


def _per_content(spec, keys):
    """'mists_black=2,corrupted=1' / dict / number (all) -> {key: value}."""
    if spec is None or spec == "":
        return {}
    if isinstance(spec, (int, float)):
        return {k: float(spec) for k in keys}
    if isinstance(spec, dict):
        return {resolve_zone(k): float(v) for k, v in spec.items()}
    out = {}
    for part in str(spec).split(","):
        if "=" in part:
            k, v = part.split("=", 1)
            out[resolve_zone(k.strip())] = float(v)
        elif part.strip():
            return {k: float(part) for k in keys}
    return out


PVP_NOTE = ("_PvP model: burst = one cast of every damaging spell with cooldown ≤30 s + 3 s of auto-attacks; DPS = autos + spells "
            "over their cooldowns (vs players, spells.json); damage × 1.0918 per +100 effective weapon IP × item damage bonus; "
            "mitigation 100/(100+armor/mres) and PvP defense bonus; CC on the opponent stops their damage (≤45%, halved by cleanse, "
            "removed by CC immunity windows); shields/heals/lifesteal offset damage (anti-heal reduces heals); win chance = "
            "1/(1+(TTK_you/TTK_them)^3); the loser escapes with dashes/speed/invisibility minus the winner's slows and CC. "
            "Player skill, positioning and cooldown timing are not modelled — compare builds, don't treat as a guarantee._")
