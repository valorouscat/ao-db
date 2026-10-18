"""Damage potential of spells, weapon kits and mobs, computed from spells.json / items.json / mobs.json.

Numbers are base values (before item-power scaling). They are used *relatively*: a kit is compared with the median kit of
all weapons in the game, a mob's abilities are added to its auto-attack, and resistances reduce damage by 100/(100+res)
(assumed formula). See gearcheck for how these feed the camp / group model.
"""
import functools, json, math, re, statistics
from .core import q, q1, num

PER_IP = 1.0918  # damage/ability power progression per +100 IP (gamedata.json ItemPowerProgression)
GCD = 1.0        # minimum cycle for spells without cooldown (global-ish cast cadence)
SKIP_KEYS = {"spellvfx", "AudioInfo", "locareferences", "spelleffectfx", "castfx", "hitfx", "vfx"}
MAX_TARGETS = 5  # cap for AoE without explicit maxeffectareatargets
MAX_PULSES = 30  # cap for pulsing/over-time counts (auras use 9999)
MAX_CAST_DAMAGE = 2000  # base damage per cast sanity cap (player kits are 50–700)


@functools.lru_cache(maxsize=None)
def spell_json(sid):
    r = q1("SELECT json FROM spells WHERE id=?", sid)
    return json.loads(r["json"]) if r else None


def _aslist(x):
    return x if isinstance(x, list) else ([] if x is None else [x])


def _targets_ok(node, vs):
    cond = node.get("IfTargetType")
    if isinstance(cond, dict) and cond.get("@type"):
        if (vs == "mobs") != (cond["@type"] == "mob"):
            return False
    t = (node.get("@target") or "").lower()
    if vs == "mobs" and "player" in t:
        return False
    if vs == "players" and "mob" in t:
        return False
    return "enemy" in t or "enemies" in t or t in ("target", "")


