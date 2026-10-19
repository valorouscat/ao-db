"""PvP / PvPvE: zone rules and item-power soft caps (worldsettings.json), a player's kit against players (burst, sustained
damage, crowd control, escapes, defenses, purge/cleanse), a duel model between two loadouts, the open-world killboard meta
split by fight size, build search and a farm plan (reward multipliers vs death risk and re-gear cost).

Everything combat-related is a model on top of spells.json / items.json: compare options, don't read it as a guarantee.
"""
import functools, json, math, os, re, statistics, time
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
def defense_dr(x):
    """Damage reduction of a Defense / % resistance bonus: damage × 1/(1+x) (Defense +117% = −54% damage)."""
    return 1 - 1 / (1 + max(x, 0))


class PvpWalk:
    """PvP-relevant effects of one cast: CC on enemies, escapes, defenses, purge/cleanse, anti-heal, armor shred, damage
    reduction / damage buffs / weakening (value × seconds), reflected damage, cast interrupts.
    Conditions (If…/not/and/or) are not followed; mob-only effects are skipped; effects of short-radius auras / areas around
    the caster count at REACH (a ranged opponent is inside them only part of the time)."""
    HARD = ("stun", "silence", "fear", "sleep", "imprison", "cannotattack")
    DMG_TYPES = {"physicalattackdamagebonus": "p", "physicalspelldamagebonus": "p", "magicattackdamagebonus": "m",
                 "magicspelldamagebonus": "m"}
    REACH = 0.5
    CLOSE_RADIUS = 8.0

    def __init__(self):
        self.v = defaultdict(float)
        self.seen = set()

    BUFF_WINDOW = 15.0  # a buff counts at most this long (charge buffs carry 100 s timers that the parent ends early)

    def spell(self, sid, depth=0, ctx="", mult=1.0, own_mult=1.0, window=None):
        d = combat.spell_json(sid)
        if not d or sid in self.seen or depth > 6:
            return
        self.seen.add(sid)
        self.walk(d, depth, ctx, mult, own_mult, window)

    @staticmethod
    def _condition(k):
        return k.startswith("If") or k in ("not", "and", "or")

    def walk(self, n, depth, ctx="", mult=1.0, own_mult=1.0, window=None):
        if not isinstance(n, dict) or depth > 10:
            return
        v = self.v
        for k, val in n.items():
            if k.startswith("@") or k in combat.SKIP_KEYS or self._condition(k):
                continue
            for ch in combat._aslist(val):
                if not isinstance(ch, dict):
                    continue
                t = (ch.get("@target") or "").lower()
                if t.endswith("mobs") or "IfClusterArcheType" in ch:  # mob-only / arena-only variants of the effect
                    continue
                # effects of a spell applied to the enemy (proc on hit, debuff) target "self" inside: they hit the enemy
                enemy = "enemy" in t or (ctx == "enemy" and t in ("self", "", "target", "all"))
                own = not enemy and t in ("self", "", "caster", "friendall", "all")
                conditional = any(self._condition(x) for x in ch)
                sec = min(core.num(ch.get("@time")) or 0, window or self.BUFF_WINDOW)
                m = mult if enemy else own_mult
                if k in self.HARD and enemy:
                    v["cc_hard"] += sec * m
                elif k == "knockback" and enemy:
                    v["cc_hard"] += 0.5 * m
                elif k == "interruptcast" and enemy and not conditional:
                    v["cc_hard"] += 0.5 * m  # a cancelled cast: worth about half a second of hard CC on a caster
                elif k == "root" and enemy:
                    v["root"] += sec * m
                elif k == "dash":
                    v["dash"] += 1
                elif k == "buffovertime":
                    typ, value = ch.get("@type"), core.num(ch.get("@value")) or 0
                    if typ == "movespeedbonus" and enemy and value < 0:
                        v["slow"] += -value * sec * m
                    elif typ == "movespeedbonus" and own and value > 0:
                        v["speed"] += value * sec * m
                    elif typ in ("physicalarmor", "magicresistance") and own and value > 0:
                        if value <= 1:  # "damage resistances +20%": relative, counted like Defense on that damage type
                            v["dr_" + typ[0]] += defense_dr(value) * sec * m
                            v["drpk_" + typ[0]] = max(v["drpk_" + typ[0]], defense_dr(value))
                        else:
                            v["resist"] += value * sec / 2 * m
                    elif typ in ("physicalarmor", "magicresistance") and enemy and value < 0:
                        v["shred"] += (-value * sec / 2 if value < -1 else -value * 100 * sec / 2) * m
                    elif typ == "bonusdefensevsplayers" and own and value > 0:
                        for x in ("p", "m"):
                            v["dr_" + x] += defense_dr(value) * sec * m
                            v["drpk_" + x] = max(v["drpk_" + x], defense_dr(value))
                    elif typ in self.DMG_TYPES and own:
                        v["dmg_" + self.DMG_TYPES[typ]] += value * sec / 2 * m  # attack + spell bonus pair = one damage bonus (± self-debuff)
                    elif typ in self.DMG_TYPES and enemy and value < 0:
                        v["weaken_" + self.DMG_TYPES[typ]] += -value * sec / 2 * m
                    elif typ == "attackspeedbonus" and own and value > 0:
                        v["aspd"] += value * sec * m
                    elif typ == "magiccooldownreduction" and own and value > 0:  # "Cooldown Rate +x"
                        v["cdr"] += value * sec * m
                    elif typ == "hitpointsmaxbonus" and own and 0 < value <= 1:
                        v["hpbuff"] += value * sec
                    elif typ == "healmodifier" and enemy and value < 0:
                        v["antiheal"] += -value * sec * m
                    elif typ in ("crowdcontrolresistance", "bonusccrvsplayers") and own and value > 0:
                        v["ccres"] += defense_dr(value) * sec  # CC duration × 1/(1+x)
                elif k == "reflectdamageactive" and own:
                    v["reflect"] += (core.num(ch.get("@amountpercent")) or 0) * sec
                    v["reflectpk"] = max(v["reflectpk"], core.num(ch.get("@amountpercent")) or 0)
                elif k in ("invincibility", "nothittable", "notselectable") and own:
                    v["invuln"] += sec
                elif k == "spellimmunity" and own:
                    cat = (ch.get("@category") or "").lower()
                    if cat == "damage":
                        v["invuln"] += sec
                    elif cat == "crowdcontrol":
                        v["ccimmune"] = max(v["ccimmune"], sec)
                    # forcedmovement / purge / buff / heal immunities don't stop damage
                elif k == "invisibility" and own and (ch.get("@to") or "everyone").lower() in ("everyone", "players"):
                    v["invis"] += sec
                elif k == "cceffectimmunity" and own:
                    v["ccimmune"] = max(v["ccimmune"], sec)
                elif k == "removeactiveeffects":
                    cat = (ch.get("@category") or "").lower()
                    if enemy and cat in ("buff", "buff_damageshield", "heal", "movementbuff"):
                        v["purge"] += m
                    elif t in ("self", "all") and cat in ("crowdcontrol", "debuff"):
                        v["cleanse"] += 1
                sub = "enemy" if (enemy or (ch.get("@applyeffecttarget") or "").lower() == "enemy") else ctx
                sub_m, sub_own, sub_win = mult, own_mult, window
                radius = core.num(ch.get("@auraradius")) or 0
                if k in ("aura",) and 0 < radius < self.CLOSE_RADIUS:
                    sub_m = mult * self.REACH
                if k == "applyeffectoneventactive" and sub != "enemy":
                    # stacking procs (Fury: +8% per hit taken, 7 charges): about half the charges are up on average,
                    # and the stacks live only as long as the parent effect window
                    sub_own = own_mult * max(1.0, min(core.num(ch.get("@count")) or 1, 8) * 0.5)
                    sub_win = sec or window
                for a in ("@spell", "@effect"):
                    ref = ch.get(a)
                    if ref and ref != "none":
                        self.spell(ref, depth + 1, sub, sub_m, sub_own, sub_win)
                self.walk(ch, depth + 1, sub, sub_m, sub_own, sub_win)


