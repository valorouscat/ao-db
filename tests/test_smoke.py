"""Smoke tests against a built ao.db. Run: python3 -m unittest discover tests  (AO_NET=1 also hits the market API)."""
import json, os, re, unittest
import tempfile
from unittest import mock
from aodb import advisor, core, encounter, gearcheck, market, mcp_server, optimizer, patchnotes, pvp
from aodb.tools import TOOLS, call


class Core(unittest.TestCase):
    def test_resolve(self):
        self.assertEqual(core.resolve_item("T4_MAIN_SWORD@2"), "T4_MAIN_SWORD@2")
        self.assertEqual(core.resolve_item("6.1 палаш"), "T6_MAIN_SWORD@1")
        self.assertEqual(core.resolve_item("Adept's Bag"), "T4_BAG")
        self.assertTrue(core.resolve_item("T6 bar").endswith("METALBAR"))
        with self.assertRaises(core.AOError):
            core.resolve_item("zzzqqqxx")

    def test_item_card(self):
        t = core.item("T4_MAIN_SWORD")
        for s in ("Broadsword", "### Recipe 1", "T4_METALBAR", "HEROICSTRIKE2", "### Stats"):
            self.assertIn(s, t)

    def test_spells_follow_reference(self):
        self.assertIn("HEROICSTRIKE2", core.item("T8_MAIN_SWORD"))

    def test_recipe_tree(self):
        t = core.recipe("T8_2H_CLAYMORE_AVALON@3", qty=2, return_rate=15.2)
        self.assertIn("Total base materials", t)
        self.assertIn("T8_ARTEFACT_2H_CLAYMORE_AVALON", t)

    def test_variants(self):
        self.assertIn("T8_MAIN_SWORD@4", core.variants("T4_MAIN_SWORD"))

    def test_spell_placeholders(self):
        t = core.spell("HEROICSTRIKE2")
        self.assertNotIn("{0}", t)
        self.assertIn("Heroic", t)

    def test_misc(self):
        self.assertIn("Martlock", core.zone("Martlock"))
        self.assertIn("Adept", core.loc(key="@ITEMS_T4_BAG"))
        self.assertIn("FAME_BOOKS", core.drops("T4_SKILLBOOK_STANDARD"))
        self.assertIn("Items", core.search("broadsword"))
        self.assertIn("hellgate", core.doc("hellgate", keys_only=True))
        self.assertIn("KEEPER", core.mob("T8_MOB_KEEPER_UNPROVEN_MALE"))
        with self.assertRaises(core.AOError):
            core.sql("DELETE FROM items")

    def test_item_value(self):
        self.assertEqual(core.item_value("T4_METALBAR"), 16)
        self.assertEqual(core.item_value("T4_MAIN_SWORD"), 16 * 16 + 8 * 16)


class Advisor(unittest.TestCase):
    def test_chest_value_offline(self):
        t = advisor.chest_value("avaroadloot", tier=8)
        self.assertIn("AVALON_SMALL_SOLO_BASE", t)
        self.assertIn("value index", t)

    def test_build_cost_with_fake_prices(self):
        fake = lambda ids, *a, **k: {i: (1000.0, "test") for i in ids}
        with mock.patch.object(market, "price_map", fake):
            t = advisor.build_cost(["T8_2H_BOW", "T8_HEAD_LEATHER_SET1", "10x T8_MEAL_STEW"])
        self.assertIn("Estimated total: 12,000", t)
        self.assertIn("other enchantments", t)

    def test_difficulty(self):
        t = advisor.difficulty("соло подземелья")
        self.assertIn("1.43", t)            # .1 loot factor
        self.assertIn("HP +84%", t)         # .4 mob buff
        z = advisor.difficulty("black zone")
        self.assertIn("black6", z)
        self.assertIn("dmg +25%", z)
        self.assertIn("1100", advisor.difficulty("corrupted"))  # Slayer base IP (Abyssal Depths)
        self.assertIn("transactiontax", advisor.difficulty("market"))
        self.assertIn("Content keys", advisor.difficulty())

    def test_mechanics_and_notes(self):
        self.assertIn("Infamy", advisor.mechanics("corrupted"))
        with tempfile.TemporaryDirectory() as d, mock.patch.object(advisor, "KNOWLEDGE", d):
            with self.assertRaises(core.AOError):
                advisor.save_note("x", "y", [])
            advisor.save_note("Avalon chest test", "Green chests are cheap", ["test://source"], ["avalon"])
            self.assertIn("Green chests", advisor.notes("avalon chest"))


