"""Can this loadout farm that PvE content? Loadout analysis + camp strength model from the game files.

Model (transparent, documented in the output):
- Player power: weapon IP (damage) and head/armor/shoes IP (survivability), incl. quality bonus, mastery (weapon_ip) and
  optional spec IP; the fight model uses their mean. The game's average IP (6 slots, 2H counted twice) is shown too.
- Per +100 IP the game scales weapon damage ×1.0918 and survivability ×≈1.0918 (HP ×1.06 · armor ×1.03), so a fight's
  balance (enemy HP × enemy DPS vs player DPS × player EHP) shifts by ×1.192 per 100 IP (gamedata.json ItemPowerProgression).
- Content strength: guards of the camp at each chest stage (templates + randomspawnbehaviors + mobs). The base stage of a
  solo (green) camp of tier T is assumed to be tuned for tier-T .0 gear (the common anchor for all camps); any camp/stage needs
  IP = par + 100·ln(F/F_anchor)/ln(1.192),
  where F = HP × DPS of the hardest pull (the camp boss slot, or the 3 strongest guards).
"""
import json, math, re
from collections import Counter
from . import core, advisor, market
from .core import AOError, q, q1, label, money, fmt, table, resolve_item

PER100 = math.log(1.0918 * 1.0918)
COMBAT_SLOTS = ("mainhand", "offhand", "head", "armor", "shoes", "cape")
QUALITY_IP = {1: 0, 2: 20, 3: 40, 4: 60, 5: 100}
STAGE_NAMES = {"small": 0, "малый": 0, "base": 0, "medium": 1, "средний": 1, "champion": 1, "large": 2, "большой": 2, "boss": 2}
CONTENT = {
    "avalon_solo": ("AVALON_SMALL_SOLO", "Roads of Avalon solo camps (green)", [4, 6, 8]),
    "avalon_veteran": ("AVALON_MEDIUM_VETERAN", "Roads of Avalon veteran camps (blue)", [4, 6, 8]),
    "avalon_elite": ("AVALON_MEDIUM_ELITE", "Roads of Avalon elite camps (gold)", [6, 8]),
}
ALIASES = {"green": "avalon_solo", "зел": "avalon_solo", "solo": "avalon_solo", "blue": "avalon_veteran", "син": "avalon_veteran",
           "veteran": "avalon_veteran", "gold": "avalon_elite", "зол": "avalon_elite", "elite": "avalon_elite"}
KIT_RULES = [  # (flag, regex over spell description/name/category)
    ("AoE", r"\bcone\b|\barea\b|radius|explod|all enemies|nearby enemies|around you|in a line|конус|област"),
    ("sustain", r"restor\w* .*health|heal|lifesteal|steal .*health|health the enemy has lost"),
    ("defensive", r"shield|immun|invisib|damage taken|resistances|unstoppable|untargetable|reduce\w* damage"),
    ("mobility", r"dash|sprint|move speed|blink|jump|leap|teleport"),
    ("crowd control", r"\bstun|\broot|\bslow|knock|silence|fear|purge|interrupt"),
]


# ------------------------------------------------------------------ loadout
def parse_loadout(loadout):
    if isinstance(loadout, str):
        s = loadout.strip()
        if s.startswith("@"):
            with open(s[1:], encoding="utf-8") as fh:
                s = fh.read()
        try:
            loadout = json.loads(s)
        except json.JSONDecodeError as e:
            raise AOError(f"Loadout is not valid JSON: {e}")
    entries = []
    for e in (loadout.get("equipment") or []) + [dict(x, _inventory=True) for x in (loadout.get("inventory") or [])]:
        iid = resolve_item(e["item"])
        it = q1("SELECT * FROM items WHERE id=?", iid)
        entries.append({"id": iid, "row": it, "quality": int(e.get("quality") or 1), "stack": int(e.get("stack") or 1),
                        "ip": e.get("ip") or e.get("itemPower"),
                        "active": e.get("activeSpells") or [], "passive": e.get("passiveSpells") or [], "inventory": bool(e.get("_inventory"))})
    if not entries:
        raise AOError("Loadout has no equipment")
    return loadout.get("name") or "loadout", entries