class SpellWalk:
    """Total damage of one cast (vs mobs or players), following applied/pulsing/multi/chained spells and effect areas."""

    def __init__(self, vs):
        self.vs = vs
        self.aoe = False
        self.max_targets = None
        self.types = {}
        self.seen = set()

    def walk_spell(self, sid, mult, depth):
        if not sid or depth > 6 or sid in self.seen:  # each effect counted once per cast (re-applications refresh)
            return 0.0
        self.seen.add(sid)
        d = spell_json(sid)
        return self.walk(d, mult, depth) if d else 0.0

    def walk(self, node, mult, depth):
        if depth > 10 or not isinstance(node, dict):
            return 0.0
        total = 0.0
        for k in ("@effectarearadius", "@maxeffectareatargets"):
            if k in node:
                self.aoe = True
                if k == "@maxeffectareatargets":
                    self.max_targets = max(self.max_targets or 0, int(num(node[k]) or MAX_TARGETS))
        for key, val in node.items():
            if key.startswith("@") or key in SKIP_KEYS or key.startswith("If"):
                continue
            for ch in _aslist(val):
                if not isinstance(ch, dict):
                    continue
                if key == "directattributechange":
                    if ch.get("@attribute") == "health" and (num(ch.get("@change")) or 0) < 0 and _targets_ok(ch, self.vs):
                        v = -num(ch["@change"]) * mult
                        total += v
                        et = ch.get("@effecttype") or "physical"
                        self.types[et] = self.types.get(et, 0) + v
                    continue
                if key == "attributechangeovertime":  # DoT/HoT: change per tick × ticks
                    if ch.get("@attribute") == "health" and (num(ch.get("@change")) or 0) < 0 and _targets_ok(ch, self.vs):
                        v = -num(ch["@change"]) * min(num(ch.get("@count")) or 1, MAX_PULSES) * mult
                        total += v
                        et = ch.get("@effecttype") or "magic"
                        self.types[et] = self.types.get(et, 0) + v
                    continue
                if key == "buffovertime":
                    if ch.get("@type") == "health" and (num(ch.get("@value")) or 0) < 0 and _targets_ok(ch, self.vs):
                        v = -num(ch["@value"]) * (num(ch.get("@time")) or 1) * mult
                        total += v
                        et = ch.get("@effecttype") or "magic"
                        self.types[et] = self.types.get(et, 0) + v
                    continue
                if ch.get("IfConsumeCharges"):  # needs charges of another spell (e.g. Explosive Arrows): counted on that spell
                    continue
                m = mult
                if key == "spelleffectarea":
                    self.aoe = True
                    interval = num(ch.get("@interval")) or num(ch.get("@pulseinterval")) or num(ch.get("@tickinterval"))
                    if interval:
                        m *= min((num(ch.get("@time")) or 1) / interval, 20)
                elif key == "pulsingspell":
                    cnt = num(ch.get("@count")) or 1
                    sub = spell_json(ch.get("@spell") or "") or {}
                    dot = _aslist(sub.get("attributechangeovertime"))
                    if dot and (num(sub.get("@maxstack")) or 1) <= 1:  # re-applying a non-stacking DoT only refreshes it
                        ticks = num(dot[0].get("@count")) or 1
                        cnt = (cnt + ticks - 1) / ticks
                    m *= min(cnt, MAX_PULSES)  # persistent auras use huge counts (9999): cap to one realistic window
                elif key.startswith("applyeffectonevent") or key.startswith("applyspellonevent"):
                    m *= num(ch.get("@count")) or 1  # e.g. Explosive Arrows: next N auto-attacks
                elif key == "chainspell":
                    m *= min(num(ch.get("@maxtargets")) or num(ch.get("@count")) or 1, MAX_TARGETS)
                elif key in ("circle", "cone", "rectangle"):
                    self.aoe = True
                for attr in ("@spell", "@effect"):
                    ref = ch.get(attr)
                    if ref and ref != "none" and spell_json(ref):
                        total += self.walk_spell(ref, m, depth + 1)
                total += self.walk(ch, m, depth + 1)
        return total


@functools.lru_cache(maxsize=None)
def spell_profile(sid, vs="mobs"):
    """{'dmg': per-cast damage, 'cycle': seconds, 'aoe': bool, 'targets': cap, 'types': {physical/magic: share}}"""
    d = spell_json(sid)
    if not d:
        return None
    w = SpellWalk(vs)
    raw = w.walk(d, 1.0, 0)
    unreliable = raw >= MAX_CAST_DAMAGE  # runaway nested copy/chain multipliers: don't trust the number
    dmg = 0.0 if unreliable else raw
    cd = num(d.get("@recastdelay")) or 0
    stages, cur, guard = 0, d, 0
    while cur and guard < 6:  # combo / recast chains: each extra press takes ~0.8 s
        ms = _aslist(cur.get("multispell"))
        if not ms:
            break
        cd = max(cd, num(ms[0].get("@timeoutcooldown")) or 0)
        nxt = ms[0].get("@spell")
        if not nxt or nxt == cur.get("@uniquename"):
            break
        stages += 1
        cur, guard = spell_json(nxt), guard + 1
    cycle = max(cd, GCD) + (num(d.get("@castingtime")) or 0) + 0.8 * stages
    if d.get("@target") == "ground" and not w.aoe and re.search(r"area|cone|radius", json.dumps(d)[:4000], re.I):
        w.aoe = True
    if not w.aoe:  # e.g. Explosive Arrows: the effect is applied to auto-attacks but explodes in an area
        desc = q1("SELECT desc_en FROM spells WHERE id=?", sid)
        if desc and re.search(r"explod|in an area|radius|all enemies|nearby enemies|cone", desc["desc_en"] or "", re.I):
            w.aoe = True
    tot = sum(w.types.values()) or 1
    targets = w.max_targets or (MAX_TARGETS if w.aoe else 1)
    if w.aoe and targets <= 1:  # a single-target projectile that spawns an area (e.g. Raging Storm): the area hits the pull
        targets = MAX_TARGETS
    return {"dmg": dmg, "cycle": cycle, "aoe": w.aoe, "targets": targets,
            "types": {k: v / tot for k, v in w.types.items()}, "category": d.get("@category"), "unreliable": unreliable}