LOADOUT = {"name": "bow", "equipment": [
    {"item": "T6_2H_BOW_KEEPER@1", "quality": 3, "activeSpells": ["MULTISHOT2", "BURNINGARROWS", "LIGHTNING_ARROW"], "passiveSpells": ["PASSIVE_ENERGYCHANCE_BOW"]},
    {"item": "T6_HEAD_LEATHER_SET2@1", "quality": 3, "activeSpells": ["ENERGY_BARRIER"]},
    {"item": "T6_ARMOR_LEATHER_SET1@1", "quality": 3, "activeSpells": ["BLOODLUST"]},
    {"item": "T6_SHOES_LEATHER_SET1@1", "quality": 3, "activeSpells": ["SPRINT_CD_REDUCTION"]},
    {"item": "T4_CAPEITEM_FW_THETFORD@2", "quality": 3}, {"item": "T8_POTION_CLEANSE"}, {"item": "T7_MEAL_ROAST", "stack": 3}]}


class GearCheck(unittest.TestCase):
    def test_ip_and_kit(self):
        _, entries = gearcheck.parse_loadout(json.dumps(LOADOUT))
        ip, _ = gearcheck.loadout_ip(entries)
        self.assertAlmostEqual(ip, (1115 * 2 + 1040 * 3 + 940) / 6, places=3)  # 2H counts twice, quality +40
        flags, _ = gearcheck.kit(entries)
        self.assertTrue(flags["AoE"] and flags["sustain"] and flags["defensive"])

    def test_slot_ip_and_avg_distribution(self):
        _, entries = gearcheck.parse_loadout(json.dumps(LOADOUT))
        avg, rows = gearcheck.loadout_ip(entries, weapon_ip=1300, avg_ip=1250)
        self.assertAlmostEqual(avg, 1250, places=6)
        ips = {r[0]: r[1] for r in rows}
        self.assertEqual(ips["mainhand"], 1300)
        self.assertAlmostEqual(ips["head"], 1250, places=6)    # 1040 + 210
        self.assertAlmostEqual(ips["cape"], 1150, places=6)    # 940 + 210
        self.assertAlmostEqual(gearcheck.model_ip(rows), 1275, places=6)
        _, rows = gearcheck.loadout_ip(entries, slot_ip="weapon=1300,шлем=1200")
        self.assertEqual({r[0]: r[1] for r in rows}["head"], 1200)

    def test_camp_model(self):
        ev = gearcheck.content_eval("AVALON_SMALL_SOLO", 6, gearcheck.NEUTRAL_MIX, True)
        self.assertEqual([st["stage"] for st in ev], [0, 1, 2])
        med = lambda st: sorted(e["F"] for e in st["evals"])[len(st["evals"]) // 2]
        self.assertLess(med(ev[0]), med(ev[2]))                       # guards upgrade with the chest
        self.assertTrue(all(5 <= e["guards"] <= 20 for e in ev[0]["evals"]))  # one camp per chest, not the whole template
        self.assertAlmostEqual(gearcheck.needed_ip(gearcheck.anchor_F(6), 6), gearcheck.par_ip(6), places=6)
        self.assertLess(gearcheck.par_ip(4), gearcheck.par_ip(6))
        t = gearcheck.gear_check(json.dumps(LOADOUT), "green", tiers=["6"], price=False, calibrate=False)
        self.assertIn("Invisibility Potion", t)
        self.assertIn("Hardest pull", t)

    def test_spell_damage_engine(self):
        from aodb import combat
        self.assertEqual(combat.spell_profile("MULTISHOT2")["dmg"], 116)          # vs mobs, not the PvP value 94
        self.assertAlmostEqual(combat.spell_profile("LIGHTNING_ARROW")["dmg"], 504, delta=1)  # 24 ticks × 21 (patch 2026-03)
        self.assertTrue(combat.spell_profile("THORNSAREA")["aoe"])
        self.assertIn("LIGHTNING_ARROW", [x[0] for x in combat.weapon_spells("T6_2H_BOW_KEEPER")["3"]])  # artifact's own E

    def test_dodge_and_defenses(self):
        t = gearcheck.gear_check(json.dumps(LOADOUT), "green", tiers=["6"], price=False, calibrate=False)
        self.assertIn("@90% dodge", t)
        self.assertIn("@50% dodge", t)
        self.assertIn("caught heavy hit", t)
        row = next(l for l in t.splitlines() if l.startswith("| T6 | large | "))
        cells = [c.strip() for c in row.split("|")]
        self.assertGreaterEqual(float(cells[5]), float(cells[7]))  # less dodging never helps
        from aodb import combat
        self.assertGreater(combat.spell_defense("ENERGY_BARRIER")["shield_ps"], 0)
        self.assertGreater(combat.spell_defense("CIRCLEOFLIFE")["heal_ally_ps"], 0)
        self.assertGreater(combat.spell_defense("FOOD_BUFF_LIFESTEAL_P5")["lifesteal"], 0)

    def test_player_stats_from_items(self):
        _, e = gearcheck.parse_loadout(json.dumps(LOADOUT))
        _, rows = gearcheck.loadout_ip(e)
        st = gearcheck.player_stats(e, rows)
        self.assertGreater(st["hp"], 1200)                       # base 1200 + gear
        self.assertGreater(st["physicalarmor"], 108)             # mercenary jacket 108 at 700 IP, scaled up
        self.assertEqual(gearcheck.player_stats(e, rows, 2500)["hp"], 2500)  # in-game value overrides

    def test_consumable_damage_and_calibration(self):
        lo = json.loads(json.dumps(LOADOUT))
        base = gearcheck.build_player(json.dumps(lo))["wf"]
        lo.setdefault("inventory", []).append({"item": "T6_POTION_COOLDOWN", "quality": 1, "stack": 2})  # Poison Potion
        self.assertGreater(gearcheck.build_player(json.dumps(lo))["wf"], base)
        t = gearcheck.record_outcome(json.dumps(LOADOUT), "green", 6, "large", "легко", save=False)  # dry run, journal untouched
        self.assertIn("model raw margin", t)
        self.assertIn("easy", t)
        with self.assertRaises(gearcheck.AOError):
            gearcheck.record_outcome(json.dumps(LOADOUT), "green", 6, "large", "meh", save=False)

    def test_mists_calibration_group(self):
        import pathlib, shutil
        d = pathlib.Path(tempfile.mkdtemp()) / "calibration.json"
        shutil.copy(gearcheck.CALIBRATION_FILE, d)
        with mock.patch.object(gearcheck, "CALIBRATION_FILE", d):
            encounter._cal.clear()
            self.assertEqual(encounter.sim_calibration("mists")["borrowed"], ["roads"])
            roads_k = encounter.sim_calibration("green")["k"]
            t = gearcheck.record_outcome(json.dumps(LOADOUT), "мгла", outcome="doable", min_hp=0.35, clear_minutes=7, save=False)
            self.assertIn("lowest HP: you 35%", t)
            self.assertEqual(encounter.sim_calibration("mists")["borrowed"], ["roads"])      # dry run: journal untouched
            with self.assertRaises(core.AOError):
                gearcheck.record_outcome(json.dumps(LOADOUT), "mists", outcome="easy")        # min_hp is required
            gearcheck.record_outcome(json.dumps(LOADOUT), "mists", outcome="doable", min_hp=0.35, clear_minutes=7)
            mists = encounter.sim_calibration("mists")
            self.assertEqual((mists["n"], mists["tn"], mists["borrowed"]), (1, 1, []))
            self.assertEqual(encounter.sim_calibration("green")["k"], roads_k)              # other groups keep their factor
            self.assertIn("mists", gearcheck.calibration())
        encounter._cal.clear()

    def test_intents(self):
        self.assertEqual(gearcheck.parse_intents("Q W на урон"), {"1": "damage", "2": "damage"})
        _, e = gearcheck.parse_loadout(json.dumps({"equipment": [{"item": "T4_MAIN_NATURESTAFF_KEEPER@1"}]}))
        gearcheck.apply_intents(e, gearcheck.parse_intents("q w на урон"))
        self.assertEqual(e[0]["active"][:2], ["THORNSAREA", "BRAMBLESEED"])


class GroupCheck(unittest.TestCase):
    EX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples", "loadouts")

    def test_roles(self):
        for f, role in (("bow_badon.json", "Ranged_DPS"), ("mace_tank.json", "Tank"), ("holy_healer.json", "Heal")):
            _, e = gearcheck.parse_loadout("@" + os.path.join(self.EX, f))
            self.assertEqual(gearcheck.detect_role(e)[0], role)

    def test_group_beats_solo_and_composition_matters(self):
        bow, heal = "@" + os.path.join(self.EX, "bow_badon.json"), "@" + os.path.join(self.EX, "holy_healer.json")
        duo = gearcheck.group_check([bow, bow], "blue", ips="avg=1250,mainhand=1300 | avg=1250,mainhand=1300", tiers=["6"], price=False, calibrate=False)
        trio = gearcheck.group_check([bow, bow, heal], "blue", ips="avg=1250,mainhand=1300 | avg=1250,mainhand=1300 | avg=1250",
                                     tiers=["6"], price=False, calibrate=False)

        def margin(t, chest="small"):  # margin @ default dodge for T6 <chest>
            row = next(l for l in t.splitlines() if l.startswith(f"| T6 | {chest} | "))
            return float(row.split("|")[5])
        self.assertGreater(margin(trio), margin(duo))   # adding a healer helps
        self.assertIn("no tank", duo)
        self.assertIn("Loot per player", trio)
        self.assertIn("Hardest pull", trio)


class PatchNotes(unittest.TestCase):
    def test_search_and_freshness(self):
        t = patchnotes.patchnotes("roads of avalon")
        self.assertIn("Roads", t)
        self.assertIn("[source]", t)
        self.assertTrue(patchnotes.current_patch()[0])
        self.assertTrue(patchnotes.last_major()[1])
        self.assertIn("current patch", core.info())

    def test_cards_show_recent_changes(self):
        self.assertIn("Recent patch changes", core.item("T8_MAIN_SWORD"))

    def test_unified_knowledge_index(self):
        t = core.search("avalon knight", types=["structs", "knowledge"])
        self.assertIn("Game structures", t)
        self.assertIn("AVALON", t)
        self.assertIn("Knowledge", core.search("bloodlust", types=["knowledge"]))
        sig = patchnotes._signature()
        with tempfile.NamedTemporaryFile("w", suffix=".md", dir=patchnotes.KNOWLEDGE_DIR, delete=False) as f:
            f.write("# zzqx test note\n")
        try:
            self.assertNotEqual(patchnotes._signature(), sig)  # a new note invalidates knowledge.db
        finally:
            os.remove(f.name)
        self.assertEqual(patchnotes._signature(), sig)

    def test_bbcode(self):
        md = patchnotes.bbcode_to_md("[h3]Title[/h3][b]Bold[/b][list][*]A[list][*]B[/*][/list][/*][/list][url=https://x.y]link[/url]")
        self.assertIn("### Title", md)
        self.assertIn("**Bold**", md)
        self.assertIn("- A", md)
        self.assertIn("  - B", md)
        self.assertIn("[link](https://x.y)", md)

    def test_note_staleness(self):
        self.assertIn("⚠", advisor._staleness("_updated: 2019-01-01_"))
        self.assertEqual(advisor._staleness("_updated: 2999-01-01_"), "")


class MCP(unittest.TestCase):
    def rpc(self, method, params=None, id_=1):
        return mcp_server.handle({"jsonrpc": "2.0", "id": id_, "method": method, "params": params or {}})

    def test_protocol(self):
        self.assertEqual(self.rpc("initialize", {"protocolVersion": "2025-06-18"})["result"]["serverInfo"]["name"], "albion")
        self.assertIsNone(mcp_server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}))
        names = {t["name"] for t in self.rpc("tools/list")["result"]["tools"]}
        self.assertEqual(names, {t["name"] for t in TOOLS})
        self.assertIn("error", self.rpc("nope"))

    def test_call(self):
        r = self.rpc("tools/call", {"name": "item", "arguments": {"query": "T4_BAG"}})["result"]
        self.assertFalse(r["isError"])
        self.assertIn("Adept's Bag", r["content"][0]["text"])
        r = self.rpc("tools/call", {"name": "item", "arguments": {"query": "zzzqqqxx"}})["result"]
        self.assertTrue(r["isError"])

    def test_every_tool_schema_is_json(self):
        for t in mcp_server.TOOL_LIST:
            json.dumps(t["inputSchema"])