def parse_slot_ip(slot_ip):
    """{'mainhand': 1300, 'head': 1150} from a dict, 'mainhand=1300,head=1150' or ['mainhand=1300', ...]."""
    if not slot_ip:
        return {}
    if isinstance(slot_ip, dict):
        items = slot_ip.items()
    else:
        parts = slot_ip if isinstance(slot_ip, list) else re.split(r"[,;\s]+", slot_ip)
        items = [p.split("=", 1) for p in parts if "=" in p]
    aliases = {"weapon": "mainhand", "оружие": "mainhand", "helmet": "head", "шлем": "head", "chest": "armor", "куртка": "armor",
               "броня": "armor", "boots": "shoes", "ботинки": "shoes", "плащ": "cape", "offhand": "offhand", "левая": "offhand"}
    out = {}
    for k, v in items:
        k = aliases.get(str(k).strip().lower(), str(k).strip().lower())
        if k not in COMBAT_SLOTS:
            raise AOError(f"Unknown slot {k!r}; use {', '.join(COMBAT_SLOTS)}")
        out[k] = float(v)
    return out


def loadout_ip(entries, spec_ip=0, weapon_ip=None, slot_ip=None, avg_ip=None):
    """Per-slot IP of combat items and the game's average (6 slots, 2H weapon counted twice).

    Priority per slot: slot_ip / weapon_ip (in-game values incl. mastery) > 'ip' field in the loadout entry > computed
    (item IP + quality). If avg_ip (the character's in-game average) is given, slots without an explicit value get an equal
    bonus so that the average matches it. spec_ip adds a flat bonus to every slot that has no explicit value."""
    fixed = parse_slot_ip(slot_ip)
    if weapon_ip:
        fixed.setdefault("mainhand", float(weapon_ip))
    rows = []  # [slot, ip, weight, source]
    for e in entries:
        it, slot = e["row"], e["row"]["slot"]
        if e["inventory"] or slot not in COMBAT_SLOTS or not it["itempower"]:
            continue
        w = 2 if slot == "mainhand" and core.item_json(e["id"]).get("@twohanded") == "true" else 1
        if slot in fixed:
            rows.append([slot, fixed[slot], w, "given"])
        elif e.get("ip"):
            rows.append([slot, float(e["ip"]), w, "loadout"])
        else:
            rows.append([slot, it["itempower"] + QUALITY_IP.get(e["quality"], 0) + spec_ip, w, "item+quality" + (" +spec" if spec_ip else "")])
    if not rows:
        raise AOError("No combat items (weapon/armor/cape) in the loadout")
    n = sum(r[2] for r in rows)
    if avg_ip:
        free = [r for r in rows if r[3] not in ("given", "loadout")]
        if free:
            bonus = (avg_ip * n - sum(r[1] * r[2] for r in rows)) / sum(r[2] for r in free)
            for r in free:
                r[1] += bonus
                r[3] = f"distributed ({bonus:+.0f})"
    rows = [tuple(r) for r in rows]
    return sum(r[1] * r[2] for r in rows) / n, rows


def model_ip(rows, spec_ip=0):
    """IP the fight model uses: damage scales with the weapon (main/off hand), survivability with head/armor/shoes,
    so the balance point is the mean of the two (both progress ×1.0918 per 100 IP in gamedata.json)."""
    off = [r[1] for r in rows if r[0] in ("mainhand", "offhand")]
    deff = [r[1] for r in rows if r[0] in ("head", "armor", "shoes")]
    if not off or not deff:
        return None
    return (sum(off) / len(off) + sum(deff) / len(deff)) / 2


