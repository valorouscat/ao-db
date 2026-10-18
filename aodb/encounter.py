"""Mob encounters simulated in time: each pull of the concrete monsters of a content (corrupted dungeon maps, Mists camps,
Mists dungeon, hellgate PvE, Roads camps) is fought second by second — the player's real kit damage (spells.json) against
each mob's HP and resistances, the mobs' auto-attacks and abilities (dodge share for telegraphed ones) against the player's
HP, resistances, shields, heals and lifesteal. Output: kill time, lowest HP, death risk per pull, clear time and fame per
hour per map, and the hardest pull.

Absolute times are model seconds (base spell numbers × item-power scaling); a time calibration from real clears
(`record_outcome ... clear_minutes=`) rescales them.
"""
import functools, json, math, statistics
from collections import Counter
from . import core, combat, gearcheck, pvp
from .core import AOError, q, q1, table, label

STEP = 0.5            # simulation step, seconds
MAX_FIGHT = 240.0     # a pull not killed within this is a fail (you run out of cooldowns / potions)
TRAVEL = 8.0          # seconds walking between pulls (assumption)
SKIP = ("ANTIRESET", "TELEPORT_TARGET", "TRAP_", "HAZARD_", "PATROL_", "_STATUE", "CD_STATUE", "CRITTER")
CONTENT = {  # key -> (title, encounters.content, default tier, zone rules key for soft cap / multipliers, continent)
    "corrupted_hunter": ("Corrupted Dungeon — Hunter", "corrupted", 5, "corrupted_hunter", None),
    "corrupted_stalker": ("Corrupted Dungeon — Stalker", "corrupted", 6, "corrupted_stalker", None),
    "corrupted_slayer": ("Corrupted Dungeon — Slayer", "corrupted", 8, "corrupted_slayer", None),
    "mists": ("Mists camps", "mists", 6, "mists_black", "Mists"),
    "mists_yellow": ("Mists camps (yellow)", "mists", 6, "mists_yellow", "Mists"),
    "mists_dungeon": ("Mists dungeon", "mists_dungeon", 6, "mists_dungeon", "Mists"),
    "hellgate": ("Hellgate PvE", "hellgate", 6, "hellgate_2v2", None),
}
ALIASES = [("slayer", "corrupted_slayer"), ("слеер", "corrupted_slayer"), ("stalker", "corrupted_stalker"), ("сталкер", "corrupted_stalker"),
           ("hunter", "corrupted_hunter"), ("хантер", "corrupted_hunter"), ("corrupt", "corrupted_stalker"), ("проклят", "corrupted_stalker"),
           ("mist dungeon", "mists_dungeon"), ("mists_dungeon", "mists_dungeon"), ("желт", "mists_yellow"), ("жёлт", "mists_yellow"),
           ("yellow", "mists_yellow"), ("mist", "mists"), ("мист", "mists"), ("туман", "mists"), ("hellgate", "hellgate"), ("адск", "hellgate")]


def resolve(content):
    s = (content or "").lower().strip()
    if s in CONTENT:
        return s
    for a, k in ALIASES:
        if a in s:
            return k
    raise AOError(f"Unknown encounter content {content!r}. Known: {', '.join(CONTENT)} (Roads camps: gear_check / camp_sim)")


# ------------------------------------------------------------------ monsters
@functools.lru_cache(maxsize=None)
def spawn_options(beh, tier, continent=None):
    """[(mob_id, probability, upgrade level)] for a spawn behaviour at a tier (per-tier variant, continent preferred)."""
    rows = q("SELECT continent, mobs FROM spawn_tiers WHERE name=? AND tier=?", beh, tier)
    pick = next((r for r in rows if continent and r["continent"] and continent.lower() in r["continent"].lower()), None) \
        or next((r for r in rows if not r["continent"]), None) or (rows[0] if rows else None)
    if pick:
        mobs = json.loads(pick["mobs"])
    else:
        r = q1("SELECT mobs FROM spawnbehaviors WHERE name=?", beh)
        if not r:
            return ()
        mobs = json.loads(r["mobs"])
        mobs = [dict(m, mob=_retier(m["mob"], tier)) for m in mobs]
    mobs = [m for m in mobs if "FOULRAT" not in (m["mob"] or "")]
    tot = sum(m["weight"] for m in mobs) or 1
    return tuple((m["mob"], m["weight"] / tot, m["level"]) for m in mobs if q1("SELECT 1 FROM mobs WHERE id=?", m["mob"]))