class PvP(unittest.TestCase):
    EX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples", "loadouts")

    def test_rules_from_game_data(self):
        st, sl = pvp.zone_rules("corrupted_stalker"), pvp.zone_rules("corrupted_slayer")
        self.assertTrue(st["lethal"])
        self.assertEqual((st["cap"], st["entry_ip"]), (1000, 900))
        self.assertEqual((sl["cap"], sl["factor"], sl["entry_ip"]), (1300, 0.5, 1100))
        self.assertFalse(pvp.zone_rules("mists_yellow")["lethal"])
        self.assertFalse(pvp.zone_rules("arena_1v1")["lethal"])      # arena gear is never dropped
        self.assertEqual(pvp.resolve_zone("проклятые слеер"), "corrupted_slayer")
        self.assertAlmostEqual(pvp.effective_ip(1250, st), 1050)       # 1000 + 250 × 0.2
        self.assertEqual(pvp.effective_ip(900, st), 900)
        self.assertIn("Hellgate 2v2", pvp.pvp_rules())

    def test_kit_and_duel(self):
        bow = "@" + os.path.join(self.EX, "bow_badon.json")
        rules = pvp.zone_rules("corrupted_stalker")
        p = pvp.build_pvp_player(bow, {"avg_ip": 1250}, rules)
        self.assertLess(p["eff_avg"], p["avg"])                       # soft cap bites
        self.assertGreater(p["kit"]["burst"], 0)
        self.assertGreater(pvp.pvp_spell("CLEANSE_DASH")["cleanse"], 0)
        frost = {"name": "frost", "equipment": [{"item": "T8_MAIN_FROSTSTAFF"}, {"item": "T8_ARMOR_CLOTH_SET1"}]}
        self.assertGreater(pvp.build_pvp_player(frost, {"avg_ip": 1200})["kit"]["root30"], 0)
        strong = pvp.build_pvp_player(bow, {"avg_ip": 1400})
        weak = pvp.build_pvp_player(bow, {"avg_ip": 900})
        d = pvp.duel(strong, weak)
        self.assertGreater(d["win"], d["lose"])                       # more IP wins the mirror match
        self.assertAlmostEqual(d["win"] + d["lose"] + d["disengage"], 1.0, places=6)
        t = pvp.pvp_check(bow, "stalker", ips="avg=1250", opponent=bow, price=False)
        self.assertIn("lost (effective", t)
        self.assertIn("Matchups", t)

    def test_copy_spells_are_not_summed(self):
        from aodb import combat
        mimic = pvp.pvp_spell("MIMIC")                                # copies the enemy's last spell: refs dozens of spells
        self.assertLess(mimic["dmg"], 400)
        self.assertFalse(mimic.get("cc_hard"))
        self.assertTrue(combat.spell_profile("MIMIC", "players")["unreliable"])

    def test_cap_variants(self):
        c = pvp.ip_variants(["T6_HEAD_LEATHER_SET2@1"], 1000)["T6_HEAD_LEATHER_SET2@1"]
        self.assertIn("T4_HEAD_LEATHER_SET2@3", c)
        self.assertIn("T7_HEAD_LEATHER_SET2", c)

    @unittest.skipUnless(os.environ.get("AO_NET"), "network")
    def test_killboard_builds(self):
        self.assertIn("model win rate", pvp.pvp_builds("mists_black", pages=4, top=3))