def kit(entries):
    """Spell kit flags + consumables, from the selected spells' descriptions."""
    flags, spells = {f: [] for f, _ in KIT_RULES}, []
    for e in entries:
        for sid in e["active"] + e["passive"]:
            s = q1("SELECT * FROM spells WHERE id=?", sid)
            if not s:
                continue
            text = " ".join(filter(None, [s["name_en"], s["category"], core.spell_text(s, json.loads(s["json"]), "en")[0]])).lower()
            spells.append((e["row"]["slot"], sid, s["name_en"], s["category"]))
            for f, rx in KIT_RULES:
                if re.search(rx, text):
                    flags[f].append(s["name_en"] or sid)
        if e["row"]["slot"] in ("food", "potion") or e["inventory"]:
            cs = core.item_json(e["id"]).get("@consumespell")
            s = q1("SELECT * FROM spells WHERE id=?", cs) if cs else None
            if s:
                text = core.spell_text(s, json.loads(s["json"]), "en")[0].lower()
                for f, rx in KIT_RULES:
                    if re.search(rx, text):
                        flags[f].append(f"{e['row']['name_en']} (consumable)")
    return flags, spells


# ------------------------------------------------------------------ camps
def _mob_stats(mid):
    r = q1("SELECT hp, damage, json_extract(json,'$.\"@attackspeed\"') aspd, name_en FROM mobs WHERE id=?", mid)
    if not r or not r["hp"]:
        return None
    return {"id": mid, "name": r["name_en"], "hp": r["hp"], "dps": (r["damage"] or 0) * float(r["aspd"] or 1)}


def camp_at_stage(spawns, level):
    """Guards of a camp layer at chest upgrade level: each spawn point uses its highest mob variant with level ≤ chest level."""
    guards = []
    for beh, n in spawns.items():
        r = q1("SELECT mobs FROM spawnbehaviors WHERE name=?", beh)
        if not r:
            continue
        mobs = json.loads(r["mobs"])
        ok = [m for m in mobs if m["level"] <= level] or mobs[:1]
        top = max(m["level"] for m in ok)
        cands = [s for s in (_mob_stats(m["mob"]) for m in ok if m["level"] == top) if s]
        if not cands:
            continue
        avg = {"name": cands[0]["name"] if len(cands) == 1 else f"{len(cands)} possible ({cands[0]['name']}, …)",
               "hp": sum(c["hp"] for c in cands) / len(cands), "dps": sum(c["dps"] for c in cands) / len(cands),
               "boss": "BOSS" in beh, "roaming": beh.startswith("ROAMING")}
        guards += [avg] * n
    return [g for g in guards if not g["roaming"]]


def _hardest_pull(guards):
    if not guards:
        return 0, 0
    boss = [g for g in guards if g["boss"]]
    trio = sorted((g for g in guards if not g["boss"]), key=lambda g: -g["hp"] * g["dps"])[:3]
    f_boss = max((g["hp"] * g["dps"] for g in boss), default=0)
    f_trio = sum(g["hp"] for g in trio) * sum(g["dps"] for g in trio)
    return max(f_boss, f_trio), f_boss >= f_trio


def content_profile(behaviour, tiers):
    """[(tier, stage_idx, chest, level, guards, F)] for a chest behaviour (one representative layer per tier)."""
    up = q1("SELECT stages FROM chest_upgrades WHERE name=?", behaviour)
    if not up:
        raise AOError(f"No chest-upgrade data for {behaviour}")
    stages = sorted(json.loads(up["stages"]), key=lambda s: s["level"])
    camps = q("SELECT * FROM camps WHERE chest_behaviour=?", behaviour)
    out = []
    for t in tiers:
        layer = next((c for c in camps if re.search(rf"T{t}\b", c["layer"]) and "SOLO_01" in c["template"]), None) \
            or next((c for c in camps if re.search(rf"T{t}\b", c["layer"])), None)
        if not layer:
            continue
        spawns = json.loads(layer["spawns"])
        spawns = {k: v for k, v in spawns.items() if re.match(rf"T{t}_", k) or re.search(rf"_T{t}$", k) or k.startswith("ROAMING")}
        for i, st in enumerate(stages):
            guards = camp_at_stage(spawns, st["level"])
            f, _ = _hardest_pull(guards)
            out.append({"tier": t, "stage": i, "chest": st["chest"], "level": st["level"], "weight": st["weight"], "guards": guards,
                        "F": f, "template": f"{layer['template']} › {layer['layer']}"})
    return out


_anchor_cache = {}