def _retier(mob, tier):
    cand = f"T{tier}_" + mob.split("_", 1)[1] if mob and mob[:1] == "T" and mob[1:2].isdigit() else mob
    return cand if q1("SELECT 1 FROM mobs WHERE id=?", cand) else mob


@functools.lru_cache(maxsize=None)
def mob(mob_id, solo=True):
    """Combat numbers of one mob + name and fame; damage estimated from similar mobs when the data has none."""
    p = combat.mob_profile(mob_id, solo)
    if not p:
        return None
    r = q1("SELECT name_en, fame, tier FROM mobs WHERE id=?", mob_id)
    out = dict(p, id=mob_id, name=r["name_en"] or mob_id, fame=r["fame"] or 0.0, tier=r["tier"] or 0, estimated=False)
    if p["auto"] + p["targeted"] + p["dodgeable"] <= 0 and p["hp"] > 300:
        out["auto"] = _dps_per_hp(out["tier"]) * p["hp"]
        out["estimated"] = True
    return out


@functools.lru_cache(maxsize=None)
def _dps_per_hp(tier):
    """Median (auto + ability DPS) / HP of mobs of a tier that have damage data — fallback for mobs without any."""
    vals = []
    for r in q("SELECT id FROM mobs WHERE tier=? AND hp > 300 AND hp < 20000 AND id NOT LIKE '%TEST%' LIMIT 600", tier):
        p = combat.mob_profile(r["id"], True)
        if p and p["auto"] + p["targeted"] > 0:
            vals.append((p["auto"] + p["targeted"] + p["dodgeable"]) / p["hp"])
    return statistics.median(vals) if vals else 0.05


def _skip(beh):
    return any(s in beh for s in SKIP)


# ------------------------------------------------------------------ simulation
class Fighter:
    """The player side of a fight: absolute kit damage by number of targets, defenses, HP."""

    def __init__(self, p, k=1.0):
        self.p = p
        w = p["weapon_e"]
        st = p["stats"]
        bonus = p["mix"].get("physical", 0) * (st["physicalspelldamagebonus"] + st["physicalattackdamagebonus"]) / 2 \
            + p["mix"].get("magic", 0) * (st["magicspelldamagebonus"] + st["magicattackdamagebonus"]) / 2
        # spell damage scales with the weapon's ability power; k = damage calibration from real outcomes (see sim_calibration)
        self.scale = combat.PER_IP ** ((p["weapon"] - 1000) / 100) * (1 + bonus) * p["ap"] * k
        self.k = k
        self.w = w
        cons = 0.0
        for e in p["entries"]:  # damaging consumables (poison potions)
            cs = core.item_json(e["id"]).get("@consumespell")
            if cs and (e["row"]["slot"] in ("food", "potion") or e["inventory"]):
                cons += combat.spell_dps(cs, 1)
        self.cons = cons
        d = p["def"]
        ipf = combat.PER_IP ** ((p["weapon"] - 1000) / 100) * p["ap"]
        self.sustain = (d["shield_ps"] + d["heal_self_ps"]) * ipf + d["heal_pct_ps"] * p["hp"]
        self.lifesteal = d["lifesteal"]
        self.cc = min(sum(min(f, gearcheck.CC_CAP_SPELL) for f, aoe in d["cc"]), gearcheck.CC_CAP_GROUP)
        self.invuln = min(d["invuln_frac"], 0.3)
        self.hp = p["hp"]
        self.res = p["res"]
        self.ranged = p["ranged"]

    @functools.lru_cache(maxsize=None)
    def dps(self, n):
        """(damage per second on the focused target, extra AoE damage per second on each other target)."""
        if not self.w:
            base1 = baseN = combat.reference_kit_dps(1)
        else:
            base1 = combat.kit_dps(self.w["id"], self.w["active"], 1)[0]
            baseN = combat.kit_dps(self.w["id"], self.w["active"], max(n, 1))[0]
        focus = (base1 + self.cons) * self.scale
        splash = max(baseN - base1, 0) * self.scale / max(n - 1, 1) if n > 1 else 0.0
        return focus, splash