MAX_SPELL_DPS = 250  # per-spell base DPS sanity cap (outliers come from nested copy/chain effects)


def spell_dps(sid, n_targets=1, vs="mobs"):
    p = spell_profile(sid, vs)
    if not p or not p["dmg"]:
        return 0.0
    hits = min(n_targets, p["targets"]) if p["aoe"] else 1
    return min(p["dmg"] * hits / p["cycle"], MAX_SPELL_DPS)


# ------------------------------------------------------------------ weapon kits
def weapon_spells(base_item):
    """{slot: [(spell_id, name, category)]} — slot 1/2/3 = Q/W/E, 'passive'."""
    out = {}
    for r in q("SELECT s.spell_id, s.slots, sp.name_en, sp.name_ru, sp.category FROM item_spells s LEFT JOIN spells sp ON sp.id=s.spell_id "
               "WHERE s.item_id=?", base_item):
        out.setdefault(r["slots"] or "passive", []).append((r["spell_id"], r["name_en"], r["name_ru"], r["category"]))
    return out


def _autoattack_dps(item_id, n_targets=1):
    d = json.loads(q1("SELECT json FROM items WHERE id=?", item_id)["json"])
    return (num(d.get("@attackdamage")) or 0) * (num(d.get("@attackspeed")) or 1)


def pick_spells(item_id, intent="damage", n_targets=3):
    """Choose Q/W/E by intent per slot: 'damage' (max DPS vs mobs) or 'heal' (heal category first). intent may be a dict per slot."""
    base = q1("SELECT base_id FROM items WHERE id=?", item_id)["base_id"]
    kit = weapon_spells(base)
    chosen = []
    for slot in ("1", "2", "3"):
        opts = kit.get(slot) or []
        if not opts:
            continue
        want = intent.get(slot, "damage") if isinstance(intent, dict) else intent
        if want == "heal":
            heals = [o for o in opts if o[3] == "heal"]
            if heals:
                chosen.append(heals[0][0])
                continue
        chosen.append(max(opts, key=lambda o: spell_dps(o[0], n_targets))[0])
    return chosen


def kit_dps(item_id, spells, n_targets=3):
    """Base DPS of auto-attacks + chosen active spells vs a pull of n_targets mobs, and its damage-type mix."""
    aa = _autoattack_dps(item_id, n_targets)
    total, types = aa, {"physical": aa}
    parts = [("auto-attack", aa)]
    for sid in spells:
        v = spell_dps(sid, n_targets)
        p = spell_profile(sid) or {"types": {}}
        for t, share in p["types"].items():
            types[t] = types.get(t, 0) + v * share
        total += v
        parts.append((sid, v))
    tot = sum(types.values()) or 1
    return total, {k: v / tot for k, v in types.items()}, parts


@functools.lru_cache(maxsize=None)
def reference_kit_dps(n_targets=3):
    """Median best-damage kit DPS over all base weapons (T4 versions) — the '1.0' weapon."""
    vals = []
    for r in q("SELECT DISTINCT item_id FROM item_spells WHERE item_id LIKE 'T4\\_%' ESCAPE '\\'"):
        it = q1("SELECT slot, shopcat FROM items WHERE id=?", r["item_id"])
        if not it or it["slot"] != "mainhand" or it["shopcat"] != "weapons":
            continue
        sp = pick_spells(r["item_id"], "damage", n_targets)
        v, _, _ = kit_dps(r["item_id"], sp, n_targets)
        if v > 0:
            vals.append(v)
    return statistics.median(vals) if vals else 1.0