def anchor_F(tier):
    """Hardest-pull strength of a base-stage solo Avalon camp of this tier — the reference tuned for tier-T .0 gear."""
    if tier not in _anchor_cache:
        prof = content_profile("AVALON_SMALL_SOLO", [tier])
        _anchor_cache[tier] = next((p["F"] for p in prof if p["stage"] == 0), None)
    return _anchor_cache[tier]


def required_ip(p):
    par = 700 + 100 * (p["tier"] - 4)
    ref = anchor_F(p["tier"])
    return par + (100 * math.log(p["F"] / ref) / PER100 if ref and p["F"] else 0)


BURST_GAP = 150  # focused player's raw armor IP this far below the content tier's gear IP → burst / one-shot risk


def _verdict_capped(margin, armor_ip, tier):
    """Verdict from the margin, capped when raw armor IP is far below the content tier (heals/kiting don't stop bursts)."""
    v = _verdict(margin)
    gap = 700 + 100 * (tier - 4) - armor_ip
    if gap > BURST_GAP and margin >= -200:
        return "🟠 burst risk: armor " + f"{gap:.0f} IP below tier"
    return v


def _verdict(margin):
    if margin >= 0:
        return "✅ comfortable"
    if margin >= -200:
        return "🟡 doable with good play / spec"
    if margin >= -400:
        return "🟠 hard, high risk"
    return "❌ not recommended"