@functools.lru_cache(maxsize=None)
def pvp_spell(sid):
    """Per-cast PvP profile of a spell (base values, before item-power scaling)."""
    d = combat.spell_json(sid)
    if not d:
        return None
    if d.get("@usableincombat") == "false":  # out-of-combat spells contribute nothing in a fight
        return {"dmg": 0.0, "cycle": max(core.num(d.get("@recastdelay")) or 1.0, combat.GCD), "aoe": False, "types": {}, "shield": 0.0,
                "heal": 0.0, "lifesteal": 0.0}
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
            + per(p.get("purge", 0)) * 15 + per(p.get("cleanse", 0)) * 15 + per(p.get("ccimmune", 0), ESCAPE_CYCLE) * 10
            + per(p.get("dr_p", 0) + p.get("dr_m", 0)) * 10 + per(p.get("reflect", 0)) * 15
            + per(p.get("dmg_p", 0) + p.get("dmg_m", 0)) * 8 + per(p.get("weaken_p", 0) + p.get("weaken_m", 0)) * 8
            + per(p.get("aspd", 0)) * 4 + per(p.get("hpbuff", 0)) * 10 + per(p.get("cdr", 0)) * 6
            + (p.get("drpk_p", 0) + p.get("drpk_m", 0)) * 10 + p.get("reflectpk", 0) * 20)


def pick_pvp_spells(item_id):
    """Q/W/E for PvP when a loadout (or killboard build) has no spells selected."""
    base = q1("SELECT base_id FROM items WHERE id=?", item_id)
    if not base:
        return []
    kit = combat.weapon_spells(base["base_id"])
    return [max(kit[s], key=lambda o: pvp_value(o[0]))[0] for s in ("1", "2", "3") if kit.get(s)]


# ------------------------------------------------------------------ passives, food, cape procs
CONST_KEYS = {"bonusdefensevsplayers": "pdr", "attackspeedbonus": "paspd", "crowdcontrolresistance": "pccres",
              "hitpointsmaxbonus": "php", "magiccooldownreduction": "pcdr"}


@functools.lru_cache(maxsize=None)
def const_buffs(sid):
    """Always-on modifiers of a passive spell ('buff' nodes) or a long food buff ('buffovertime' ≥ 10 min): {pdr, pdmg_p, pdmg_m,
    paspd, pccres, php} (fractions)."""
    d = combat.spell_json(sid)
    out = defaultdict(float)
    if not d:
        return {}
    nodes = combat._aslist(d.get("buff"))
    nodes += [b for b in combat._aslist(d.get("buffovertime")) if (core.num(b.get("@time")) or 0) >= 600
              and (b.get("@target") or "self").lower() in ("self", "")]
    for b in nodes:
        typ, val = b.get("@type"), core.num(b.get("@value")) or 0
        if typ in PvpWalk.DMG_TYPES:
            out["pdmg_" + PvpWalk.DMG_TYPES[typ]] += val / 2
        elif typ == "bonusdefensevsplayers":
            out["pdr"] = 1 - (1 - out.get("pdr", 0)) * (1 - defense_dr(val))
        elif typ in CONST_KEYS and (typ != "hitpointsmaxbonus" or val <= 1):
            out[CONST_KEYS[typ]] += val
    return dict(out)


def passive_value(sid):
    c = const_buffs(sid)
    proc = cape_proc(sid)
    return (c.get("pdr", 0) * 400 + (c.get("pdmg_p", 0) + c.get("pdmg_m", 0)) * 150 + c.get("paspd", 0) * 150
            + c.get("pccres", 0) * 50 + c.get("php", 0) * 300 + c.get("pcdr", 0) * 200 + (pvp_value_cycle(*proc[:2]) if proc else 0))


def _cape_cooldown(sid, depth=0, seen=None):
    seen = seen if seen is not None else set()
    d = combat.spell_json(sid)
    if not d or sid in seen or depth > 5:
        return None
    seen.add(sid)
    if d.get("@category") == "cape_cooldown":
        return max((core.num(x.get("@time")) or 0 for x in combat._aslist(d.get("dummy"))), default=0) or None
    for node in _refs(d):
        cd = _cape_cooldown(node, depth + 1, seen)
        if cd:
            return cd
    return None


def _refs(n):
    out = []
    if isinstance(n, dict):
        for k, v in n.items():
            if k in ("@spell", "@effect") and isinstance(v, str) and v != "none":
                out.append(v)
            elif isinstance(v, (dict, list)):
                out += _refs(v)
    elif isinstance(n, list):
        for x in n:
            out += _refs(x)
    return out


@functools.lru_cache(maxsize=None)
def cape_proc(sid):
    """(proc spell, cycle s, resets potion) of an on-event passive with an internal cooldown (capes), else None."""
    d = combat.spell_json(sid)
    ev = combat._aslist((d or {}).get("applyeffectoneventpassive"))
    if not ev:
        return None
    proc = ev[0].get("@spell")
    cd = _cape_cooldown(proc) if proc else None
    if not proc or not cd:
        return None
    resets = '"resetcooldowns"' in json.dumps(combat.spell_json(proc) or {}) and '"potion"' in json.dumps(combat.spell_json(proc) or {})
    return proc, max(cd, 1.0), resets


def pvp_value_cycle(sid, cycle):
    p = pvp_spell(sid)
    if not p:
        return 0.0
    return pvp_value(sid) * p["cycle"] / max(cycle, 1.0)


def potion_damage(sid):
    """Damage of a thrown potion against an unmounted player: (amount, ignores armor). Potions carry separate damage nodes for
    mobs, players and mounted players, and don't scale with item power."""
    d = combat.spell_json(sid) or {}
    best = None
    for k in ("attributechangeovertime", "directattributechange"):
        for n in combat._aslist(d.get(k)):
            if n.get("@attribute") != "health" or (core.num(n.get("@change")) or 0) >= 0 or n.get("@target") != "enemyplayers":
                continue
            amount = -core.num(n["@change"]) * (min(core.num(n.get("@count")) or 1, combat.MAX_PULSES) if k.endswith("overtime") else 1)
            unmounted = "mountbuff" in json.dumps(n.get("not") or {})  # the unmounted, open-world value (largest such node)
            if best is None or (unmounted and (not best[2] or amount > best[0])):
                best = (amount, n.get("@ignorearmor") == "true", unmounted)
    return best[:2] if best else (0.0, False)