class Encounters(unittest.TestCase):
    BOW = "@" + os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples", "loadouts", "bow_badon.json")

    def test_spawn_tiers_and_maps(self):
        opts = encounter.spawn_options("ROAMING_HERETIC_CAMP_ANY", 6, "Mists")
        self.assertTrue(all("MISTS" in m for m, _, _ in opts))           # the Mists variant, not the Royal one
        self.assertAlmostEqual(sum(pr for _, pr, _ in opts), 1.0, places=6)
        self.assertTrue(encounter._maps("corrupted", 6, None, 2))        # concrete corrupted dungeon maps
        self.assertTrue(encounter._maps("mists", 6, "Mists", 2))

    def test_mob_abilities(self):
        from aodb import combat
        archer = combat.mob_profile("T6_MOB_CAMP_MISTS_UNDEAD_ARCHER", True)
        self.assertNotIn("MOB_UNDEAD_ARCHER_BOSS_CHAIN_LIGHTNING", archer["abilities"])   # boss spell not on a normal mob
        self.assertTrue(combat.telegraphed("MOB_UNDEAD_ARCHER_SKILLSHOT"))                # warning area on the ground
        self.assertGreater(combat.mob_profile("T6_MOB_CD_DEMON_SORCERER", True)["dodgeable"], 0)  # caster without autos

    def test_optimizer_pieces(self):
        fams = optimizer.weapon_families(["bow", "crossbow"])
        self.assertIn("2H_WARBOW", fams)
        self.assertIn("MAIN_1HCROSSBOW", fams)
        self.assertIn("T4_2H_WARBOW@3", optimizer._variant_at("2H_WARBOW", 1000))
        lo = optimizer._loadout("MAIN_1HCROSSBOW", optimizer.KITS[0], 900, {})
        self.assertTrue(any("OFF_TORCH" in e["item"] for e in lo["equipment"]))  # one-handed weapon gets an off-hand
        from aodb import combat, market
        self.assertEqual(combat.spell_profile("SKILLSHOT_STUN", "players")["dmg"], 232)  # near/far alternatives, player version only
        self.assertIn("T6_2H_BOW_KEEPER", optimizer._variant_at("2H_BOW_KEEPER", 900))  # artifact 975 IP sits in the 900 band
        self.assertEqual(market._value_ratio([], True)[0], 10.0)                  # default market/value ratio, consumables
        self.assertTrue(market._absurd("T8_POTION_CLEANSE", 13_000_000))           # troll listing
        self.assertFalse(market._absurd("T8_POTION_CLEANSE", 15_000))

    def test_optimizer_weights(self):
        w = optimizer._weights("hunter", "pvp_win=1,pve_safe=0,pve_speed=0,pvp_live=0")
        self.assertEqual(w["pvp_win"], 1.0)
        self.assertAlmostEqual(sum(optimizer._weights("farm", None).values()), 1.0)
        for bad in (("nope", None), ("balanced", "speed=1"), ("balanced", "pvp_win=x")):
            with self.assertRaises(core.AOError):
                optimizer._weights(*bad)

    def test_fight_and_sim(self):
        p = gearcheck.build_player(self.BOW, {"avg_ip": 1250})
        strong, weak = encounter.Fighter(p, 3.0), encounter.Fighter(p, 0.5)
        knight = gearcheck._variant("T6_AVALON_SOLO_BOSS_ANY", 8, True)
        a, b = encounter.fight(strong, [(knight, 1)], 0.9), encounter.fight(weak, [(knight, 1)], 0.9)
        self.assertLess(a["time"], b["time"])                            # more damage kills faster
        t = encounter.encounter_sim(self.BOW, "stalker", ips="avg=1250", maps=2)
        self.assertIn("after the 1000 soft cap", t)
        self.assertIn("fame / hour", t)
        self.assertIn("Camp simulation", encounter.camp_sim(self.BOW, "green", 6, "small", ips="avg=1250"))