# ------------------------------------------------------------------ tool
def gear_check(loadout, content="avalon_solo", tiers=None, stages=None, spec_ip=0, weapon_ip=None, slot_ip=None, avg_ip=None,
               server="europe", city="Caerleon", price=True):
    name, entries = parse_loadout(loadout)
    key = content if content in CONTENT else next((v for a, v in ALIASES.items() if a in (content or "").lower()), None)
    if not key:
        raise AOError(f"Unknown content {content!r}. Supported: {', '.join(CONTENT)} (aliases: green/blue/gold).")
    behaviour, title, default_tiers = CONTENT[key]
    tiers = [int(t) for t in (tiers or default_tiers)]
    want = None
    if stages:
        want = {STAGE_NAMES.get(str(s).lower(), s) for s in stages}
    game_avg, slot_ips = loadout_ip(entries, spec_ip, weapon_ip, slot_ip, avg_ip)
    fight_ip = model_ip(slot_ips) or game_avg
    _arm = [r[1] for r in slot_ips if r[0] in ("head", "armor", "shoes")]
    armor_ip = sum(_arm) / len(_arm) if _arm else game_avg
    flags, spells = kit(entries)
    prof = content_profile(behaviour, tiers)

    o = [f"## Gear check: “{name}” → {title}", ""]
    # loadout
    rows = []
    for e in entries:
        it = e["row"]
        rows.append((it["slot"] or it["kind"], f"![]({core.ICON.format(e['id'])}?size=32&quality={e['quality']}) {label(e['id'])}",
                     core.QUALITY_NAMES.get(e["quality"], e["quality"]), (it["itempower"] or 0) + QUALITY_IP.get(e["quality"], 0) if it["itempower"] else "",
                     ", ".join(e["active"] + e["passive"]) + (f" ×{e['stack']}" if e["stack"] > 1 else "") + (" (bag)" if e["inventory"] else "")))
    o.append(table(rows, ["slot", "item", "quality", "IP", "spells / stack"]))
    o.append("\n### Item power used\n" + table([(sl, f"{ip:.0f}", "×2 (two-handed)" if w == 2 else "", src) for sl, ip, w, src in slot_ips],
                                               ["slot", "IP", "weight", "source"]))
    o.append(f"Average item power (game formula): **{game_avg:.0f}** · model IP (mean of weapon IP → damage and head/armor/shoes "
             f"IP → survivability): **{fight_ip:.0f}**")
    if not (slot_ip or weapon_ip or avg_ip or spec_ip):
        o.append("_No mastery given: pass avg_ip (character average from the game) and/or slot_ip / weapon_ip for exact numbers._")
    # kit
    o.append("\n### Kit\n" + table([(f, ", ".join(dict.fromkeys(v)) or "—") for f, v in flags.items()], ["capability", "from"]))
    warn = []
    if not flags["AoE"]:
        warn.append("no AoE: camps have 8–10 guards, clearing will be slow")
    if not flags["sustain"]:
        warn.append("no self-heal/lifesteal: you rely on resets between pulls")
    if not any("heal" in (e["row"]["id"] or "").lower() and e["row"]["slot"] == "potion" for e in entries) and \
            not any("POTION_HEAL" in e["id"] for e in entries):
        warn.append("no healing potion")
    if not flags["defensive"]:
        warn.append("no defensive/escape tool")
    for e in entries:
        if e["row"]["slot"] in ("potion", "food") or e["inventory"]:
            iid_name = e["id"].split("_", 1)[1]
            real = e["row"]["name_en"] or ""
            if any(w in iid_name for w in ("CLEANSE", "COOLDOWN", "SLOWFIELD")) and real:
                warn.append(f"`{e['id']}` is actually **{real}** (legacy item ID)")
    if warn:
        o.append("⚠ " + "; ".join(warn))

    # content
    o.append(f"\n### Content strength — chest behaviour `{behaviour}` (stages: " +
             ", ".join(f"{s['chest'].split('_')[-1]} weight {fmt(s['weight'])}" for s in prof[:3]) + ")")
    res = []
    for p in prof:
        if want is not None and p["stage"] not in want:
            continue
        need = required_ip(p)
        margin = fight_ip - need
        strongest = max(p["guards"], key=lambda g: g["hp"] * g["dps"]) if p["guards"] else None
        res.append((f"T{p['tier']}", ["small", "medium", "large"][p["stage"]] if p["stage"] < 3 else p["stage"], len(p["guards"]),
                    f"{sum(g['hp'] for g in p['guards']):,.0f}", f"{sum(g['dps'] for g in p['guards']):,.0f}",
                    f"{strongest['name']} ({strongest['hp']:,.0f} HP)" if strongest else "", f"{need:.0f}", f"{margin:+.0f}",
                    _verdict_capped(margin, armor_ip, p["tier"])))
    o.append(table(res, ["roads tier", "chest", "guards", "total HP", "total raw DPS", "strongest guard", "model IP needed", "margin", "verdict"]))
    o.append(f"_Guard composition from `{prof[0]['template'] if prof else ''}`; guards upgrade together with the chest. "
             "Roads tier: T4 from blue/yellow zones, T6 from red/black, T8 deep roads (Paths to Glory, 2024-07-22)._")

    # economics
    if price:
        items = [f"{e['stack']}x {e['id']}" if e["stack"] > 1 else e["id"] for e in entries]
        try:
            base = market.price_map([e["id"] for e in entries], server, city)  # normal quality (most liquid)
            by_q = {}
            for qual in sorted({e["quality"] for e in entries if e["quality"] > 1}):
                if not market.WARNINGS:
                    by_q[qual] = market.price_map([e["id"] for e in entries if e["quality"] == qual], server, city, qual)
            regear, unknown = 0.0, []
            for e in entries:
                p = (by_q.get(e["quality"], {}).get(e["id"], (None,))[0]) or base.get(e["id"], (None,))[0]
                regear += (p or 0) * e["stack"]
                if not p:
                    unknown.append(e["id"])
            o.append(f"\n### Risk\nRe-gear cost (Roads are full loot): **≈{money(regear)} silver** ({city}, {server}; each item at its quality, normal-quality price as fallback)" +
                     (f" — no price for {', '.join(f'`{u}`' for u in unknown)}" if unknown else "") +
                     (f"\n⚠ {'; '.join(market.WARNINGS)}" if market.WARNINGS else "") + f"\nDetails: build_cost {items}")
        except AOError as e:
            o.append(f"\n### Risk\nPrice lookup failed ({e}); run build_cost later.")
    o.append("\n_Model: base stage of a tier-T camp ≈ tuned for T.0 gear (IP 700 + 100·(T−4)); each larger chest stage needs extra IP "
             "= 100·ln(F_stage/F_base)/ln(1.192), F = HP×DPS of the hardest pull (boss slot or 3 strongest guards); "
             "+100 IP ≈ ×1.0918 damage (weapon) and ×1.0918 survivability (armor) (gamedata.json); model IP = mean of weapon and armor IP. Ignores player skill, spec, resistances, mechanics, "
             "and PvP risk — use it to compare options, not as a guarantee. Verdict capped at 🟠 when armor IP is >150 below the content "
             "tier's gear IP (burst risk)._")
    return "\n".join(o)