def pick_armor_spells(item_id):
    """(active, passive) for a head/armor/shoes item without selected spells: best by PvP value."""
    actives, passives = gearcheck._slot_spells(item_id)
    act = max(actives[0], key=lambda o: pvp_value(o[0]))[0] if actives and actives[0] else None
    pas = max(passives, key=lambda o: passive_value(o[0]))[0] if passives else None
    return act, pas


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
    for e in entries:  # armor pieces without selected spells: the game's choice is unknown, pick the best for PvP
        if e["inventory"] or e["row"]["slot"] not in ("head", "armor", "shoes"):
            continue
        if not e["active"] or not e["passive"]:
            act, pas = pick_armor_spells(e["id"])
            if not e["active"] and act:
                e["active"], e["auto_slots"] = [act], ["armor"]
            if not e["passive"] and pas:
                e["passive"] = [pas]
    avg, rows = gearcheck.loadout_ip(entries, ip_spec.get("spec_ip", 0), ip_spec.get("weapon_ip"),
                                     ip_spec.get("slot_ip") or raw.get("slot_ip"), ip_spec.get("avg_ip") or raw.get("avg_ip"))
    eff_rows = [[r[0], effective_ip(r[1], rules) if rules else r[1], *r[2:]] for r in rows]
    eff_avg = sum(r[1] * r[2] for r in eff_rows) / max(sum(r[2] for r in eff_rows), len(gearcheck.COMBAT_SLOTS))  # empty slot = 0
    hp_given = ip_spec.get("hp") or raw.get("hp")
    # food / potions are modelled below (const_buffs, potion casts) — the calibration was fitted that way, so keep them out of
    # the item stats that gearcheck.player_stats now also fills from consumables (PvE uses those)
    stats = gearcheck.player_stats([e for e in entries if e["row"]["slot"] not in ("food", "potion")], eff_rows,
                                   hp_given if not (rules and rules["cap"]) else None)
    wip = next((r[1] for r in eff_rows if r[0] == "mainhand"), eff_avg)
    k = {"burst": 0.0, "dps": 0.0, "cc30": 0.0, "root30": 0.0, "slow30": 0.0, "dash30": 0.0, "speed30": 0.0, "invis30": 0.0,
         "invuln30": 0.0, "ccimmune30": 0.0, "sustain30": 0.0, "resist30": 0.0, "purge": 0, "cleanse": 0, "antiheal": 0.0,
         "shred30": 0.0, "lifesteal": 0.0, "aa": 0.0, "dr_p30": 0.0, "dr_m30": 0.0, "dmg_p30": 0.0, "dmg_m30": 0.0,
         "weaken_p30": 0.0, "weaken_m30": 0.0, "aspd30": 0.0, "hpbuff30": 0.0, "reflect30": 0.0, "drpk_p": 0.0, "drpk_m": 0.0,
         "reflectpk": 0.0, "ccres30": 0.0, "cdr30": 0.0, "pcdr": 0.0, "pot_burst": 0.0, "pot_true": 0.0, "pdr": 0.0, "pdmg_p": 0.0, "pdmg_m": 0.0, "paspd": 0.0, "php": 0.0, "pccres": 0.0}
    types = Counter()
    spells = []
    if weapon:
        aa = combat._autoattack_dps(weapon["id"])
        k["burst"] += aa * 3
        k["dps"] += aa
        k["aa"] = aa
        types["physical"] += aa
    casts = []  # (slot, spell, profile)
    potion_uses = 1
    for e in entries:
        if e["inventory"]:
            continue
        sl = e["row"]["slot"]
        if sl in COMBAT_SPELL_SLOTS:
            casts += [(sl, sid, pvp_spell(sid)) for sid in e["active"]]
        for sid in (e["passive"] if sl in COMBAT_SPELL_SLOTS else []) + \
                [r["spell_id"] for r in core.q("SELECT spell_id FROM item_spells WHERE item_id=?", e["row"]["base_id"])
                 if sl == "cape"]:
            for ck, cv in const_buffs(sid).items():
                k[ck] += cv
            proc = cape_proc(sid)
            if proc and pvp_spell(proc[0]):
                casts.append((sl, proc[0], dict(pvp_spell(proc[0]), cycle=proc[1])))
                potion_uses += proc[2]
            if sl in COMBAT_SPELL_SLOTS or proc:
                spells.append((sl, sid))
    for e in entries:  # potions: one use per fight (two with a potion-cooldown reset), food: always-on buffs
        cs = core.item_json(e["id"]).get("@consumespell")
        if not cs or e["inventory"]:
            continue
        if e["row"]["slot"] == "potion" and pvp_spell(cs):
            dmg, true_dmg = potion_damage(cs)
            k["pot_true" if true_dmg else "pot_burst"] += dmg * potion_uses  # fixed damage: no IP scaling
            casts.append(("potion", cs, dict(pvp_spell(cs), cycle=30.0 / potion_uses, dmg=0.0)))
        elif e["row"]["slot"] == "food":
            for ck, cv in const_buffs(cs).items():
                k[ck] += cv
    # Cooldown Rate (passives, food, sprint buffs): spells come back 1/(1+rate) faster; averaged over the casts' own uptime
    k["cdr30"] = sum((p.get("cdr", 0) * 30 / p["cycle"]) for _, _, p in casts if p)
    rate = 1 + k["pcdr"] + k["cdr30"] / 30
    for slot, sid, p in casts:
        if not p:
            continue
        if slot not in ("potion", "cape") and p["cycle"] > combat.GCD:
            p = dict(p, cycle=max(p["cycle"] / rate, combat.GCD))
        if slot not in ("potion", "cape"):  # cape procs are listed under the cape passive
            spells.append((slot, sid))
        if p["cycle"] <= 30:
            k["burst"] += p["dmg"]
        sp_dps = min(p["dmg"] / p["cycle"], combat.MAX_SPELL_DPS)
        k["dps"] += sp_dps
        for t, share in p["types"].items():
            types[t] += sp_dps * share
        for src, dst, floor in (("cc_hard", "cc30", CC_CYCLE), ("root", "root30", CC_CYCLE), ("slow", "slow30", 0),
                                ("dash", "dash30", ESCAPE_CYCLE), ("speed", "speed30", ESCAPE_CYCLE), ("invis", "invis30", ESCAPE_CYCLE),
                                ("invuln", "invuln30", ESCAPE_CYCLE), ("ccimmune", "ccimmune30", ESCAPE_CYCLE),
                                ("resist", "resist30", 0), ("shred", "shred30", 0), ("dr_p", "dr_p30", 0), ("dr_m", "dr_m30", 0),
                                ("dmg_p", "dmg_p30", 0), ("dmg_m", "dmg_m30", 0), ("weaken_p", "weaken_p30", 0),
                                ("weaken_m", "weaken_m30", 0), ("aspd", "aspd30", 0), ("hpbuff", "hpbuff30", 0),
                                ("reflect", "reflect30", 0)):
            k[dst] += min(p.get(src, 0), 1 if src == "dash" else 1e9) * 30 / max(p["cycle"], floor)
        if p["cycle"] <= 45:  # defensive cooldowns short enough to be up for the opponent's burst
            for pk in ("drpk_p", "drpk_m", "reflectpk"):
                k[pk] = max(k[pk], p.get(pk, 0))
        k["sustain30"] += (p["shield"] + p["heal"]) * 30 / p["cycle"]
        k["purge"] += p.get("purge", 0) > 0
        k["cleanse"] += p.get("cleanse", 0) > 0
        k["antiheal"] = max(k["antiheal"], p.get("antiheal", 0))
        k["lifesteal"] += p["lifesteal"]
    for e in entries:  # food / carried consumables (lifesteal, cleanse, heal, invisibility); the potion slot is a cast above
        cs = core.item_json(e["id"]).get("@consumespell")
        if cs and (e["row"]["slot"] == "food" or e["inventory"]):
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


DR_CAP = 0.6        # damage reduction from Defense / % resistance buffs, passives and timed cooldowns together
TIMING = 0.5        # share of the opponent's burst a timed defensive / reflect cooldown catches (player skill not modelled)
KITE_BASE = 0.6     # melee vs ranged: share of the sustained phase the melee player is in reach — ASSUMPTION, raised by own
                    # gap closers / speed / CC, lowered by the ranged player's slows, roots and escapes (clamped 0.35–0.95)


