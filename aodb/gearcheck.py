"""Can this loadout farm that PvE content? Loadout analysis + camp strength model from the game files.

Model (transparent, documented in the output):
- Player power: weapon IP (damage) and head/armor/shoes IP (survivability), incl. quality bonus, mastery (weapon_ip) and
  optional spec IP; the fight model uses their mean. The game's average IP (6 slots, 2H counted twice) is shown too.
- Per +100 IP the game scales weapon damage ×1.0918 and survivability ×≈1.0918 (HP ×1.06 · armor ×1.03), so a fight's
  balance (enemy HP × enemy DPS vs player DPS × player EHP) shifts by ×1.192 per 100 IP (gamedata.json ItemPowerProgression).
- Content strength: guards of the camp at each chest stage (templates + randomspawnbehaviors + mobs). The base stage of a
  camp of tier T is assumed to be tuned for tier-T .0 gear; higher stages need extra IP = 100·ln(F_stage/F_base)/ln(1.192),
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
    "avalon_elite": ("AVALON_SMALL_ELITE", "Roads of Avalon elite camps (gold)", [4, 6, 8]),
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
                        "active": e.get("activeSpells") or [], "passive": e.get("passiveSpells") or [], "inventory": bool(e.get("_inventory"))})
    if not entries:
        raise AOError("Loadout has no equipment")
    return loadout.get("name") or "loadout", entries


def loadout_ip(entries, spec_ip=0, weapon_ip=None):
    """Average IP of combat slots; weapon_ip = in-game weapon IP incl. mastery (replaces the computed main-hand value)."""
    total, n, rows = 0.0, 0, []
    for e in entries:
        it, slot = e["row"], e["row"]["slot"]
        if e["inventory"] or slot not in COMBAT_SLOTS or not it["itempower"]:
            continue
        ip = it["itempower"] + QUALITY_IP.get(e["quality"], 0)
        if slot == "mainhand" and weapon_ip:
            ip = weapon_ip
        w = 2 if slot == "mainhand" and core.item_json(e["id"]).get("@twohanded") == "true" else 1
        total += ip * w
        n += w
        rows.append((slot, ip, w))
    if not n:
        raise AOError("No combat items (weapon/armor/cape) in the loadout")
    return total / n + spec_ip, rows


def model_ip(rows, spec_ip=0):
    """IP the fight model uses: damage scales with the weapon (main/off hand), survivability with head/armor/shoes,
    so the balance point is the mean of the two (both progress ×1.0918 per 100 IP in gamedata.json)."""
    off = [ip for slot, ip, _ in rows if slot in ("mainhand", "offhand")]
    deff = [ip for slot, ip, _ in rows if slot in ("head", "armor", "shoes")]
    if not off or not deff:
        return None
    return (sum(off) / len(off) + sum(deff) / len(deff)) / 2 + spec_ip


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
        spawns = {k: v for k, v in spawns.items() if re.match(rf"T{t}_", k) or k.startswith("ROAMING")}
        for i, st in enumerate(stages):
            guards = camp_at_stage(spawns, st["level"])
            f, _ = _hardest_pull(guards)
            out.append({"tier": t, "stage": i, "chest": st["chest"], "level": st["level"], "weight": st["weight"], "guards": guards,
                        "F": f, "template": f"{layer['template']} › {layer['layer']}"})
    return out


def _verdict(margin):
    if margin >= 0:
        return "✅ comfortable"
    if margin >= -200:
        return "🟡 doable with good play / spec"
    if margin >= -400:
        return "🟠 hard, high risk"
    return "❌ not recommended"


# ------------------------------------------------------------------ tool
def gear_check(loadout, content="avalon_solo", tiers=None, stages=None, spec_ip=0, weapon_ip=None, server="europe", city="Caerleon", price=True):
    name, entries = parse_loadout(loadout)
    key = content if content in CONTENT else next((v for a, v in ALIASES.items() if a in (content or "").lower()), None)
    if not key:
        raise AOError(f"Unknown content {content!r}. Supported: {', '.join(CONTENT)} (aliases: green/blue/gold).")
    behaviour, title, default_tiers = CONTENT[key]
    tiers = [int(t) for t in (tiers or default_tiers)]
    want = None
    if stages:
        want = {STAGE_NAMES.get(str(s).lower(), s) for s in stages}
    avg_ip, slot_ips = loadout_ip(entries, spec_ip, weapon_ip)
    fight_ip = model_ip(slot_ips, spec_ip) or avg_ip
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
    o.append(f"\n**Average item power: {avg_ip - spec_ip:.0f}**" + (f" (weapon at {weapon_ip} incl. mastery)" if weapon_ip else "") +
             (f" + spec {spec_ip} = **{avg_ip:.0f}**" if spec_ip else
              "" if weapon_ip else " (without mastery/spec: pass weapon_ip from the game, or spec_ip, e.g. 100–300)") +
             f"\nModel IP (mean of weapon IP → damage and head/armor/shoes IP → survivability): **{fight_ip:.0f}**")
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
    base = {p["tier"]: p["F"] for p in prof if p["stage"] == 0}
    res = []
    for p in prof:
        if want is not None and p["stage"] not in want:
            continue
        par = 700 + 100 * (p["tier"] - 4)
        extra = 100 * math.log(p["F"] / base[p["tier"]]) / PER100 if base.get(p["tier"]) and p["F"] else 0
        need = par + extra
        margin = fight_ip - need
        strongest = max(p["guards"], key=lambda g: g["hp"] * g["dps"]) if p["guards"] else None
        res.append((f"T{p['tier']}", ["small", "medium", "large"][p["stage"]] if p["stage"] < 3 else p["stage"], len(p["guards"]),
                    f"{sum(g['hp'] for g in p['guards']):,.0f}", f"{sum(g['dps'] for g in p['guards']):,.0f}",
                    f"{strongest['name']} ({strongest['hp']:,.0f} HP)" if strongest else "", f"{need:.0f}", f"{margin:+.0f}", _verdict(margin)))
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
             "and PvP risk — use it to compare options, not as a guarantee._")
    return "\n".join(o)
