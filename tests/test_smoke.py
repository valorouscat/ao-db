"""Smoke tests against a built ao.db. Run: python3 -m unittest discover tests  (AO_NET=1 also hits the market API)."""
import json, os, unittest
import tempfile
from unittest import mock
from aodb import advisor, core, market, mcp_server, patchnotes
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


@unittest.skipUnless(os.environ.get("AO_NET"), "set AO_NET=1 to test the live market API")
class Market(unittest.TestCase):
    def test_price_and_profit(self):
        self.assertIn("T4_BAG", market.price(["T4_BAG"], cities="Caerleon"))
        self.assertIn("total cost", call("craft_profit", {"item": "T4_BAG", "city": "Martlock"}))


if __name__ == "__main__":
    unittest.main()