# ------------------------------------------------------------------ small groups (2-3 players)
# Role factors are model assumptions (documented in the output). Role detection uses itemroles.json (party context).
ROLE_FACTORS = {  # damage share, survivability when focused
    "Tank": (0.6, 1.6), "DPS": (1.0, 1.0), "Ranged_DPS": (1.0, 1.0), "Support": (0.6, 1.0), "Heal": (0.3, 1.0),
    "Hybrid_Heal": (0.8, 1.0),  # healing weapon with damage spells on Q/W: mostly damage, light group healing
}
HYBRID_HEAL_BONUS = 0.4
HEAL_BONUS = (0.8, 0.4)        # focused target survivability +80% from the 1st healer, +40% from the 2nd
SUPPORT_DMG = 0.15             # arcane-style support: +15% group damage each
SPREAD_BONUS = 0.25            # no tank: aggro can be swapped/kited, +25% per extra player


def detect_role(entries):
    rows = q("SELECT json FROM docs WHERE file='itemroles.json'")
    ratings = {}
    for r in rows:
        d = json.loads(r["json"])
        if d.get("@context") != "party":
            continue
        cats = d.get("category") or []
        ratings[d["@baserole"]] = {c["@value"]: float(c["@rating"]) for c in (cats if isinstance(cats, list) else [cats])}
    weapon = next((e["row"] for e in entries if e["row"]["slot"] == "mainhand" and not e["inventory"]), None)
    armor = next((e["row"] for e in entries if e["row"]["slot"] == "armor" and not e["inventory"]), None)
    score = {}
    for role, cats in ratings.items():
        if role == "BattleMount":
            continue
        score[role] = 2 * cats.get(weapon["sub1"] if weapon else "", 0) + cats.get(armor["sub1"] if armor else "", 0)
    role = max(score, key=score.get) if score and max(score.values()) > 0 else "DPS"
    if role == "Heal":  # damage-specced healer weapon (e.g. druid with damage Q/W) → hybrid
        dmg_spells = 0
        for e in entries:
            if e["row"]["slot"] != "mainhand":
                continue
            for sid in e["active"][:2]:
                sp = q1("SELECT category, desc_en FROM spells WHERE id=?", sid)
                if sp and sp["category"] != "heal" and re.search(r"damage", sp["desc_en"] or "", re.I):
                    dmg_spells += 1
        if dmg_spells >= 2:
            role = "Hybrid_Heal"
    return role, score


def _raw_loadout(lo):
    if isinstance(lo, dict):
        return lo
    s = lo.strip()
    if s.startswith("@"):
        with open(s[1:], encoding="utf-8") as fh:
            s = fh.read()
    return json.loads(s)


def chest_offline_values(behaviour, tier):
    """{chest name: expected value (game item value units)} for the stages of a chest behaviour."""
    ev, out = advisor.LootEV(), {}
    for r in q("SELECT name, json FROM chests WHERE name LIKE ?", behaviour + "%"):
        lists = advisor._chest_lists(json.loads(r["json"]), tier)
        if not lists:
            continue
        wsum = sum(w for _, w, _ in lists)
        out[r["name"]] = sum(w / wsum * sum(n * advisor._offline_value(i) for i, n in ev.expected(ln).items()) for _, w, ln in lists)
    return out


def _parse_ips(ips, n):
    """'avg=1250,mainhand=1300 | avg=1180' → [{'avg_ip':1250,'slot_ip':{...}}, ...]"""
    out = [{} for _ in range(n)]
    if not ips:
        return out
    chunks = ips if isinstance(ips, list) else str(ips).split("|")
    for i, chunk in enumerate(chunks[:n]):
        slots = {}
        for part in re.split(r"[,;\s]+", chunk.strip()):
            if "=" not in part:
                continue
            k, v = part.split("=", 1)
            if k.strip().lower() in ("avg", "average", "avg_ip", "средний"):
                out[i]["avg_ip"] = float(v)
            else:
                slots[k] = v
        if slots:
            out[i]["slot_ip"] = slots
    return out