class EliteRisk(unittest.TestCase):
    def test_graded_and_worst_map(self):
        kit = next(k for k in optimizer.KITS if k[0].startswith("Mage Cowl · Cleric"))
        lo = optimizer._loadout("2H_DEMONICSTAFF", kit, 1000, {})
        key = encounter.resolve("mists")
        _, kind, tier, _, cont = encounter.CONTENT[key]
        p, mp, k = gearcheck.build_player(lo, {"spec_ip": 100}), encounter._maps(kind, tier, cont, 4), encounter.sim_calibration()["k"]
        risk = [max(r["elite_death"] for r in encounter.simulate(encounter.Fighter(p, k * x), mp, 0.9)) for x in (0.8, 1.0, 1.2)]
        self.assertGreater(risk[0], risk[1])                                    # less damage → more risk, no 0/1 cliff
        self.assertGreater(risk[1], risk[2])
        self.assertTrue(0.05 < risk[1] < 0.95)
        s = encounter.pve_summary(lo, "mists", ip_spec={"spec_ip": 100})
        self.assertAlmostEqual(s["elite"], risk[1])                             # worst map, not the median
        self.assertLessEqual(s["low_worst"], s["low"])


class MarketCache(unittest.TestCase):
    """Per-item cache, batching and 429 handling without the network (urlopen is faked)."""
    def setUp(self):
        d = tempfile.mkdtemp()
        self.patches = [mock.patch.object(market, "CACHE_DIR", d), mock.patch.object(market, "CACHE_DB", os.path.join(d, "m.sqlite")),
                        mock.patch.object(market, "_mem", {}), mock.patch.object(market.time, "sleep", lambda s: self.slept.append(s))]
        for p in self.patches:
            p.start()
        self.urls, self.slept, self.fail = [], [], 0
        market.WARNINGS.clear()

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def _urlopen(self, req, timeout=None):
        import io, urllib.error
        self.urls.append(req.full_url)
        if self.fail:
            self.fail -= 1
            raise urllib.error.HTTPError(req.full_url, 429, "Too Many Requests", {"Retry-After": "5"}, io.BytesIO())
        ids = req.full_url.split("/prices/")[1].split(".json")[0].split(",")
        body = json.dumps([{"item_id": i, "city": "Caerleon", "sell_price_min": 100} for i in ids]).encode()
        resp = mock.MagicMock(headers={})
        resp.read.return_value = body
        resp.__enter__.return_value = resp
        return resp

    def test_cache_per_item_and_429(self):
        with mock.patch.object(market.urllib.request, "urlopen", self._urlopen):
            self.assertEqual(len(market._get("prices", ["T4_BAG", "T5_BAG"], "europe")), 2)
            market._get("prices", ["T5_BAG", "T6_BAG"], "europe")
            self.assertIn("/prices/T6_BAG.json", self.urls[-1])                      # only the uncached item is requested
            self.fail = 1
            self.assertEqual(len(market._get("prices", ["T7_BAG"], "europe")), 1)    # waits Retry-After, then succeeds
            self.assertAlmostEqual(sum(self.slept), 5.0, places=1)
            market._mem.clear()
            with mock.patch.object(market, "TTL", {"prices": -1}), mock.patch.object(market, "WAIT", 1):
                self.fail = 9
                rows = market._get("prices", ["T4_BAG", "T8_BAG"], "europe")          # 429 → stale cache, gap reported
                self.assertEqual([r["item_id"] for r in rows], ["T4_BAG"])
                self.assertTrue(any("used cached" in w for w in market.WARNINGS))
                self.assertTrue(any("no prices data for 1" in w for w in market.WARNINGS))
                n = len(self.urls)
                market._get("prices", ["T4_BAG"], "europe")                          # cool-down: no new request
                self.assertEqual(len(self.urls), n)
                with self.assertRaises(market.RateLimited):
                    market._get("prices", ["T8_BAG"], "europe")

    def test_batches(self):
        ids = [f"T4_ITEM_NUMBER_{i:04d}" for i in range(400)]
        with mock.patch.object(market.urllib.request, "urlopen", self._urlopen):
            self.assertEqual(len(market._get("prices", ids, "europe")), 400)
        self.assertGreater(len(self.urls), 1)
        self.assertTrue(all(len(u) < 3300 for u in self.urls))


