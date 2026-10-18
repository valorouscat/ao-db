"""Can this loadout (or a small group) farm that PvE content? Model built on the concrete monsters of the content.

Players
- Weapon IP → damage, head/armor/shoes IP → survivability; +100 IP = ×1.0918 each (gamedata.json ItemPowerProgression).
- Weapon factor: DPS potential of the chosen Q/W/E + auto-attacks vs a typical pull, from the real spell effects
  (combat.py), relative to the median best-damage kit of all weapons (=1.0). Missing spells are picked by intent
  (`intents`, e.g. "q=damage,w=damage"); healer weapons default to heal spells unless told otherwise.
- Damage type mix (physical/magic) from those spells is matched against each mob's armor / magic resistance.
- Roles (itemroles.json): damage share and survivability factors (tank, healer, damage-specced healer, support);
  groups get a coordination penalty (−7.5% damage per extra player).

Content (every template variant of the camp)
- Guards placed by the map templates; at each chest stage every spawn point uses its mob variant for that upgrade level.
- Each mob: HP, auto-attack DPS + ability DPS (abilities found via its prefab, alternatives counted once, capped), armor, mres;
  big telegraphed hits are listed as mechanics to dodge.
- Guards are clustered into pulls by position (single linkage, 10 m). F(pull) = Σ effective HP × Σ DPS; the hardest pull decides.
- Anchor: the median base-stage solo (green) camp of the tier is tuned for tier-T .0 gear (IP 700 + 100·(T−4)), neutral damage mix.
  Needed IP = par + 100·ln(F / F_anchor)/ln(1.192). The verdict uses the median template; best/worst variants are shown.
"""
import json, math, re, statistics
from collections import Counter
from . import core, advisor, market, combat
from .core import AOError, q, q1, label, money, fmt, table, resolve_item