def melee_uptime(a, b):
    """Share of the sustained fight a melee `a` can hit a ranged `b` (1.0 unless a is melee and b ranged)."""
    if a["ranged"] or not b["ranged"]:
        return 1.0
    ka, kb = a["kit"], b["kit"]
    up = KITE_BASE + 0.06 * ka["dash30"] + 0.03 * ka["speed30"] + 0.02 * (ka["cc30"] + ka["root30"]) + 0.01 * ka["slow30"] \
        - 0.03 * kb["dash30"] - 0.02 * kb["speed30"] - 0.03 * kb["root30"] - 0.01 * kb["slow30"] - 0.01 * kb["invis30"]
    return min(max(up, 0.35), 0.95)


def _mit(attacker, target, shred30=0.0):
    st, kt = target["stats"], target["kit"]
    extra = kt["resist30"] / 30  # flat armor / magic resistance buffs, averaged over 30 s
    arm = max(st["physicalarmor"] + extra - shred30 / 30, 0)
    mres = max(st["magicresistance"] + extra - shred30 / 30, 0)
    m = attacker["mix"].get("physical", 0) * combat.mitigation(arm) + attacker["mix"].get("magic", 0) * combat.mitigation(mres)
    return m * (1 - defense_dr(st.get("bonusdefensevsplayers", 0) or 0))


def _mods(a, b, burst=False):
    """Damage multiplier for a hitting b: a's damage buffs/passives × (1 − b's damage reduction) × (1 − b's weakening of a).
    Sustained phase uses 30-s averages; the burst phase assumes b times its shortest defensive cooldown (TIMING)."""
    ka, kb = a["kit"], b["kit"]
    out = 0.0
    for t, share in a["mix"].items():
        x = "m" if t == "magic" else "p"
        dmg = 1 + ka["pdmg_" + x] + ka["dmg_" + x + "30"] / 30
        dr = kb["pdr"] + kb["dr_" + x + "30"] / 30
        if burst:
            dr = max(dr, kb["pdr"] + TIMING * kb["drpk_" + x])
        weak = min(kb["weaken_" + x + "30"] / 30, 0.5)
        out += share * dmg * (1 - min(dr, DR_CAP)) * (1 - weak)
    return out


def _hit(a, b):
    """(burst, sustained DPS) a deals to b after mitigation, buffs, defenses and b's CC / immunity windows on a."""
    ka, kb = a["kit"], b["kit"]
    m = _mit(a, b, ka["shred30"])
    burst = (ka["burst"] * a["scale"] * m + ka["pot_burst"] * m + ka["pot_true"]) * _mods(a, b, burst=True)
    dps = (ka["dps"] + ka["aa"] * (ka["aspd30"] / 30 + ka["paspd"])) * a["scale"] * m * _mods(a, b)
    cc_on_a = min(kb["cc30"] / 30 * (0.5 if ka["cleanse"] else 1) * max(0.0, 1 - ka["ccimmune30"] / 30)
                  * max(0.0, 1 - defense_dr(ka["pccres"]) - ka["ccres30"] / 30), CC_CAP)
    dps *= (1 - cc_on_a) * max(0.0, 1 - min(kb["invuln30"] / 30, 0.4)) * melee_uptime(a, b)
    return burst, dps


def _ttk(a, b):
    """Seconds for `a` to kill `b`: burst, then sustained damage minus b's sustain; b's CC on a and b's immunity windows;
    damage b deals that a reflects back (Retaliate, Frost Shield…: timed on b's burst, averaged afterwards)."""
    ka, kb = a["kit"], b["kit"]
    burst, dps = _hit(a, b)
    b_burst, b_dps = _hit(b, a)
    back = combat.mitigation(b["stats"]["magicresistance"])  # reflected damage arrives as magic damage
    burst += b_burst * TIMING * min(ka["reflectpk"], 0.85) * back
    dps += b_dps * min(ka["reflect30"] / 30, 0.85) * back
    heal_mult = 1 - min(ka["antiheal"], 0.5)
    sustain = (kb["sustain30"] / 30) * b["scale"] / max(b["ap"], 0.01) * heal_mult + kb["lifesteal"] * kb["dps"] * b["scale"] * 0.3
    ehp = b["stats"]["hp"] * (1 + kb["hpbuff30"] / 30 + kb["php"])
    net = max(dps - sustain, 0.15 * dps, 1e-6)
    return OPENING + max(ehp - burst, 0) / net


CAL_PATH = os.path.join(core.ROOT, "knowledge", "pvp_calibration.json")
KIT_FEATURES = ("logttk", "burst", "cc", "escape", "ranged", "hp")
FAMILY_SLOTS = ("mainhand", "offhand", "head", "armor", "shoes", "cape")


