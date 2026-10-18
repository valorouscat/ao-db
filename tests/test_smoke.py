"""Smoke tests against a built ao.db. Run: python3 -m unittest discover tests  (AO_NET=1 also hits the market API)."""
import json, os, re, unittest
import tempfile
from unittest import mock
from aodb import advisor, core, gearcheck, market, mcp_server, patchnotes, pvp
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

    def test_cap_variants(self):
        c = pvp.ip_variants(["T6_HEAD_LEATHER_SET2@1"], 1000)["T6_HEAD_LEATHER_SET2@1"]
        self.assertIn("T4_HEAD_LEATHER_SET2@3", c)
        self.assertIn("T7_HEAD_LEATHER_SET2", c)

    @unittest.skipUnless(os.environ.get("AO_NET"), "network")
    def test_killboard_builds(self):
        self.assertIn("model win rate", pvp.pvp_builds("mists_black", pages=4, top=3))


@unittest.skipUnless(os.environ.get("AO_NET"), "set AO_NET=1 to test the live market API")
class Market(unittest.TestCase):
    def test_price_and_profit(self):
        self.assertIn("T4_BAG", market.price(["T4_BAG"], cities="Caerleon"))
        self.assertIn("total cost", call("craft_profit", {"item": "T4_BAG", "city": "Martlock"}))


if __name__ == "__main__":
    unittest.main()