def weapon_factor(item_id, spells, n_targets=3):
    v, types, parts = kit_dps(item_id, spells, n_targets)
    return v / reference_kit_dps(n_targets), types, parts


# ------------------------------------------------------------------ mobs
@functools.lru_cache(maxsize=None)
def mob_abilities(mob_id):
    """Top-level damaging abilities of a mob, found by its prefab name (mob AI files are not in the dump)."""
    r = q1("SELECT json FROM mobs WHERE id=?", mob_id)
    if not r:
        return []
    d = json.loads(r["json"])
    prefab = d.get("@prefab") or ""
    stem = re.sub(r"(_(BOSS|MINIBOSS|CHAMPION|ELITE|VETERAN|STANDARD|SOLO))*(_\d+)?$", "", prefab)
    if not stem or len(stem) < 8:
        return []
    out = []
    for s in q("SELECT id, cooldown FROM spells WHERE id LIKE ? ESCAPE '\\' AND category IN ('damage','debuff','crowdcontrol','instant') "
               "AND cooldown > 2", stem + "\\_%"):
        if re.search(r"_(EFFECT|APPLY|SOUND|DAMAGE|KNOCKBACK|IMMUNITY|AURA|COUNTER|START|ONDEATH|VOICE\w*)$", s["id"]):
            continue
        p = spell_profile(s["id"], "players")
        if p and p["dmg"] > 0:
            out.append((s["id"], p["dmg"], p["cycle"], p["aoe"]))
    return out


HEAVY_HIT = 1500  # per-cast damage (after ability power) treated as a telegraphed heavy hit to dodge


def _ability_group(sid):
    s = sid
    for _ in range(3):
        s = re.sub(r"_(SOLO|INVERTED|TARGETED|CW|CCW|MR|ML|RM|LM|OM|MO|FINALE|CHAMPION|STANDARD|VETERAN|ELITE|BOSS|MINIBOSS|\d+)$", "", s)
    return s


@functools.lru_cache(maxsize=None)
def mob_combat(mob_id, solo=False):
    """Mob combat numbers. Abilities: alternatives grouped (variants count once), top 2 groups, each capped at 2× auto-attack DPS;
    single hits ≥ HEAVY_HIT are reported as telegraphed mechanics instead of sustained DPS."""
    r = q1("SELECT hp, damage, armor, mres, json FROM mobs WHERE id=?", mob_id)
    if not r or not r["hp"]:
        return None
    d = json.loads(r["json"])
    ap = (num(d.get("@abilitypower")) or 100) / 100
    auto = (r["damage"] or 0) * (num(d.get("@attackspeed")) or 1)
    groups, heavy = {}, []
    for sid, dmg, cyc, aoe in mob_abilities(mob_id):
        if solo is False and sid.endswith("_SOLO"):
            continue
        hit = dmg * ap
        if hit >= HEAVY_HIT:
            heavy.append((sid, round(hit)))
            continue
        g = _ability_group(sid)
        groups[g] = max(groups.get(g, 0), min(hit / cyc, 2 * auto))
    spells = sum(sorted(groups.values(), reverse=True)[:2])
    return {"hp": r["hp"], "dps_auto": auto, "dps_spells": spells, "dps": auto + spells, "armor": r["armor"] or 0,
            "mres": r["mres"] or 0, "abilities": sorted(groups), "heavy": heavy}


def mitigation(res):
    """Damage multiplier for a resistance value (assumed 100/(100+res))."""
    return 100 / (100 + max(res or 0, 0))