def fight(f, pull, dodge):
    """Second-by-second fight against a pull [(mob, count)]: {'time', 'min_hp', 'died', 'dealt'}."""
    mobs = []
    for m, k in pull:
        mit = f.p["mix"].get("physical", 0) * combat.mitigation(m["armor"]) + f.p["mix"].get("magic", 0) * combat.mitigation(m["mres"])
        for _ in range(k):
            mobs.append({"hp": m["hp"], "mit": mit or 1.0, "dps": gearcheck.mob_dps(m, dodge, f.ranged)})
    hp, low, t = f.hp, f.hp, 0.0
    taken_mit = combat.mitigation(f.res)
    while mobs and t < MAX_FIGHT:
        alive = len(mobs)
        focus, splash = f.dps(alive)
        mobs.sort(key=lambda x: x["hp"])  # kill the weakest first: fewer attackers sooner
        dealt = focus * mobs[0]["mit"] * STEP
        mobs[0]["hp"] -= dealt
        for x in mobs[1:]:
            x["hp"] -= splash * x["mit"] * STEP
            dealt += splash * x["mit"] * STEP
        incoming = sum(x["dps"] for x in mobs) * taken_mit * (1 - f.cc) * (1 - f.invuln)
        heal = f.sustain + f.lifesteal * dealt / STEP * 0.3
        hp = min(f.hp, hp - (incoming - heal) * STEP)
        low = min(low, hp)
        if hp <= 0:
            return {"time": t, "min_hp": 0.0, "died": True}
        mobs = [x for x in mobs if x["hp"] > 0]
        t += STEP
    return {"time": t, "min_hp": max(low, 0) / f.hp, "died": False, "timeout": bool(mobs)}


# ------------------------------------------------------------------ maps
def _pulls(guards, tier, continent, active=None):
    """Guards of a template (optionally only active layers) → pulls [(expected mobs), elite chance, fame]."""
    pts = []
    for beh, x, z, layer in guards:
        if _skip(beh) or (active is not None and layer is not None and layer not in active):
            continue
        opts = spawn_options(beh, tier, continent)
        if opts:
            pts.append((x, z, (beh, opts)))
    out = []
    for grp in gearcheck._cluster(pts):
        mobs, fame, elite = Counter(), 0.0, 0.0
        for beh, opts in grp:
            # expected spawn: the most likely mob stands in for the time model; rare elites (level ≥ 4) raise risk
            common = max(opts, key=lambda o: o[1])
            mobs[common[0]] += 1
            for mid, pr, lvl in opts:
                mm = mob(mid)
                if mm:
                    fame += pr * mm["fame"]
                if lvl >= 4:
                    elite += pr
        pull = [(mob(mid), k) for mid, k in mobs.items() if mob(mid)]
        if pull:
            # elite check: the rarest high-level spawn of the pull replaces one of the common mobs (not all at once)
            beh_e, opts_e = max(grp, key=lambda g: max(o[2] for o in g[1]))
            top = max(opts_e, key=lambda o: (o[2], o[1]))
            worst = list(mobs.items())
            common = max(opts_e, key=lambda o: o[1])[0]
            worst = [(mid, k - (1 if mid == common else 0)) for mid, k in worst] + [(top[0], 1)]
            out.append({"pull": pull, "worst": [(mob(mid), k) for mid, k in worst if k > 0 and mob(mid)], "fame": fame,
                        "elite": min(elite, 1.0) if top[2] >= 4 else 0.0})
    return out