class ThinPrices(unittest.TestCase):
    def test_thin_and_artifact_craft(self):
        import time as _t
        now = _t.strftime("%Y-%m-%dT%H:%M:%S", _t.gmtime())
        listings = {"T4_2H_DOUBLEBLADEDSTAFF_CRYSTAL@1": [("Lymhurst", 2_000_000)],          # lone troll listing
                    "T4_ARTEFACT_2H_DOUBLEBLADEDSTAFF_CRYSTAL": [("Caerleon", 400_000), ("Martlock", 410_000), ("Lymhurst", 420_000)],
                    "T4_METALBAR_LEVEL1@1": [("Caerleon", 600)], "T4_LEATHER_LEVEL1@1": [("Caerleon", 650)],
                    "T4_METALBAR": [("Caerleon", 200)], "T4_LEATHER": [("Caerleon", 250)],
                    "T5_BAG": [("Caerleon", 20_000)]}

        def fake_get(kind, ids, server, **params):
            if kind == "history":
                return []
            return [{"item_id": i, "city": c, "sell_price_min": p, "sell_price_min_date": now}
                    for i in ids for c, p in listings.get(i, [])]
        with mock.patch.object(market, "_get", fake_get), mock.patch.object(market, "_last_load", dict), \
                mock.patch.object(market, "_last_save", lambda s: None):
            pm = market.price_map(["T4_2H_DOUBLEBLADEDSTAFF_CRYSTAL@1", "T4_2H_DOUBLEBLADEDSTAFF_CRYSTAL", "T5_BAG"], estimate=True)
        twin1, twin0, bag = (pm[i] for i in ("T4_2H_DOUBLEBLADEDSTAFF_CRYSTAL@1", "T4_2H_DOUBLEBLADEDSTAFF_CRYSTAL", "T5_BAG"))
        self.assertTrue(twin1[1].startswith("≈ craft cost") and "looks inflated" in twin1[1])   # 2M listing vs ~430k craft
        self.assertLess(twin1[0], 500_000)
        self.assertTrue(twin0[1].startswith("≈ craft cost"))                                      # no listing: artifact + materials
        self.assertGreater(twin0[0], 400_000)                                                     # not item value × average ratio
        self.assertTrue(market.is_thin(bag[1]))                                                   # one city, no history
        self.assertEqual(bag[0], 20_000)