def group_check(loadouts, content="avalon_veteran", ips=None, tiers=None, stages=None, server="europe", city="Caerleon", price=True):
    """Predict how a 2-3 player group performs in PvE camps: roles, combined power, per-tier/stage verdict, loot split, risk."""
    if isinstance(loadouts, str):
        loadouts = [loadouts]
    if not 2 <= len(loadouts) <= 5:
        raise AOError("Give 2-5 loadouts (one per player)")
    key = content if content in CONTENT else next((v for a, v in ALIASES.items() if a in (content or "").lower()), None)
    if not key:
        raise AOError(f"Unknown content {content!r}. Supported: {', '.join(CONTENT)}")
    behaviour, title, default_tiers = CONTENT[key]
    tiers = [int(t) for t in (tiers or default_tiers)]
    want = {STAGE_NAMES.get(str(x).lower(), x) for x in stages} if stages else None
    per_ip = _parse_ips(ips, len(loadouts))
    players = []
    for i, lo in enumerate(loadouts):
        name, entries = parse_loadout(lo)
        raw = _raw_loadout(lo)
        avg_ip = per_ip[i].get("avg_ip") or raw.get("avg_ip") or raw.get("avgIp")
        slot_ip = per_ip[i].get("slot_ip") or raw.get("slot_ip") or raw.get("slotIp")
        game_avg, rows = loadout_ip(entries, 0, None, slot_ip, avg_ip)
        weapon = next((r[1] for r in rows if r[0] == "mainhand"), game_avg)
        armor = [r[1] for r in rows if r[0] in ("head", "armor", "shoes")]
        armor = sum(armor) / len(armor) if armor else game_avg
        role, _ = detect_role(entries)
        flags, _ = kit(entries)
        players.append({"name": name, "entries": entries, "avg": game_avg, "weapon": weapon, "armor": armor, "role": role,
                        "flags": flags, "explicit": bool(avg_ip or slot_ip)})
    # combined power
    dmg = sum(ROLE_FACTORS.get(p["role"], (1, 1))[0] * 1.0918 ** ((p["weapon"] - 1000) / 100) for p in players)
    dmg *= 1 + SUPPORT_DMG * sum(1 for p in players if p["role"] == "Support")
    tanks = [p for p in players if p["role"] == "Tank"]
    focus = max(tanks or players, key=lambda p: p["armor"] * ROLE_FACTORS.get(p["role"], (1, 1))[1])
    surv = 1.0918 ** ((focus["armor"] - 1000) / 100) * ROLE_FACTORS.get(focus["role"], (1, 1))[1]
    healers = [p for p in players if p["role"] == "Heal"]
    surv *= 1 + sum(HEAL_BONUS[i] if i < len(HEAL_BONUS) else 0.2 for i in range(len(healers)))
    surv *= 1 + HYBRID_HEAL_BONUS * min(1, sum(1 for p in players if p["role"] == "Hybrid_Heal" and p is not focus))
    if not tanks:
        surv *= 1 + SPREAD_BONUS * (len(players) - 1)
    balance = dmg * surv
    group_ip = 1000 + 100 * math.log(balance) / PER100

    o = [f"## Group check ({len(players)} players) → {title}", ""]
    o.append(table([(i + 1, p["name"], p["role"].replace("_", " "), f"{p['avg']:.0f}" + ("" if p["explicit"] else " (no mastery given)"),
                     f"{p['weapon']:.0f}", f"{p['armor']:.0f}", label(next((e['id'] for e in p['entries'] if e['row']['slot'] == 'mainhand'), '')),
                     ", ".join(f for f, v in p["flags"].items() if v)) for i, p in enumerate(players)],
                   ["#", "loadout", "role", "avg IP", "weapon IP", "armor IP", "weapon", "kit"]))
    comp = []
    if not tanks:
        comp.append("no tank: mobs hit whoever has aggro — kite and swap aggro (modelled as +25% survivability per extra player)")
    if not healers and not any(p["role"] == "Hybrid_Heal" for p in players):
        comp.append("no healer: sustain only from lifesteal/self-heals and potions")
    elif not healers:
        comp.append("only a damage-specced healer: light group healing (modelled as +40% survivability for the focused ally)")
    if not any(p["flags"]["AoE"] for p in players):
        comp.append("no AoE in the group")
    cc = sum(len(p["flags"]["crowd control"]) for p in players)
    comp.append(f"crowd control sources: {cc}")
    o.append("\n**Composition:** " + "; ".join(comp))
    o.append(f"\n**Group power** ≈ one player at **{group_ip:.0f} IP** (damage ×{dmg:.2f}, focused target `{focus['name']}` "
             f"survivability ×{surv:.2f}, both relative to a 1000-IP solo DPS).")
    # content
    prof = content_profile(behaviour, tiers)
    intent = {"avalon_solo": (1, 1), "avalon_veteran": (2, 5), "avalon_elite": (5, 20)}[key]
    res = []
    for p in prof:
        if want is not None and p["stage"] not in want:
            continue
        need = required_ip(p)
        margin = group_ip - need
        strongest = max(p["guards"], key=lambda g: g["hp"] * g["dps"]) if p["guards"] else None
        res.append((f"T{p['tier']}", ["small", "medium", "large"][min(p["stage"], 2)], len(p["guards"]), f"{sum(g['hp'] for g in p['guards']):,.0f}",
                    f"{strongest['name']} ({strongest['hp']:,.0f} HP)" if strongest else "", f"{need:.0f}", f"{margin:+.0f}",
                    _verdict_capped(margin, focus["armor"], p["tier"])))
    o.append(f"\n### Content strength — `{behaviour}`\n" +
             table(res, ["roads tier", "chest", "guards", "total HP", "strongest guard", "model IP needed", "margin", "verdict"]))
    if not intent[0] <= len(players) <= intent[1]:
        o.append(f"⚠ This content is intended for {intent[0]}–{intent[1]} players; with {len(players)} the "
                 + ("loot is split between more people than needed" if len(players) > intent[1] else "camp is tuned for a bigger group"))
    # loot split + risk
    vals = [(t, n, v) for t in tiers for n, v in sorted(chest_offline_values(behaviour, t).items(), key=lambda x: x[1])]
    if vals:
        o.append("\n### Loot per player (chest model value ÷ players; game item value units — compare, don't read as silver)\n" +
                 table([(f"T{t}", n.replace(behaviour + "_", "").lower(), fmt(round(v)), fmt(round(v / len(players)))) for t, n, v in vals],
                       ["tier", "chest", "chest value", "per player"]))
    if price:
        total, lines = 0.0, []
        for p in players:
            prices = market.price_map([e["id"] for e in p["entries"]], server, city)
            if market.WARNINGS:
                lines.append(f"{p['name']}: price API unavailable ({'; '.join(market.WARNINGS)})")
                break
            v = sum((prices.get(e["id"], (None,))[0] or 0) * e["stack"] for e in p["entries"])
            total += v
            lines.append(f"{p['name']}: ≈{money(v)}")
        o.append("\n### Risk (full loot)\nRe-gear per player (normal-quality prices, " + city + "): " + "; ".join(lines) +
                 (f" — group total ≈ **{money(total)}**" if total else ""))
    o.append("\n_Group model: damage = Σ role share × 1.0918^((weapon IP−1000)/100) (DPS 1.0, support 0.6 +15% group dmg, tank 0.6, "
             "healer 0.3, damage-specced healer 0.8 + 40% heal on an ally); survivability of the focused target = 1.0918^((armor IP−1000)/100) × (tank 1.6) × (1 + 0.8 first healer "
             "+ 0.4 second) × (no tank: 1 + 0.25 per extra player). Group IP = 1000 + 100·ln(damage×survivability)/ln(1.192), "
             "compared with the camp model of gear_check. Verdict capped at 🟠 when the focused player's raw armor IP is >150 below the "
             "content tier's gear IP (burst risk). Role factors are assumptions; coordination, mechanics and PvP are not modelled._")
    return "\n".join(o)