# ------------------------------------------------------------------ dodging, heavy hits, player defenses
def single_hit(sid, depth=0, seen=None):
    """Largest single application of damage to a player in an ability tree (no pulse multipliers): a 'caught' hit."""
    seen = seen if seen is not None else set()
    d = spell_json(sid)
    if not d or sid in seen or depth > 6:
        return 0.0
    seen.add(sid)
    best = 0.0

    def walk(n):
        nonlocal best
        if not isinstance(n, dict):
            return
        for k, v in n.items():
            if k.startswith("@") or k in SKIP_KEYS:
                continue
            for ch in _aslist(v):
                if not isinstance(ch, dict):
                    continue
                if k == "directattributechange" and ch.get("@attribute") == "health" and (num(ch.get("@change")) or 0) < 0 \
                        and _targets_ok(ch, "players"):
                    best = max(best, -num(ch["@change"]))
                elif k == "attributechangeovertime" and ch.get("@attribute") == "health" and (num(ch.get("@change")) or 0) < 0 \
                        and _targets_ok(ch, "players"):
                    best = max(best, -num(ch["@change"]) * min(num(ch.get("@count")) or 1, MAX_PULSES))
                for a in ("@spell", "@effect"):
                    r = ch.get(a)
                    if r and r != "none" and spell_json(r):
                        best = max(best, single_hit(r, depth + 1, seen))
                walk(ch)
    walk(d)
    return best


def telegraphed(sid):
    """Ground-targeted / area abilities with a wind-up can be dodged; instant targeted ones cannot."""
    d = spell_json(sid) or {}
    windup = (num(d.get("@castingtime")) or 0) + (num(d.get("@hitdelay")) or 0)
    return d.get("@target") in ("ground", "self") and windup >= 0.3 or (d.get("@target") == "ground")


@functools.lru_cache(maxsize=None)
def mob_profile(mob_id, solo=False):
    """Mob numbers split for dodging: auto-attack, targeted ability DPS, dodgeable ability DPS, heavy hits (single hit × AP)."""
    r = q1("SELECT hp, damage, armor, mres, json FROM mobs WHERE id=?", mob_id)
    if not r or not r["hp"]:
        return None
    d = json.loads(r["json"])
    ap = (num(d.get("@abilitypower")) or 100) / 100
    auto = (r["damage"] or 0) * (num(d.get("@attackspeed")) or 1)
    groups, heavy = {}, []
    for sid, dmg, cyc, aoe in mob_abilities(mob_id):
        if solo is False and sid.endswith("_SOLO"):
            continue
        hit = single_hit(sid) * ap
        if hit >= HEAVY_HIT:
            heavy.append((sid, round(hit)))
            continue
        g = _ability_group(sid)
        dps = min(dmg * ap / cyc, 2 * auto)
        if dps > groups.get(g, (0, False))[0]:
            groups[g] = (dps, telegraphed(sid))
    top = sorted(groups.values(), key=lambda x: -x[0])[:2]
    return {"hp": r["hp"], "auto": auto, "dodgeable": sum(x[0] for x in top if x[1]), "targeted": sum(x[0] for x in top if not x[1]),
            "armor": r["armor"] or 0, "mres": r["mres"] or 0, "melee": d.get("@attacktype") == "melee",
            "heavy": heavy, "abilities": sorted(groups)}