def _maps(kind, tier, continent, limit):
    """[(name, [pulls])] — concrete maps (cluster files with active layers) when the game data has them, else templates."""
    enc = {r["template"]: r for r in q("SELECT * FROM encounters WHERE content=?", kind)}
    runs = q("SELECT * FROM runs WHERE content=?", kind)
    out = []
    if runs and kind != "mists":  # Mists maps are assembled at runtime: the camp templates are the units there
        for r in runs[:limit]:
            pulls = []
            for tpl, layers in json.loads(r["instances"]):
                e = enc.get(tpl)
                if e:
                    pulls += _pulls(json.loads(e["guards"]), tier, continent, set(layers))  # no active layers = base layout only
            out.append((r["cluster"], pulls))
    else:
        return _maps_templates(enc, tier, continent, limit)
    out = [(n, p) for n, p in out if p]
    if not out and runs:
        return _maps_templates(enc, tier, continent, limit)
    return out


def _maps_templates(enc, tier, continent, limit):
    out = [(name, _pulls(json.loads(e["guards"]), tier, continent)) for name, e in enc.items()]
    out = [(n, p) for n, p in out if p]
    out.sort(key=lambda x: -sum(pl["fame"] for pl in x[1]))  # the richest camps first
    return out[:limit]


def _camp_eval(f, key, tier, stage, dodge):
    """[(seconds, lowest HP share, failed pulls, variant name)] for every template variant of a Roads camp."""
    behaviour = gearcheck.CONTENT[key][0]
    stage_i = gearcheck.STAGE_NAMES.get(str(stage).lower(), stage)
    up = q1("SELECT stages FROM chest_upgrades WHERE name=?", behaviour)
    st = sorted(json.loads(up["stages"]), key=lambda s_: s_["level"])[min(int(stage_i), 2)]
    out = []
    for layer in q("SELECT * FROM camps WHERE chest_behaviour=?", behaviour):
        if f"T{tier}" not in layer["layer"]:
            continue
        pts = [(x, z, v) for beh, x, z in json.loads(layer["guards"] or "[]") if not beh.startswith("ROAMING")
               for v in [gearcheck._variant(beh, st["level"], key == "avalon_solo")] if v]
        if not pts:
            continue
        t, low, died = 0.0, 1.0, 0
        for grp in gearcheck._cluster(pts):
            r = fight(f, [(g, 1) for g in grp], dodge)
            t += r["time"] + TRAVEL
            low = min(low, r["min_hp"])
            died += r["died"] or bool(r.get("timeout"))
        out.append((t, low, died, f"{layer['template']} › {layer['layer'].strip()}"))
    return out


def _camp_key(content):
    return content if content in gearcheck.CONTENT else next((v for a, v in gearcheck.ALIASES.items() if a in (content or "").lower()), None)


_cal = {}