PER100 = math.log(1.0918 * 1.0918)
COMBAT_SLOTS = ("mainhand", "offhand", "head", "armor", "shoes", "cape")
QUALITY_IP = {1: 0, 2: 20, 3: 40, 4: 60, 5: 100}
STAGE_NAMES = {"small": 0, "малый": 0, "base": 0, "medium": 1, "средний": 1, "champion": 1, "large": 2, "большой": 2, "boss": 2}
CONTENT = {
    "avalon_solo": ("AVALON_SMALL_SOLO", "Roads of Avalon solo camps (green)", [4, 6, 8], (1, 1)),
    "avalon_veteran": ("AVALON_MEDIUM_VETERAN", "Roads of Avalon veteran camps (blue)", [4, 6, 8], (2, 5)),
    "avalon_elite": ("AVALON_MEDIUM_ELITE", "Roads of Avalon elite camps (gold)", [6, 8], (5, 20)),
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
PULL_RADIUS = 10.0
COORDINATION = 0.075
BURST_GAP = 150
NEUTRAL_MIX = {"physical": 0.5, "magic": 0.5}


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


# ------------------------------------------------------------------ roles
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


# ------------------------------------------------------------------ spells by intent
SLOT_KEYS = {"q": "1", "w": "2", "e": "3", "1": "1", "2": "2", "3": "3"}


def parse_intents(text):
    """'q=damage,w=damage' / 'Q W на урон' → {'1': 'damage', '2': 'damage'}"""
    if not text:
        return {}
    if isinstance(text, dict):
        return {SLOT_KEYS.get(str(k).lower(), str(k)): v for k, v in text.items()}
    out = {}
    t = str(text).lower()
    for k, v in re.findall(r"([qwe123])\s*=\s*(\w+)", t):
        out[SLOT_KEYS[k]] = "heal" if v.startswith(("heal", "хил", "леч")) else "damage"
    if not out:  # free text: "q w на урон", "q w damage", "хил на e"
        want = "heal" if re.search(r"хил|леч|heal", t) and not re.search(r"урон|дамаг|damage|dps", t) else "damage"
        for k in re.findall(r"\b([qwe])\b", t):
            out[SLOT_KEYS[k]] = want
    return out


def apply_intents(entries, intents, role_hint=None):
    """Fill/override main-hand Q/W/E according to intents; heal weapons default to heal, others to damage."""
    for e in entries:
        if e["row"]["slot"] != "mainhand" or e["inventory"]:
            continue
        kit_ = combat.weapon_spells(e["row"]["base_id"])
        default = "heal" if e["row"]["sub1"] in ("holystaff", "naturestaff") and not intents else "damage"
        chosen = list(e["active"])
        auto = []
        for idx, slot in enumerate(("1", "2", "3")):
            want = intents.get(slot)
            have = chosen[idx] if idx < len(chosen) else None
            if have and not want:
                continue
            opts = kit_.get(slot) or []
            if not opts:
                continue
            pick = combat.pick_spells(e["id"], {slot: want or default})
            sid = next((p for p in pick if any(p == o[0] for o in opts)), None)
            if sid:
                if idx < len(chosen):
                    chosen[idx] = sid
                else:
                    chosen.append(sid)
                auto.append(slot)
        e["active"], e["auto_slots"] = chosen, auto
    return entries


# ------------------------------------------------------------------ content model
def _cluster(points, radius=PULL_RADIUS):
    """Single-linkage clusters of [(x, z, payload)] within radius."""
    n, parent = len(points), list(range(len(points)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i in range(n):
        for j in range(i + 1, n):
            if (points[i][0] - points[j][0]) ** 2 + (points[i][1] - points[j][1]) ** 2 <= radius * radius:
                parent[find(i)] = find(j)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(points[i][2])
    return list(groups.values())


def _variant(beh, level, solo):
    r = q1("SELECT mobs FROM spawnbehaviors WHERE name=?", beh)
    if not r:
        return None
    mobs = json.loads(r["mobs"])
    ok = [m for m in mobs if m["level"] <= level] or mobs[:1]
    top = max(m["level"] for m in ok)
    cands = [(m["mob"], combat.mob_combat(m["mob"], solo)) for m in ok if m["level"] == top]
    cands = [(mid, c) for mid, c in cands if c]
    if not cands:
        return None
    avg = lambda k: sum(c[k] for _, c in cands) / len(cands)
    name = q1("SELECT name_en FROM mobs WHERE id=?", cands[0][0])["name_en"] or cands[0][0]
    return {"name": name if len(cands) == 1 else f"{name} (+{len(cands) - 1} variants)", "hp": avg("hp"), "dps": avg("dps"),
            "armor": avg("armor"), "mres": avg("mres"), "boss": "BOSS" in beh,
            "heavy": sorted({h[0] for _, c in cands for h in c["heavy"]})}


def eval_layer(layer, tier, level, mix, solo):
    guards = json.loads(layer["guards"] or "[]")
    tier_ok = lambda b: re.match(rf"T{tier}_", b) or re.search(rf"_T{tier}$", b)
    pts = []
    for beh, x, z in guards:
        if beh.startswith("ROAMING") or not tier_ok(beh):
            continue
        v = _variant(beh, level, solo)
        if v:
            pts.append((x, z, v))
    if not pts:
        return None
    pulls = _cluster(pts)
    best = None
    for pull in pulls:
        hp_eff = sum(g["hp"] / (mix.get("physical", 0) * combat.mitigation(g["armor"]) * 3.34 +
                                mix.get("magic", 0) * combat.mitigation(g["mres"]) * 3.34 or 1) for g in pull)
        dps = sum(g["dps"] for g in pull)
        f = hp_eff * dps
        if not best or f > best["F"]:
            best = {"F": f, "pull": pull, "hp": sum(g["hp"] for g in pull), "dps": dps}
    best.update(guards=len(pts), total_hp=sum(p[2]["hp"] for p in pts), pulls=len(pulls),
                heavy=sorted({h for p in pts for h in p[2]["heavy"]}), template=f"{layer['template']} › {layer['layer'].strip()}")
    return best


def content_eval(behaviour, tier, mix, solo):
    """Per chest stage: evaluation of every template variant of the camp at this tier."""
    up = q1("SELECT stages FROM chest_upgrades WHERE name=?", behaviour)
    if not up:
        raise AOError(f"No chest-upgrade data for {behaviour}")
    stages = sorted(json.loads(up["stages"]), key=lambda s: s["level"])
    layers = [c for c in q("SELECT * FROM camps WHERE chest_behaviour=?", behaviour) if re.search(rf"T{tier}(?!\d)", c["layer"])]
    out = []
    for i, st in enumerate(stages):
        evals = [e for e in (eval_layer(l, tier, st["level"], mix, solo) for l in layers) if e]
        if evals:
            out.append({"stage": i, "chest": st["chest"], "level": st["level"], "weight": st["weight"], "evals": evals})
    return out


_anchor = {}


def anchor_F(tier):
    if tier not in _anchor:
        ev = content_eval("AVALON_SMALL_SOLO", tier, NEUTRAL_MIX, True)
        base = next((s for s in ev if s["stage"] == 0), None)
        _anchor[tier] = statistics.median(e["F"] for e in base["evals"]) if base else None
    return _anchor[tier]


def needed_ip(F, tier):
    ref = anchor_F(tier)
    return 700 + 100 * (tier - 4) + (100 * math.log(F / ref) / PER100 if ref and F else 0)


def _verdict(margin):
    if margin >= 0:
        return "✅ comfortable"
    if margin >= -200:
        return "🟡 doable with good play"
    if margin >= -400:
        return "🟠 hard, high risk"
    return "❌ not recommended"


def _verdict_capped(margin, armor_ip, tier):
    gap = 700 + 100 * (tier - 4) - armor_ip
    if gap > BURST_GAP and margin >= -200:
        return f"🟠 burst risk: armor {gap:.0f} IP below tier"
    return _verdict(margin)


# ------------------------------------------------------------------ players
def build_player(lo, ip_spec=None, intents=None):
    name, entries = parse_loadout(lo)
    raw = _raw_loadout(lo)
    ip_spec = ip_spec or {}
    intents_d = parse_intents(intents or raw.get("intents"))
    apply_intents(entries, intents_d)
    avg_ip = ip_spec.get("avg_ip") or raw.get("avg_ip") or raw.get("avgIp")
    slot_ip = ip_spec.get("slot_ip") or raw.get("slot_ip") or raw.get("slotIp")
    game_avg, rows = loadout_ip(entries, ip_spec.get("spec_ip", 0), ip_spec.get("weapon_ip"), slot_ip, avg_ip)
    weapon_e = next((e for e in entries if e["row"]["slot"] == "mainhand" and not e["inventory"]), None)
    weapon_ip = next((r[1] for r in rows if r[0] == "mainhand"), game_avg)
    arm = [r[1] for r in rows if r[0] in ("head", "armor", "shoes")]
    armor_ip = sum(arm) / len(arm) if arm else game_avg
    role, _ = detect_role(entries)
    flags, _ = kit(entries)
    wf, mix, parts = (combat.weapon_factor(weapon_e["id"], weapon_e["active"]) if weapon_e else (1.0, NEUTRAL_MIX, []))
    return {"name": name, "entries": entries, "rows": rows, "avg": game_avg, "weapon": weapon_ip, "armor": armor_ip, "role": role,
            "flags": flags, "wf": wf, "mix": mix, "parts": parts, "weapon_e": weapon_e, "explicit": bool(avg_ip or slot_ip or ip_spec)}


def group_power(players):
    dmg = sum(ROLE_FACTORS.get(p["role"], (1, 1))[0] * p["wf"] * 1.0918 ** ((p["weapon"] - 1000) / 100) for p in players)
    dmg *= 1 + SUPPORT_DMG * sum(1 for p in players if p["role"] == "Support")
    dmg *= 1 - COORDINATION * (len(players) - 1)
    tanks = [p for p in players if p["role"] == "Tank"]
    focus = max(tanks or players, key=lambda p: p["armor"] * ROLE_FACTORS.get(p["role"], (1, 1))[1])
    surv = 1.0918 ** ((focus["armor"] - 1000) / 100) * ROLE_FACTORS.get(focus["role"], (1, 1))[1]
    healers = [p for p in players if p["role"] == "Heal"]
    surv *= 1 + sum(HEAL_BONUS[i] if i < len(HEAL_BONUS) else 0.2 for i in range(len(healers)))
    surv *= 1 + HYBRID_HEAL_BONUS * min(1, sum(1 for p in players if p["role"] == "Hybrid_Heal" and p is not focus))
    if not tanks and len(players) > 1:
        surv *= 1 + SPREAD_BONUS * (len(players) - 1)
    weights = [ROLE_FACTORS.get(p["role"], (1, 1))[0] * p["wf"] for p in players]
    tot = sum(weights) or 1
    mix = {}
    for p, w in zip(players, weights):
        for k, v in p["mix"].items():
            mix[k] = mix.get(k, 0) + v * w / tot
    return {"dmg": dmg, "surv": surv, "focus": focus, "ip": 1000 + 100 * math.log(dmg * surv) / PER100, "mix": mix,
            "tanks": tanks, "healers": healers}


def _content_section(o, behaviour, tiers, want, gp, solo):
    res, heavy, details = [], set(), []
    for t in tiers:
        for st in content_eval(behaviour, t, gp["mix"], solo):
            if want is not None and st["stage"] not in want:
                continue
            needs = sorted(needed_ip(e["F"], t) for e in st["evals"])
            med = statistics.median(needs)
            worst = max(st["evals"], key=lambda e: e["F"])
            margin = gp["ip"] - med
            heavy.update(worst["heavy"])
            pull = Counter(g["name"] for g in worst["pull"])
            details.append((f"T{t}", ["small", "medium", "large"][min(st["stage"], 2)],
                            ", ".join(f"{n}× {m}" for m, n in pull.most_common(4)), f"{worst['hp']:,.0f}", f"{worst['dps']:,.0f}"))
            res.append((f"T{t}", ["small", "medium", "large"][min(st["stage"], 2)], len(st["evals"]),
                        f"{worst['guards']}", f"{needs[0]:.0f}–{needs[-1]:.0f}", f"{med:.0f}", f"{margin:+.0f}",
                        _verdict_capped(margin, gp["focus"]["armor"], t)))
    o.append(f"\n### Content strength — `{behaviour}` (concrete guards, all template variants)\n" +
             table(res, ["tier", "chest", "variants", "guards", "IP needed (best–worst)", "median", "margin", "verdict"]))
    o.append("\n**Hardest pull (worst variant)**\n" + table(details, ["tier", "chest", "mobs in the pull", "pull HP", "pull DPS"]))
    if heavy:
        o.append("**Telegraphed heavy hits to dodge:** " + ", ".join(f"`{h}`" for h in sorted(heavy)[:12]) + (" …" if len(heavy) > 12 else ""))


def _player_table(players):
    rows = []
    for i, p in enumerate(players):
        w = p["weapon_e"]
        sp = []
        if w:
            for idx, sid in enumerate(w["active"]):
                nm = q1("SELECT name_en FROM spells WHERE id=?", sid)
                star = "*" if str(idx + 1) in (w.get("auto_slots") or []) else ""
                sp.append(f"{'QWE'[idx] if idx < 3 else '?'}: {nm['name_en'] if nm else sid}{star}")
        rows.append((i + 1, p["name"], p["role"].replace("_", " "), f"{p['avg']:.0f}", f"{p['weapon']:.0f}", f"{p['armor']:.0f}",
                     label(w["id"]) if w else "", "; ".join(sp), f"{p['wf']:.2f}",
                     " / ".join(f"{k} {v:.0%}" for k, v in sorted(p["mix"].items(), key=lambda kv: -kv[1]) if v >= 0.05)))
    return table(rows, ["#", "loadout", "role", "avg IP", "weapon IP", "armor IP", "weapon", "Q/W/E (*auto-picked)", "weapon factor", "damage type"])


MODEL_NOTE = ("_Model: weapon factor = DPS potential of the chosen spells + auto-attacks vs a 3-mob pull (spells.json effects) ÷ median "
              "best kit of all weapons; damage = Σ role share × weapon factor × 1.0918^((weapon IP−1000)/100) × (1 − 7.5% per extra player); "
              "survivability = 1.0918^((armor IP−1000)/100) × role/healer/aggro factors. Content: concrete guards of every template "
              "variant, clustered into pulls (10 m); F = Σ HP/mitigation × Σ (auto + ability) DPS of the hardest pull; mitigation "
              "100/(100+res) (assumed). Anchor: median base-stage green camp of the tier ↔ tier .0 gear. Verdict capped at 🟠 when armor "
              "IP is >150 below the tier. Role factors and formulas are assumptions — compare options, don't treat as guarantees._")


# ------------------------------------------------------------------ tools
def gear_check(loadout, content="avalon_solo", tiers=None, stages=None, spec_ip=0, weapon_ip=None, slot_ip=None, avg_ip=None,
               intents=None, server="europe", city="Caerleon", price=True):
    key = content if content in CONTENT else next((v for a, v in ALIASES.items() if a in (content or "").lower()), None)
    if not key:
        raise AOError(f"Unknown content {content!r}. Supported: {', '.join(CONTENT)} (aliases: green/blue/gold).")
    behaviour, title, default_tiers, _ = CONTENT[key]
    tiers = [int(t) for t in (tiers or default_tiers)]
    want = {STAGE_NAMES.get(str(s).lower(), s) for s in stages} if stages else None
    p = build_player(loadout, {"spec_ip": spec_ip, "weapon_ip": weapon_ip, "slot_ip": slot_ip, "avg_ip": avg_ip}, intents)
    gp = group_power([p])
    o = [f"## Gear check: “{p['name']}” → {title}", "", _player_table([p])]
    rows = []
    for e in p["entries"]:
        it = e["row"]
        if e["row"]["slot"] in COMBAT_SLOTS and not e["inventory"]:
            continue
        rows.append((it["slot"] or it["kind"], label(e["id"]), (" ×" + str(e["stack"])) if e["stack"] > 1 else "", "bag" if e["inventory"] else ""))
    if rows:
        o.append("\n" + table(rows, ["slot", "item", "stack", ""]))
    o.append("\n### Item power used\n" + table([(sl, f"{ip:.0f}", "×2 (two-handed)" if w == 2 else "", src) for sl, ip, w, src in p["rows"]],
                                               ["slot", "IP", "weight", "source"]))
    o.append(f"Average item power (game formula): **{p['avg']:.0f}** · effective model IP (weapon IP adjusted by weapon factor, armor IP, "
             f"role): **{gp['ip']:.0f}**")
    o.append("\n### Kit\n" + table([(f, ", ".join(dict.fromkeys(v)) or "—") for f, v in p["flags"].items()], ["capability", "from"]))
    warn = []
    if not p["flags"]["AoE"]:
        warn.append("no AoE: camps have 8–10 guards")
    if not any("POTION_HEAL" in e["id"] for e in p["entries"]):
        warn.append("no healing potion")
    for e in p["entries"]:
        if (e["row"]["slot"] in ("potion", "food") or e["inventory"]) and any(w in e["id"] for w in ("CLEANSE", "COOLDOWN", "SLOWFIELD")):
            warn.append(f"`{e['id']}` is actually **{e['row']['name_en']}** (legacy item ID)")
    if warn:
        o.append("⚠ " + "; ".join(warn))
    _content_section(o, behaviour, tiers, want, gp, solo=True)
    if price:
        _risk(o, [p], server, city)
    o.append("\n" + MODEL_NOTE)
    return "\n".join(o)


def _risk(o, players, server, city):
    total, lines = 0.0, []
    for p in players:
        base = market.price_map([e["id"] for e in p["entries"]], server, city)
        if market.WARNINGS:
            lines.append(f"price API unavailable ({'; '.join(market.WARNINGS)})")
            break
        by_q = {}
        for qual in sorted({e["quality"] for e in p["entries"] if e["quality"] > 1}):
            if not market.WARNINGS:
                by_q[qual] = market.price_map([e["id"] for e in p["entries"] if e["quality"] == qual], server, city, qual)
        v = sum(((by_q.get(e["quality"], {}).get(e["id"], (None,))[0]) or base.get(e["id"], (None,))[0] or 0) * e["stack"] for e in p["entries"])
        total += v
        lines.append(f"{p['name']}: ≈{money(v)}")
    o.append(f"\n### Risk (full loot)\nRe-gear ({city}, {server}; each item at its quality): " + "; ".join(lines) +
             (f" — total ≈ **{money(total)}**" if total and len(players) > 1 else ""))


def group_check(loadouts, content="avalon_veteran", ips=None, intents=None, tiers=None, stages=None, server="europe", city="Caerleon",
                price=True):
    """Predict how a 2-3 player group performs in PvE camps (concrete guards of the content, kit-based weapon factors)."""
    if isinstance(loadouts, str):
        loadouts = [loadouts]
    if not 1 <= len(loadouts) <= 5:
        raise AOError("Give 1-5 loadouts (one per player)")
    key = content if content in CONTENT else next((v for a, v in ALIASES.items() if a in (content or "").lower()), None)
    if not key:
        raise AOError(f"Unknown content {content!r}. Supported: {', '.join(CONTENT)}")
    behaviour, title, default_tiers, intent_size = CONTENT[key]
    tiers = [int(t) for t in (tiers or default_tiers)]
    want = {STAGE_NAMES.get(str(x).lower(), x) for x in stages} if stages else None
    per_ip = _parse_ips(ips, len(loadouts))
    per_int = (intents if isinstance(intents, list) else str(intents).split("|")) if intents else []
    players = [build_player(lo, per_ip[i], per_int[i] if i < len(per_int) else None) for i, lo in enumerate(loadouts)]
    gp = group_power(players)
    o = [f"## Group check ({len(players)} players) → {title}", "", _player_table(players)]
    comp = []
    if not gp["tanks"] and len(players) > 1:
        comp.append("no tank: aggro swapping/kiting (+25% survivability per extra player)")
    if not gp["healers"]:
        comp.append("damage-specced healer only: light healing (+40% for the focused ally)" if any(p["role"] == "Hybrid_Heal" for p in players)
                    else "no healer: sustain only from lifesteal/self-heals and potions")
    if not any(p["flags"]["AoE"] for p in players):
        comp.append("no AoE")
    comp.append(f"crowd control sources: {sum(len(p['flags']['crowd control']) for p in players)}")
    o.append("\n**Composition:** " + "; ".join(comp))
    o.append(f"\n**Group power** ≈ one player at **{gp['ip']:.0f} IP** (damage ×{gp['dmg']:.2f} incl. coordination "
             f"−{COORDINATION * (len(players) - 1):.0%}, focused target `{gp['focus']['name']}` survivability ×{gp['surv']:.2f}; "
             f"group damage type " + " / ".join(f"{k} {v:.0%}" for k, v in gp["mix"].items() if v >= 0.05) + ")")
    _content_section(o, behaviour, tiers, want, gp, solo=len(players) == 1)
    if not intent_size[0] <= len(players) <= intent_size[1]:
        o.append(f"⚠ Content intended for {intent_size[0]}–{intent_size[1]} players; with {len(players)} the "
                 + ("loot is split between more people" if len(players) > intent_size[1] else "camp is tuned for a bigger group"))
    vals = [(t, n, v) for t in tiers for n, v in sorted(chest_offline_values(behaviour, t).items(), key=lambda x: x[1])]
    if vals:
        o.append("\n### Loot per player (chest model value ÷ players; game item value units — compare, don't read as silver)\n" +
                 table([(f"T{t}", n.replace(behaviour + "_", "").lower(), fmt(round(v)), fmt(round(v / len(players)))) for t, n, v in vals],
                       ["tier", "chest", "chest value", "per player"]))
    if price:
        _risk(o, players, server, city)
    o.append("\n" + MODEL_NOTE)
    return "\n".join(o)