@functools.lru_cache(maxsize=1)
def calibration_model():
    """Logistic weights fitted on killboard fights by pvp_backtest(fit=True), or None."""
    try:
        with open(CAL_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _families(p):
    by = {e["row"]["slot"]: advisor._family(e["id"]) for e in p["entries"] if not e["inventory"]}
    return {s_: by.get(s_) or "none" for s_ in FAMILY_SLOTS}


def pair_features(a, b, t_ab=None, t_ba=None):
    """Antisymmetric features of a vs b (f(b, a) = −f(a, b)): effective IP gap (100 IP = 1), the duel simulation's kit
    signals (TTK ratio, burst share of HP, CC, escapes, ranged, HP; clipped to ±2) and the item family in every slot
    (slot:family = +1 for a, −1 for b) — the item effects are learned from killboard outcomes."""
    t_ab = t_ab if t_ab is not None else _ttk(a, b)
    t_ba = t_ba if t_ba is not None else _ttk(b, a)
    ka, kb = a["kit"], b["kit"]
    ba, bb = _hit(a, b)[0], _hit(b, a)[0]
    esc = lambda k: k["dash30"] + k["invis30"] / 3 + k["invuln30"]
    clip = lambda x: max(min(x, 2.0), -2.0)
    f = {"dip": (a["eff_avg"] - b["eff_avg"]) / 100, "logttk": clip(math.log(max(t_ba, 0.1) / max(t_ab, 0.1))),
         "burst": clip(min(ba / b["stats"]["hp"], 2) - min(bb / a["stats"]["hp"], 2)),
         "cc": clip((ka["cc30"] + ka["root30"] - kb["cc30"] - kb["root30"]) / 10), "escape": clip((esc(ka) - esc(kb)) / 10),
         "ranged": float(a["ranged"]) - float(b["ranged"]), "hp": clip((a["stats"]["hp"] - b["stats"]["hp"]) / 1000)}
    fa, fb = _families(a), _families(b)
    for s_ in FAMILY_SLOTS:  # an empty slot is not an item: its learned "effect" was who plays without a cape, not gear power
        if fa[s_] != fb[s_]:
            if fa[s_] != "none":
                f[f"{s_}:{fa[s_]}"] = f.get(f"{s_}:{fa[s_]}", 0) + 1
            if fb[s_] != "none":
                f[f"{s_}:{fb[s_]}"] = f.get(f"{s_}:{fb[s_]}", 0) - 1
    return f


def win_probability(a, b, t_ab=None, t_ba=None):
    """P(a beats b): calibrated on killboard fights when knowledge/pvp_calibration.json exists, else the raw TTK model."""
    t_ab = t_ab if t_ab is not None else _ttk(a, b)
    t_ba = t_ba if t_ba is not None else _ttk(b, a)
    cal = calibration_model()
    if not cal:
        return 1 / (1 + (t_ab / t_ba) ** DUEL_K)
    w = cal["weights"]
    z = sum(w.get(k, 0.0) * v for k, v in pair_features(a, b, t_ab, t_ba).items())
    return 1 / (1 + math.exp(-max(min(z, 30), -30)))


def duel(a, b):
    """{'win', 'lose', 'disengage', 'ttk_ab', 'ttk_ba'} for player a against player b (model)."""
    t_ab, t_ba = _ttk(a, b), _ttk(b, a)
    p = win_probability(a, b, t_ab, t_ba)
    loser, winner = (b, a) if p >= 0.5 else (a, b)
    lk, wk = loser["kit"], winner["kit"]
    esc = 0.1 + 0.08 * lk["dash30"] + 0.04 * lk["speed30"] + 0.02 * lk["invis30"] + 0.02 * lk["invuln30"] \
        - 0.02 * wk["slow30"] - 0.03 * wk["cc30"] - 0.02 * wk["root30"] - (0.05 if winner["ranged"] else 0)
    esc = min(max(esc, 0.0), 0.6)
    if p >= 0.5:  # b may get away
        return {"win": p * (1 - esc), "lose": 1 - p, "disengage": p * esc, "ttk_ab": t_ab, "ttk_ba": t_ba}
    return {"win": p, "lose": (1 - p) * (1 - esc), "disengage": (1 - p) * esc, "ttk_ab": t_ab, "ttk_ba": t_ba}


# ------------------------------------------------------------------ backtest / calibration on the killboard
KB_SLOTS = ("MainHand", "OffHand", "Head", "Armor", "Shoes", "Cape", "Potion", "Food")


def _kb_loadout(p):
    items = []
    for sl in KB_SLOTS:
        it = (p.get("Equipment") or {}).get(sl) or {}
        t = it.get("Type")
        if t and q1("SELECT 1 FROM items WHERE id=?", t):
            e = {"item": t, "quality": it.get("Quality") or 1}
            if it.get("ActiveSpells"):
                e["activeSpells"] = it["ActiveSpells"]
            if it.get("PassiveSpells"):
                e["passiveSpells"] = it["PassiveSpells"]
            items.append(e)
    return {"name": p.get("Name") or "?", "equipment": items}


def _is_fight(p):
    eq = p.get("Equipment") or {}
    mh = (eq.get("MainHand") or {}).get("Type") or ""
    return mh and "TOOL" not in mh and "GATHERER" not in json.dumps(eq)


KB_STORE = os.path.join(core.ROOT, "knowledge", "killboard_fights.jsonl.gz")


def _compact_side(p):
    eq = {sl: [it["Type"], it.get("Quality") or 1] for sl, it in (p.get("Equipment") or {}).items() if sl in KB_SLOTS and it and it.get("Type")}
    return {"ip": p.get("AverageItemPower") or 0, "eq": eq}


def _expand_side(c):
    return {"Name": "?", "AverageItemPower": c["ip"], "Equipment": {sl: {"Type": t, "Quality": q_} for sl, (t, q_) in c["eq"].items()}}


def kb_store():
    """{event id: compact solo fight} accumulated by killboard_collect."""
    import gzip
    out = {}
    try:
        with gzip.open(KB_STORE, "rt", encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                out[r["id"]] = r
    except OSError:
        pass
    return out


def killboard_collect(servers="europe,west,east", pages=20):
    """Append new solo kills (armed, non-gathering, both sides' gear + IP) from the killboard to
    knowledge/killboard_fights.jsonl.gz — the training data of the PvP calibration. Run it regularly: the public feed only
    holds the last ~1000 events per server (≈ 1 hour)."""
    import gzip
    store = kb_store()
    before = len(store)
    srv = tuple(x.strip() for x in str(servers).split(",") if x.strip())
    per = Counter()
    for sv in srv:  # advisor._events fetches the newest pages (into its local cache) and returns every cached event
        for e in advisor._events(sv, pages, since=""):
            if e["EventId"] in store or (e.get("numberOfParticipants") or len(e.get("Participants") or [])) != 1:
                continue
            K, V = e["Killer"], e["Victim"]
            if not (_is_fight(K) and _is_fight(V)):
                continue
            store[e["EventId"]] = {"id": e["EventId"], "t": e.get("TimeStamp", "")[:19], "srv": sv, "k": _compact_side(K), "v": _compact_side(V)}
            per[sv] += 1
    with gzip.open(KB_STORE, "wt", encoding="utf-8") as fh:
        for r in sorted(store.values(), key=lambda r: r["t"]):
            fh.write(json.dumps(r, separators=(",", ":")) + "\n")
    ts = sorted(r["t"] for r in store.values())
    return (f"## Killboard collection\nAdded **{len(store) - before}** solo fights ("
            + ", ".join(f"{k} {v}" for k, v in per.items()) + f"); stored **{len(store)}** fights"
            + (f", {ts[0]} → {ts[-1]} UTC" if ts else "") + ".\nRe-fit the calibration with `pvp_backtest fit=true`.")


def kb_pairs(fights):
    """[(timestamp, features of killer vs victim, raw p(killer), IP gap)] from stored compact fights."""
    out = []
    for r in fights:
        K, V = _expand_side(r["k"]), _expand_side(r["v"])
        try:
            a = build_pvp_player(_kb_loadout(K), {"avg_ip": K["AverageItemPower"]})
            b = build_pvp_player(_kb_loadout(V), {"avg_ip": V["AverageItemPower"]})
            t_ab, t_ba = _ttk(a, b), _ttk(b, a)
        except (AOError, KeyError, TypeError, ValueError, ZeroDivisionError):
            continue
        out.append((r["t"], pair_features(a, b, t_ab, t_ba), 1 / (1 + (t_ab / t_ba) ** DUEL_K), a["eff_avg"] - b["eff_avg"]))
    return out


L2 = {"dense": 0.001, "kit": 0.5, "family": 0.03}  # chosen by 5-fold cross-validation on 1399 fights (2026-10-19)


def _fit_logistic(rows, keep=None, iters=300, lr=0.5):
    """L2 logistic regression without intercept on antisymmetric features (label: a = the killer). keep = feature filter."""
    data = [{k: v for k, v in f.items() if keep is None or keep(k)} for f in rows]
    w = defaultdict(float)
    reg = lambda k: L2["family"] if ":" in k else (L2["kit"] if k in KIT_FEATURES else L2["dense"])
    for _ in range(iters):
        g = defaultdict(float)
        for x in data:
            pr = 1 / (1 + math.exp(-max(min(sum(w[k] * v for k, v in x.items()), 30), -30)))
            for k, v in x.items():
                g[k] += (1 - pr) * v
        for k in set(g) | set(w):
            w[k] += lr * (g[k] / len(data) - reg(k) * w[k])
    return dict(w)


def _predict(w, f):
    return 1 / (1 + math.exp(-max(min(sum(w.get(k, 0.0) * v for k, v in f.items()), 30), -30)))


def _metrics(ps):
    """Accuracy, log-loss, calibration bins for predicted P(killer wins)."""
    ps = [min(max(p, 1e-3), 1 - 1e-3) for p in ps]
    bins = defaultdict(lambda: [0, 0])
    for p in ps:
        for q, won in ((p, 1), (1 - p, 0)):
            b_ = min(int(q * 5), 4)
            bins[b_][0] += 1
            bins[b_][1] += won
    return (sum(p > 0.5 for p in ps) / len(ps), -sum(math.log(p) for p in ps) / len(ps), {b_: v for b_, v in sorted(bins.items())})


def pvp_backtest(servers="europe,west,east", pages=20, fit=False, test_share=0.3, collect=True):
    """Backtest the duel model on killboard solo kills (killer vs victim with their real gear and IP): accuracy, log-loss and
    calibration on a held-out split for IP-only, the raw TTK model and the calibrated feature model; fit=True refits the
    calibration on all fights and saves it to knowledge/pvp_calibration.json (used by duel / pvp_check / pvp_tune)."""
    srv = tuple(x.strip() for x in str(servers).split(",") if x.strip())
    if collect:
        killboard_collect(servers, pages)
    rows = sorted(kb_pairs(kb_store().values()), key=lambda r: r[0])
    if len(rows) < 100:
        raise AOError(f"Only {len(rows)} usable fights — run killboard_collect a few times")
    cut = int(len(rows) * (1 - test_share))  # time split: the newest fights are the test set (no look-ahead)
    train, test = rows[:cut], rows[cut:]
    o = [f"## PvP model backtest — {len(rows)} stored solo kills ({rows[0][0]} → {rows[-1][0]} UTC); train {len(train)} / "
         f"test {len(test)} (newest {test_share:.0%})", ""]
    tr = [r[1] for r in train]
    w_ip = _fit_logistic(tr, lambda k: k == "dip")
    w_kit = _fit_logistic(tr, lambda k: ":" not in k)
    w_all = _fit_logistic(tr)
    res = {"IP gap only": [_predict(w_ip, r[1]) for r in test],
           "raw duel simulation (TTK)": [r[2] for r in test],
           "IP + simulated kit": [_predict(w_kit, r[1]) for r in test],
           "IP + kit + items (calibrated)": [_predict(w_all, r[1]) for r in test]}
    rows_t, cal_txt = [], []
    for name, ps in res.items():
        acc, ll, bins = _metrics(ps)
        conf = [p for p in ps if abs(p - 0.5) >= 0.25]
        rows_t.append((name, f"{acc:.1%}", f"{ll:.3f}", f"{len(conf)} ({len(conf) / len(ps):.0%}): "
                       + (f"{sum(p > 0.5 for p in conf) / len(conf):.0%} right" if conf else "—")))
        cal_txt.append(f"- {name}: " + "; ".join(f"{b_ * 20}–{b_ * 20 + 20}% → {v[1] / v[0]:.0%} (n={v[0]})" for b_, v in bins.items()))
    o.append(table(rows_t, ["predictor (held-out fights)", "picks the killer", "log-loss (0.693 = coin)", "confident calls (≥75/≤25%)"]))
    o.append("\n**Calibration** (predicted → observed win share):\n" + "\n".join(cal_txt))
    o.append("\n**Weights** (train): " + ", ".join(f"{n} {w_all.get(n, 0):+.2f}" for n in ("dip",) + KIT_FEATURES)
             + " — dip = per 100 effective IP; kit signals clipped to ±2.")
    fam = sorted(((v, k) for k, v in w_all.items() if ":" in k), reverse=True)
    if fam:
        nm = lambda k: f"{k.split(':')[0]} {advisor._fam_name(k.split(':', 1)[1])}"
        o.append("\n**Items that win more than their IP explains** (log-odds; +0.94 ≈ +100 IP): "
                 + ", ".join(f"{nm(k)} {v:+.2f}" for v, k in fam[:8])
                 + "\n**…and less:** " + ", ".join(f"{nm(k)} {v:+.2f}" for v, k in fam[-8:]))
    if fit:
        w_final = _fit_logistic([r[1] for r in rows])
        acc, ll, _ = _metrics(res["IP + kit + items (calibrated)"])
        cal = {"weights": {k: round(v, 4) for k, v in sorted(w_final.items()) if abs(v) >= 1e-4}, "n": len(rows),
               "period": [rows[0][0], rows[-1][0]],
               "trained": time.strftime("%Y-%m-%d"), "test_accuracy": round(acc, 4), "test_logloss": round(ll, 4)}
        with open(CAL_PATH, "w", encoding="utf-8") as fh:
            json.dump(cal, fh, indent=1)
        calibration_model.cache_clear()
        o.append(f"\n✅ Saved calibration to `knowledge/pvp_calibration.json` (weights refit on all {len(rows)} fights). "
                 "duel / pvp_check / pvp_tune now use it.")
    o.append("\n_Killboard = fights that ended in a death in the open world (no IP cap): ambushes, third parties and fights "
             "against mobs are mixed in. In capped content the IP weight is applied to the effective IP after the cap._")
    return "\n".join(o)


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


def weighted_ci(xs, ws):
    """(mean, ± 90% half-width) of xs weighted by kill counts ws: the field's build mix is a sample of sum(ws) fights, so
    a smaller sample or opponents the build fares very differently against widen the range."""
    tw = sum(ws)
    if not tw:
        return 0.0, 0.0
    m = sum(x * w for x, w in zip(xs, ws)) / tw
    var = sum(w / tw * (x - m) ** 2 for x, w in zip(xs, ws)) / tw
    return m, 1.645 * math.sqrt(var)


def opponent_label(row):
    """Short name of a killboard field build: weapon (armor), with its kill count."""
    sig = row["sig"]
    return f"{advisor._fam_name(sig[0])} ({advisor._fam_name(sig[3]) if sig[3] else '—'}) ×{row['n']}"


def matchup_matrix(builds, opponents):
    """Markdown: one row per build, one column per opponent with 'win / die' % (✅ win ≥ 60, ⚠ die ≥ 40 — in full-loot
    content the death chance is what costs the bag; the rest of 100 is fights someone escapes), and a verdict per build: who
    it beats and who is most dangerous to it. builds: [(label, [duel dict per opponent])], opponents: [label]."""
    cell = lambda d: f"{d['win'] * 100:.0f} / {d['lose'] * 100:.0f}" + (" ✅" if d["win"] >= 0.6 else "") + (" ⚠" if d["lose"] >= 0.4 else "")
    rows = [(lbl, *[cell(d) for d in ds]) for lbl, ds in builds]
    short = lambda o: o.rsplit(" ×", 1)[0]
    lines = []
    for lbl, ds in builds:
        beats = [f"{short(o)} {d['win']:.0%}" for o, d in sorted(zip(opponents, ds), key=lambda x: -x[1]["win"]) if d["win"] >= 0.6][:3]
        danger = sorted(zip(opponents, ds), key=lambda x: -x[1]["lose"])
        bad = [f"{short(o)} (dies {d['lose']:.0%}, wins {d['win']:.0%})" for o, d in danger if d["lose"] >= 0.4][:2]
        lines.append(f"- **{lbl}**: " + (f"beats {', '.join(beats)}" if beats else "no clear wins") + "; " + (
            "dies to " + ", ".join(bad) if bad else
            f"most dangerous: {short(danger[0][0])} (dies {danger[0][1]['lose']:.0%})"))
    return table(rows, ["build (win / die %)", *opponents]) + "\n" + "\n".join(lines)


def pct_ci(m, half):
    return f"{m:.0%} ±{half * 100:.0f}"


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
                     f"{p['stats']['hp']:,.0f}", f"{k['burst'] * p['scale'] + k['pot_burst'] + k['pot_true']:,.0f}",
                     f"{k['dps'] * p['scale']:,.0f}",
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
        wr, half = weighted_ci([duel(p, o)["win"] for o, _ in others], [w for _, w in others])
        p["win_ci"] = half
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
    trs = [(i + 1, _sig_text(r["sig"]), f"{r['kills']}/{r['deaths']}", f"{r['kd']:.2f}", f"{r['ip'] or 0:.0f}", pct_ci(wr, p["win_ci"]),
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
    if ranked:
        opp_rows = rows[:8]
        o.append("\n### Matchups of the top builds (model win / die % vs each killboard build; ✅ win ≥ 60, ⚠ die ≥ 40)\n" + matchup_matrix(
            [(f"{i + 1}. {advisor._fam_name(r['sig'][0])}", [duel(p, players[rows.index(o_)]) for o_ in opp_rows])
             for i, (_, r, p, _, _) in enumerate(ranked[:min(top, 5)])], [opponent_label(o_) for o_ in opp_rows]))
    o.append(advisor.kb_line())
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
        win = lose = win_ci = None
        if f:
            ds = [duel(me, build_pvp_player(b["loadout"], {"avg_ip": b["ip"] or _pct(fips, 0.5) or 1100}, r)) for b in f]
            (win, win_ci), (lose, _) = (weighted_ci([d[k_] for d in ds], [b["n"] for b in f]) for k_ in ("win", "lose"))
        e_h = enc.get(k, ENCOUNTERS.get(k, 1.0))
        loss_h = e_h * (lose or 0.5) * regear if r["lethal"] else 0.0
        entry_ok = not r["entry_ip"] or me["avg"] >= r["entry_ip"]
        net = f"{money(sph[k] - loss_h)}" if k in sph else "—"
        from . import encounter
        pve = encounter.pve_summary(loadout, k, ips) if k.startswith(("corrupted", "mists")) else None
        pve_txt = (f"T{pve['tier']}: {pve['low']:.0%} / {pve['low_pess']:.0%} HP, {pve['fame_h']:,.0f} fame/h"
                   + (f", elite risk {pve['elite']:.0%} at {pve['worst_map']}" if pve["elite"] >= 0.05 else "")) if pve else "—"
        rows.append((k, r["title"], "✅" if entry_ok else f"⛔ <{r['entry_ip']:.0f}", f"{me['eff_avg']:.0f}",
                     pct_ci(win, win_ci) if win is not None else "n/a", f"{lose:.0%}" if lose is not None else "n/a", f"{e_h:g}",
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
         "(corrupted dungeons / Mists camps) — run it for details._\n" + PVP_NOTE, advisor.kb_line()]
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


PVP_NOTE = ("_PvP model: burst = one cast of every damaging spell with cooldown ≤30 s + 3 s of auto-attacks + potion damage; DPS = "
            "autos + spells over their cooldowns (vs players, spells.json); damage × 1.0918 per +100 effective weapon IP × item damage "
            "bonus × passive/food/buff damage bonuses; mitigation 100/(100+armor/mres), PvP defense bonus, Defense / % resistance buffs "
            "(30-s average; a defensive cooldown ≤45 s is assumed timed on half of the opponent's burst), weakening debuffs, reflected "
            "damage; armor pieces without chosen spells get the best PvP spells; cape procs on their internal cooldown; CC on the opponent "
            "stops their damage (≤45%, halved by cleanse, removed by CC immunity windows); shields/heals/lifesteal offset damage "
            "(anti-heal reduces heals); melee vs ranged hits only part of the sustained phase (kiting: 0.6 base, ± dashes / speed / CC of "
            "both sides); win chance = "
            "1/(1+(TTK_you/TTK_them)^3); the loser escapes with dashes/speed/invisibility minus the winner's slows and CC. "
            "Player skill, positioning and cooldown timing are not modelled — compare builds, don't treat as a guarantee._")


# ------------------------------------------------------------------ gear tuning against reference opponents
# Archetype builds seen on the killboard (T8.3 items; their IP is set with opp_ip). role: ranged / melee.
REFERENCE_OPPONENTS = {
    "Dual Swords": ("melee", ["2H_DUALSWORD", "HEAD_LEATHER_SET2", "ARMOR_LEATHER_SET1", "SHOES_LEATHER_SET3", "CAPEITEM_FW_THETFORD"]),
    "Spear + Torch": ("melee", ["MAIN_SPEAR", "OFF_TORCH", "HEAD_LEATHER_SET1", "ARMOR_LEATHER_FEY", "SHOES_LEATHER_AVALON",
                                "CAPEITEM_FW_THETFORD"]),
    "Bear Paws": ("melee", ["2H_DUALAXE_KEEPER", "HEAD_CLOTH_HELL", "ARMOR_LEATHER_SET3", "SHOES_CLOTH_ROYAL", "CAPEITEM_FW_THETFORD"]),
    "Prowling Staff": ("melee", ["2H_SHAPESHIFTER_SET1", "HEAD_CLOTH_HELL", "ARMOR_PLATE_SET3", "SHOES_LEATHER_SET2", "CAPEITEM_FW_THETFORD"]),
    "Fire Staff + Tome": ("ranged", ["MAIN_FIRESTAFF", "OFF_BOOK", "HEAD_LEATHER_SET2", "ARMOR_CLOTH_SET2", "SHOES_PLATE_SET3",
                                     "CAPEITEM_FW_THETFORD"]),
    "Demonic Staff": ("ranged", ["2H_DEMONICSTAFF", "HEAD_PLATE_AVALON", "ARMOR_LEATHER_FEY", "SHOES_PLATE_ROYAL", "CAPEITEM_FW_THETFORD"]),
    "Frost Staff + Tome": ("ranged", ["MAIN_FROSTSTAFF", "OFF_BOOK", "HEAD_CLOTH_SET1", "ARMOR_CLOTH_SET3", "SHOES_CLOTH_SET1",
                                      "CAPEITEM_FW_THETFORD"]),
    "Cursed Staff + Tome": ("ranged", ["MAIN_CURSEDSTAFF", "OFF_BOOK", "HEAD_CLOTH_SET2", "ARMOR_CLOTH_SET2", "SHOES_CLOTH_SET1",
                                       "CAPEITEM_FW_THETFORD"]),
    "Light Crossbow + Mistcaller": ("ranged", ["MAIN_1HCROSSBOW", "OFF_HORN_KEEPER", "HEAD_PLATE_SET3", "ARMOR_CLOTH_SET2",
                                               "SHOES_PLATE_SET1", "CAPEITEM_FW_THETFORD"]),
    "Bow": ("ranged", ["2H_BOW", "HEAD_LEATHER_SET3", "ARMOR_LEATHER_SET3", "SHOES_LEATHER_SET2", "CAPEITEM_FW_THETFORD"]),
    "Warbow": ("ranged", ["2H_WARBOW", "HEAD_LEATHER_SET1", "ARMOR_LEATHER_SET1", "SHOES_LEATHER_SET3", "CAPEITEM_FW_THETFORD"]),
    "Longbow": ("ranged", ["2H_LONGBOW", "HEAD_LEATHER_SET2", "ARMOR_LEATHER_SET2", "SHOES_LEATHER_SET3", "CAPEITEM_FW_THETFORD"]),
}
TUNE_SLOTS = ("weapon", "head", "armor", "shoes", "cape", "potion", "food")


def reference_opponents(vs="ranged", opp_ip=1300, rules=None):
    roles = {"ranged": ("ranged",), "melee": ("melee",), "all": ("ranged", "melee")}.get(vs)
    if not roles:
        raise AOError("vs must be ranged, melee or all")
    out = []
    for name, (role, fams) in REFERENCE_OPPONENTS.items():
        if role in roles:
            lo = {"name": name, "equipment": [{"item": f"T8_{f}@3"} for f in fams]}
            out.append(build_pvp_player(lo, {"avg_ip": opp_ip}, rules))
    return out


def _slot_candidates(slot, cur):
    """Alternatives for one slot: [(label, equipment entry or None to drop)]. Gear keeps the current item power."""
    if slot == "weapon":
        kit = combat.weapon_spells(q1("SELECT base_id FROM items WHERE id=?", cur["item"])["base_id"])
        opts = [[o[0] for o in kit.get(s) or []] for s in ("1", "2", "3")]
        out = []
        for qs in opts[0] or [None]:
            for ws in opts[1] or [None]:
                for es in opts[2] or [None]:
                    act = [x for x in (qs, ws, es) if x]
                    out.append((" / ".join(_spell_name(x) for x in act), dict(cur, activeSpells=act)))
        return out
    if slot in ("potion", "food"):
        rows = core.q("SELECT id, base_id, tier, enchant FROM items WHERE slot=? AND id GLOB 'T[0-9]_*' ORDER BY tier DESC, enchant DESC", slot)
        best = {}
        for r in rows:
            best.setdefault(re.sub(r"^T\d_", "", r["base_id"]), r["id"])
        return [(label(i), dict(cur or {}, item=i)) for i in best.values()]
    ip = q1("SELECT itempower FROM items WHERE id=?", cur["item"])["itempower"]
    tier = q1("SELECT tier FROM items WHERE id=?", cur["item"])["tier"]
    rows = core.q("SELECT id, tier FROM items WHERE slot=? AND itempower=? AND id GLOB 'T[0-9]_*' AND id NOT LIKE '%GATHERER%' "
                  "AND shopcat NOT IN ('skins', 'vanity')", slot, ip)
    fams = {}
    for r in sorted(rows, key=lambda r: abs(r["tier"] - tier)):
        fams.setdefault(advisor._family(r["id"]), r["id"])
    out = []
    for iid in fams.values():
        base = {k: v for k, v in cur.items() if k not in ("activeSpells", "passiveSpells")}
        base["item"] = iid
        if slot == "cape":
            out.append((label(iid), base))
            continue
        actives, passives = gearcheck._slot_spells(iid)
        for a in (actives[0] if actives else []) or [None]:
            for p_ in passives or [None]:
                e = dict(base)
                if a:
                    e["activeSpells"] = [a[0]]
                if p_:
                    e["passiveSpells"] = [p_[0]]
                out.append((f"{label(iid)}: {a[1] if a else '—'} / {p_[1] if p_ else '—'}", e))
    return out


def _spell_name(sid):
    r = q1("SELECT name_en FROM spells WHERE id=?", sid)
    return r["name_en"] if r and r["name_en"] else sid


def _equip_slot(entry):
    return q1("SELECT slot FROM items WHERE id=?", core.resolve_item(entry["item"]))["slot"]


def pvp_tune(loadout, content="corrupted_stalker", vs="ranged", opp_ip=None, ips=None, slots=None, passes=3, top=5):
    """Coordinate search over the loadout's slots (weapon spells, head, armor, shoes with every active/passive, cape, potion,
    food) for the best average outcome (win − death) against reference opponents (ranged / melee / all) at opp_ip."""
    key = resolve_zone(content)
    rules = zone_rules(key)
    ip_spec = gearcheck._parse_ips(ips, 1)[0] if ips else {}
    opp_ip = float(opp_ip or (rules["cap"] * 1.3 if rules["cap"] else 1300))
    opps_ = reference_opponents(vs, opp_ip, rules)
    raw = json.loads(json.dumps(gearcheck._raw_loadout(loadout)))
    eq = {"weapon" if _equip_slot(e) == "mainhand" else _equip_slot(e): dict(e, item=core.resolve_item(e["item"]))
          for e in raw.get("equipment") or []}
    want = [s.strip() for s in (slots or ",".join(TUNE_SLOTS)).split(",") if s.strip()]
    for s_ in want:
        if s_ not in TUNE_SLOTS:
            raise AOError(f"Unknown slot {s_!r}: use {', '.join(TUNE_SLOTS)}")
    ip_avg = ip_spec.get("avg_ip")

    def build(eqd):
        lo = dict(raw, equipment=list(eqd.values()))
        spec = dict(ip_spec)
        if ip_avg:
            spec["avg_ip"] = ip_avg
        return build_pvp_player(json.dumps(lo, ensure_ascii=False), spec, rules)

    def evaluate(eqd):
        me = build(eqd)
        res = [duel(me, o) for o in opps_]
        return sum(r["win"] - r["lose"] for r in res) / len(res), res, me

    base_score, base_res, base_me = evaluate(eq)
    best, best_score = dict(eq), base_score
    rankings, tried = {}, 0
    for _ in range(max(1, min(passes, 5))):
        improved = False
        for s_ in want:
            if s_ not in best and s_ not in ("potion", "food"):
                continue
            cands = _slot_candidates(s_, best.get(s_) or {})
            scored = []
            for name, entry in cands:
                trial = dict(best)
                trial[s_] = entry
                try:
                    sc = evaluate(trial)[0]
                except (AOError, KeyError, TypeError, ZeroDivisionError):
                    continue
                tried += 1
                scored.append((sc, name, entry))
            if not scored:
                continue
            scored.sort(key=lambda x: -x[0])
            rankings[s_] = scored
            if scored[0][0] > best_score + 1e-6:
                best[s_], best_score, improved = scored[0][2], scored[0][0], True
        if not improved:
            break
    fin_score, fin_res, fin_me = evaluate(best)
    o = [f"## PvP gear tuning: “{raw.get('name') or 'loadout'}” → {rules['title']}", "",
         f"Opponents: {len(opps_)} reference **{vs}** builds at **{opp_ip:.0f} IP** (→ {effective_ip(opp_ip, rules):.0f} after the cap); "
         f"you: {base_me['avg']:.0f} → {base_me['eff_avg']:.0f} IP. {tried} variants simulated. Score = average (win − death).", ""]
    rows = []
    for op, a, b in zip(opps_, base_res, fin_res):
        rows.append((op["name"], f"{a['win']:.0%} / {a['disengage']:.0%} / {a['lose']:.0%}", f"{b['win']:.0%} / {b['disengage']:.0%} / {b['lose']:.0%}"))
    rows.append(("**score**", f"{base_score:+.2f}", f"**{fin_score:+.2f}**"))
    o.append(table(rows, ["opponent", "now: win / disengage / die", "tuned: win / disengage / die"]))
    changes = []
    for s_ in want:
        a, b = eq.get(s_), best.get(s_)
        if a != b and b:
            def desc(e):
                if not e:
                    return "—"
                sp = ", ".join(_spell_name(x) for x in (e.get("activeSpells") or []) + (e.get("passiveSpells") or []))
                return f"{label(e['item'])}" + (f" ({sp})" if sp else "")
            changes.append((s_, desc(a), desc(b)))
    o.append("\n### Changes\n" + (table(changes, ["slot", "now", "tuned"]) if changes else "None — the loadout is already the best "
                                     "the model finds for these slots."))
    for s_, sc in rankings.items():
        o.append(f"\n**{s_}** — top {top} (score with the rest tuned): " + "; ".join(f"{n} {v:+.2f}" for v, n, _ in sc[:top]))
    tuned = dict(raw, name=(raw.get("name") or "loadout") + " tuned", equipment=list(best.values()))
    o.append("\n### Import\n```json\n" + json.dumps(tuned, ensure_ascii=False, separators=(",", ":")) + "\n```")
    o.append("\n_Reference opponents are fixed archetypes, not the live killboard; run pvp_check with the tuned set for the field. "
             "Gear alternatives keep the current item power of each slot; cost them with build_cost._\n" + PVP_NOTE)
    return "\n".join(o)