def sim_calibration():
    """Damage factor k (player damage × k) fitted so the simulated lowest HP matches recorded real fights (min_hp), and a time
    scale from recorded clear_minutes. Recomputed when knowledge/calibration.json changes."""
    try:
        stamp = gearcheck.CALIBRATION_FILE.stat().st_mtime_ns
    except FileNotFoundError:
        stamp = None
    if _cal.get("stamp") == stamp:
        return _cal["v"]
    ks, ts = [], []
    for o in gearcheck._cal_load():
        key = _camp_key(o.get("content"))
        if not key or o.get("min_hp") is None or len(o.get("loadouts") or []) != 1:
            continue
        try:
            p = gearcheck.build_player(o["loadouts"][0], gearcheck._parse_ips(o.get("ips"), 1)[0], (o.get("intents") or [None])[0])
        except AOError:
            continue
        low_at = lambda k: statistics.median(r[1] for r in _camp_eval(Fighter(p, k), key, int(o["tier"]), o["stage"], gearcheck.DODGE))
        lo_k, hi_k = 0.5, 12.0
        if low_at(hi_k) < o["min_hp"]:
            continue
        for _ in range(14):  # bisection: lowest HP grows with damage
            mid = (lo_k + hi_k) / 2
            lo_k, hi_k = (mid, hi_k) if low_at(mid) < o["min_hp"] else (lo_k, mid)
        k = (lo_k + hi_k) / 2
        ks.extend([k] * max(int(o.get("runs") or 1), 1))
        if o.get("clear_minutes"):
            model = statistics.median(r[0] for r in _camp_eval(Fighter(p, k), key, int(o["tier"]), o["stage"], gearcheck.DODGE)) / 60
            ts.append(o["clear_minutes"] / model)
    v = {"k": statistics.median(ks) if ks else DEFAULT_K, "n": len(ks), "ts": statistics.median(ts) if ts else 1.0, "tn": len(ts)}
    _cal.update(stamp=stamp, v=v)
    return v


DEFAULT_K = 3.0  # used only when the journal has no usable real outcome


def simulate(f, maps, dodge):
    res = []
    for name, pulls in maps:
        tot_t, low, deaths, fame, worst_pull, survive = 0.0, 1.0, 0, 0.0, None, 1.0
        for pl in pulls:
            r = fight(f, pl["pull"], dodge)
            tot_t += r["time"] + TRAVEL
            fame += pl["fame"]
            if r["died"] or r.get("timeout"):
                deaths += 1
            if r["min_hp"] < low or worst_pull is None:
                low, worst_pull = min(low, r["min_hp"]), (pl, r)
            if pl["elite"] > 0.02:  # an elite spawn here: chance-weighted extra danger
                rw = fight(f, pl["worst"], dodge)
                if rw["died"] or rw.get("timeout"):
                    survive *= 1 - pl["elite"]
        res.append({"name": name, "pulls": len(pulls), "time": tot_t, "low": low, "deaths": deaths, "fame": fame,
                    "worst": worst_pull, "elite_death": 1 - survive})
    return res