class DefWalk:
    """Defensive value of a player's spells/consumables: shields, self/ally heals, lifesteal, CC on enemies, invulnerability."""

    def __init__(self):
        self.shield = 0.0      # absorb per cast
        self.heal_self = 0.0   # flat heal per cast
        self.heal_ally = 0.0
        self.heal_pct = 0.0    # % max HP per cast
        self.lifesteal = 0.0   # fraction of damage dealt
        self.cc = 0.0          # seconds of hard CC applied per cast (per target)
        self.invuln = 0.0      # seconds untargetable/immune per cast
        self.seen = set()

    def spell(self, sid, mult=1.0, depth=0, ctx=""):
        d = spell_json(sid)
        if not d or sid in self.seen or depth > 6:
            return
        self.seen.add(sid)
        self.walk(d, mult, depth, ctx)

    def walk(self, n, mult, depth, ctx=""):
        if not isinstance(n, dict):
            return
        for k, v in n.items():
            if k.startswith("@") or k in SKIP_KEYS:
                continue
            for ch in _aslist(v):
                if not isinstance(ch, dict):
                    continue
                t = (ch.get("@target") or "").lower()
                ally = "ally" in t or "friend" in t or (ctx == "ally" and t in ("target", "self", ""))
                own = t in ("self", "", "target") and ctx != "enemy" or ally
                if k == "damageshield" and own:
                    self.shield += (num(ch.get("@damageabsorbed")) or 0) * mult
                elif k == "directattributechange" and ch.get("@attribute") == "health" and (num(ch.get("@change")) or 0) > 0 and own:
                    val = num(ch["@change"])
                    if val < 1:
                        self.heal_pct += val * mult
                    elif ally:
                        self.heal_ally += val * mult
                    else:
                        self.heal_self += val * mult
                elif k == "attributechangeovertime" and ch.get("@attribute") == "health" and (num(ch.get("@change")) or 0) > 0 and own:
                    val = num(ch["@change"]) * min(num(ch.get("@count")) or 1, MAX_PULSES)
                    if num(ch["@change"]) < 1:
                        self.heal_pct += val * mult
                    elif ally:
                        self.heal_ally += val * mult
                    else:
                        self.heal_self += val * mult
                elif k in ("healonhit", "healonhitpassive"):
                    self.lifesteal += num(ch.get("@percentage")) or 0
                elif k in ("stun", "silence", "cannotattack", "root", "knockback", "forcedmovement", "imprison", "fear", "sleep") \
                        and "enemy" in t:
                    sec = num(ch.get("@time")) or (0.5 if k in ("knockback", "forcedmovement") else 0)
                    self.cc += sec * (0.5 if k == "root" else 1.0) * mult  # roots stop melee, not casters
                elif k in ("invincibility", "invisibility", "nothittable", "notselectable") and own:
                    self.invuln += (num(ch.get("@time")) or 0) * mult
                m = mult
                if k.startswith("applyeffectonevent"):
                    m *= min(num(ch.get("@count")) or 1, 10)
                elif k == "pulsingspell":
                    m *= min(num(ch.get("@count")) or 1, MAX_PULSES)
                sub_ctx = "ally" if ("ally" in t or "friend" in t) else ("enemy" if "enemy" in t else ctx)
                for a in ("@spell", "@effect"):
                    r = ch.get(a)
                    if r and r != "none" and spell_json(r):
                        self.spell(r, m, depth + 1, sub_ctx)
                self.walk(ch, m, depth + 1, sub_ctx)


@functools.lru_cache(maxsize=None)
def spell_defense(sid):
    """Per-second defensive value of one spell (cooldown-normalised) — dict of rates."""
    d = spell_json(sid)
    if not d:
        return None
    w = DefWalk()
    w.spell(sid)
    cycle = max(num(d.get("@recastdelay")) or 0, GCD) + (num(d.get("@castingtime")) or 0)
    passive = q1("SELECT kind FROM spells WHERE id=?", sid)
    is_passive = passive and passive["kind"] == "passivespell"
    if is_passive or (num(d.get("@recastdelay")) or 0) >= 600:  # passives / long food buffs: always on
        cycle = None
    rate = (lambda x: x / cycle) if cycle else (lambda x: x)
    return {"shield_ps": rate(w.shield) if cycle else 0.0, "heal_self_ps": rate(w.heal_self) if cycle else 0.0,
            "heal_ally_ps": rate(w.heal_ally) if cycle else 0.0, "heal_pct_ps": rate(w.heal_pct) if cycle else 0.0,
            "lifesteal": w.lifesteal, "cc_frac": (w.cc / cycle) if cycle else 0.0, "invuln_frac": (w.invuln / cycle) if cycle else 0.0,
            "aoe": (spell_profile(sid) or {}).get("aoe", False)}