class KillboardStore(unittest.TestCase):
    def test_accumulates_without_duplicates(self):
        d = tempfile.mkdtemp()
        ev = lambda i: {"EventId": i, "TimeStamp": f"2099-01-01T00:{i % 60:02d}:00Z", "numberOfParticipants": 1, "Participants": [{"x": 1}],
                        "Killer": {"AverageItemPower": 1200, "Equipment": {"MainHand": {"Type": "T6_2H_BOW", "Quality": 2}}},
                        "Victim": {"AverageItemPower": 1100, "Equipment": {"MainHand": {"Type": "T6_MAIN_SWORD", "Quality": 1}}}}
        pages = {0: [ev(i) for i in range(10, 5, -1)], 51: [ev(i) for i in range(5, 0, -1)]}
        with mock.patch.object(advisor, "KB_DB", os.path.join(d, "kb.sqlite")), \
                mock.patch.object(advisor, "_kb_page", lambda url: pages.get(int(url.rsplit("=", 1)[1]), [])), \
                mock.patch.object(advisor, "_kb_since", lambda: ("2098-01-01", None)):
            self.assertEqual(len(advisor._events("europe", 2)), 10)
            pages[0] = [ev(i) for i in range(12, 7, -1)]                     # 2 new events on top of 3 stored ones
            with mock.patch.object(advisor, "KB_FRESH", -1):
                evs = advisor._events("europe", 2)
            self.assertEqual(len(evs), 12)
            self.assertEqual(advisor.KB_INFO["new"], 2)
            self.assertNotIn("Participants", evs[0])                          # slim events only
            self.assertEqual(pvp._fight_scale(evs[0]), "solo")

    def test_weighted_ci(self):
        m, half = pvp.weighted_ci([1.0, 0.0], [10, 10])
        self.assertAlmostEqual(m, 0.5)
        self.assertGreater(half, pvp.weighted_ci([1.0, 0.0], [1000, 1000])[1])  # more fights → narrower range
        self.assertEqual(pvp.weighted_ci([0.7, 0.7], [3, 5])[1], 0.0)


class Cli(unittest.TestCase):
    def test_help_and_quantity_words(self):
        from aodb import cli
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()) as out, self.assertRaises(SystemExit):
            cli.main(["-h"])                                                            # help texts contain '%'
        self.assertIn("craft_profit", out.getvalue())
        fake = lambda ids, *a, **k: {i: (1000, "live") for i in ids}
        with mock.patch.object(market, "price_map", fake):
            self.assertIn("| 3 |", advisor.build_cost(["T4_BAG", "3x", "T7_MEAL_ROAST"], compare_enchants=False))


@unittest.skipUnless(os.environ.get("AO_NET"), "set AO_NET=1 to test the live market API")
class Market(unittest.TestCase):
    def test_price_and_profit(self):
        self.assertIn("T4_BAG", market.price(["T4_BAG"], cities="Caerleon"))
        self.assertIn("total cost", call("craft_profit", {"item": "T4_BAG", "city": "Martlock"}))


if __name__ == "__main__":
    unittest.main()