def encounter_sim(loadout, content="corrupted_stalker", tier=None, ips=None, intents=None, dodge=gearcheck.DODGE,
                  dodge_low=gearcheck.DODGE_LOW, maps=8):
    """Simulate a loadout against the concrete monsters of a content, pull by pull."""
    key = resolve(content)
    title, kind, dtier, zone, continent = CONTENT[key]
    tier = int(tier or dtier)
    rules = pvp.zone_rules(zone)
    ip_spec = gearcheck._parse_ips(ips, 1)[0] if ips else {}
    p = gearcheck.build_player(loadout, ip_spec, intents)
    capped = False
    if rules["cap"] and p["weapon"] > rules["cap"]:  # the zone's soft cap applies to monsters' fights too
        p = dict(p, weapon=pvp.effective_ip(p["weapon"], rules), armor=pvp.effective_ip(p["armor"], rules))
        capped = True
    cal = sim_calibration()
    f = Fighter(p, cal["k"])
    mp = _maps(kind, tier, continent, maps)
    if not mp:
        raise AOError(f"No {kind} maps with monsters at T{tier} in the data")
    hi, lo = simulate(f, mp, dodge), simulate(f, mp, dodge_low)
    ts = cal["ts"]
    fame_mult = rules["fame"]
    rows = []
    for a, b in zip(hi, lo):
        mins = a["time"] * ts / 60
        rows.append((a["name"], a["pulls"], f"{mins:.1f}", f"{a['low']:.0%}", f"{b['low']:.0%}",
                     f"{a['deaths']}" + (f" (+{b['deaths'] - a['deaths']} @{dodge_low:.0%})" if b["deaths"] > a["deaths"] else ""),
                     f"{a['elite_death']:.0%}", f"{a['fame'] * fame_mult:,.0f}", f"{a['fame'] * fame_mult / max(mins, 0.1) * 60:,.0f}"))
    o = [f"## Encounter simulation: “{p['name']}” → {title} T{tier}", "",
         f"Weapon IP {p['weapon']:.0f}, armor IP {p['armor']:.0f}" + (f" (after the {rules['cap']:.0f} soft cap)" if capped else "")
         + f", HP {p['hp']:,.0f}, armor/res {p['res']:.0f}; damage {f.dps(1)[0]:,.0f}/s single target, "
         f"{f.dps(3)[0] + 2 * f.dps(3)[1]:,.0f}/s on 3 targets; sustain {f.sustain:,.0f}/s"
         + (f" + lifesteal {f.lifesteal:.0%}" if f.lifesteal else "") + (f"; CC uptime {f.cc:.0%}" if f.cc else "") + ".", "",
         table(rows, ["map", "pulls", "clear (min)", f"lowest HP @{dodge:.0%}", f"@{dodge_low:.0%}", "pulls failed",
                      "chance an elite kills you", f"fame (×{fame_mult:g} zone)", "fame / hour"])]
    hardest = min(hi, key=lambda r: r["low"])
    pl, r = hardest["worst"]
    o.append(f"\n**Hardest pull** ({hardest['name']}): " + ", ".join(f"{k}× {m['name']}" + (" ⚠est." if m["estimated"] else "")
                                                                    for m, k in pl["pull"])
             + f" — {r['time']:.0f}s, lowest HP {r['min_hp']:.0%}" + (" 💀" if r["died"] else ""))
    elites = sorted({m["name"] for x in hi for pl_ in [x["worst"][0]] for m, _ in pl_["worst"] if m}, key=str)[:6]
    if elites:
        o.append(f"Rare elite spawns that can replace guards: {', '.join(elites)}")
    hv = {}
    for _, pulls in mp:
        for pl_ in pulls:
            for m, _ in pl_["pull"]:
                for sid, dmg in m["heavy"]:
                    hv[sid] = max(hv.get(sid, 0), dmg)
    heavy = sorted(hv.items(), key=lambda h: -h[1])[:5]
    if heavy:
        left = [(sid, p["hp"] - dmg * combat.mitigation(p["res"]) * 1.5) for sid, dmg in heavy]
        o.append("**Heavy telegraphed hits (dodge them):** " + ", ".join(
            f"`{sid}` ({'💀 one-shot' if l <= 0 else f'{1 - l / p['hp']:.0%} HP'})" for sid, l in left))
    est = sorted({m["name"] for _, pulls in mp for pl_ in pulls for m, _ in pl_["pull"] if m["estimated"]})
    if est:
        o.append(f"_⚠est.: no attack data for {', '.join(est[:6])} — damage estimated from mobs of the same tier._")
    o.append("\n" + _cal_line(cal))
    o.append(f"_{TRAVEL:.0f} s walking per pull assumed; a pull counts as failed if you die or can't kill it within "
             f"{MAX_FIGHT:.0f} s. Fame = Σ mob fame × zone multiplier (expected spawns); chest loot not included. Corrupted dungeon maps in "
             f"the dump are the T6 layouts; other tiers reuse them with that tier's spawn variants._\n" + SIM_NOTE)
    return "\n".join(o)


def camp_sim(loadout, content="green", tier=6, stage="large", ips=None, intents=None, dodge=gearcheck.DODGE,
             dodge_low=gearcheck.DODGE_LOW):
    """Second-by-second fights on a Roads of Avalon camp: every template variant of the chest stage, its concrete guards."""
    key = _camp_key(content)
    if not key:
        raise AOError(f"Unknown camp content {content!r} (green / blue / gold)")
    ip_spec = gearcheck._parse_ips(ips, 1)[0] if ips else {}
    p = gearcheck.build_player(loadout, ip_spec, intents)
    cal = sim_calibration()
    f = Fighter(p, cal["k"])
    hi, lo = _camp_eval(f, key, int(tier), stage, dodge), _camp_eval(f, key, int(tier), stage, dodge_low)
    if not hi:
        raise AOError(f"No T{tier} camps for {gearcheck.CONTENT[key][0]}")
    mins = lambda rs: statistics.median(r[0] for r in rs) * cal["ts"] / 60
    worst = min(hi, key=lambda r: r[1])
    o = [f"## Camp simulation: “{p['name']}” → {gearcheck.CONTENT[key][1]}, T{tier} {stage}", "",
         table([(f"@{dodge:.0%} dodge", f"{mins(hi):.1f}", f"{statistics.median(r[1] for r in hi):.0%}", f"{worst[1]:.0%}",
                 f"{sum(1 for r in hi if r[2]) / len(hi):.0%}"),
                (f"@{dodge_low:.0%} dodge", f"{mins(lo):.1f}", f"{statistics.median(r[1] for r in lo):.0%}",
                 f"{min(r[1] for r in lo):.0%}", f"{sum(1 for r in lo if r[2]) / len(lo):.0%}")],
               ["scenario", "clear (min, median)", "lowest HP (median variant)", "lowest HP (worst variant)", "variants with a failed pull"]),
         f"Worst variant: {worst[3]} · {len(hi)} template variants", "", _cal_line(cal), SIM_NOTE]
    return "\n".join(o)


def _cal_line(cal):
    return (f"_Calibration: player damage × {cal['k']:.2f} " + (f"fitted on {cal['n']} real run(s) (lowest HP)" if cal["n"] else
            "(default — no real outcome with min_hp in the journal)") + f"; times × {cal['ts']:.2f}" +
            (f" from {cal['tn']} recorded clear time(s)" if cal["tn"] else " (no recorded clear times: add clear_minutes to record_outcome)") + "._")


def pve_summary(loadout, content, ips=None, intents=None, maps=4):
    """{'minutes', 'low', 'low_pess', 'fame_h', 'elite'} — median over maps, for farm_plan; None if not simulable."""
    try:
        key = resolve(content)
    except AOError:
        return None
    title, kind, tier, zone, continent = CONTENT[key]
    rules = pvp.zone_rules(zone)
    p = gearcheck.build_player(loadout, gearcheck._parse_ips(ips, 1)[0] if ips else {}, intents)
    if rules["cap"] and p["weapon"] > rules["cap"]:
        p = dict(p, weapon=pvp.effective_ip(p["weapon"], rules), armor=pvp.effective_ip(p["armor"], rules))
    cal = sim_calibration()
    f = Fighter(p, cal["k"])
    mp = _maps(kind, tier, continent, maps)
    if not mp:
        return None
    hi, lo = simulate(f, mp, gearcheck.DODGE), simulate(f, mp, gearcheck.DODGE_LOW)
    med = lambda xs: statistics.median(xs)
    mins = med([r["time"] for r in hi]) * cal["ts"] / 60
    return {"minutes": mins, "low": med([r["low"] for r in hi]), "low_pess": med([r["low"] for r in lo]),
            "fame_h": med([r["fame"] for r in hi]) * rules["fame"] / max(mins, 0.1) * 60, "elite": med([r["elite_death"] for r in hi]),
            "tier": tier}


SIM_NOTE = ("_Simulation: each pull (guards within 10 m) is fought in 0.5 s steps; your damage = auto-attacks + selected spells "
            "(spells.json, vs the number of mobs still alive; single-target part on the weakest mob, AoE part on the rest) × "
            "1.0918 per +100 weapon IP × item damage bonus × mob mitigation 100/(100+armor/mres); the mobs' damage = auto-attacks "
            "(melee halved when you kite with a ranged weapon) + targeted abilities + telegraphed abilities × (1 − dodge), × "
            "100/(100+your armor/mres) × (1 − your CC uptime), minus shields/heals/lifesteal. HP refills between pulls. "
            "Expected spawns use the most likely mob per spawn point; rare elites (upgrade level ≥ 4) are checked separately._")
