# -*- coding: utf-8 -*-
import sys, os, unittest, unittest.mock as mock

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
for m in ("PyQt5", "PyQt5.QtCore", "PyQt5.QtGui", "PyQt5.QtWidgets", "PyQt5.QtMultimedia"):
    sys.modules.setdefault(m, mock.MagicMock())

from game.item import Inventory

class TestInventory(unittest.TestCase):

    def setUp(self):
        self.inv = Inventory()

    #  add_item
    def test_add_item_succeeds(self):
        self.assertTrue(self.inv.add_item("pomme", 3))
        self.assertEqual(self.inv.count_item("pomme"), 3)

    def test_add_item_exceeds_stack(self):
        self.inv.add_item("pomme", 10)          # stack_max=10 → plein
        self.assertFalse(self.inv.add_item("pomme", 1))  # plus d'espace

    def test_add_unknown_item(self):
        self.assertFalse(self.inv.add_item("objet_fantome"))

    #  count_item
    def test_count_absent(self):
        self.assertEqual(self.inv.count_item("bombe"), 0)

    def test_count_collectible(self):
        self.inv.add_item("key", 4)
        self.assertEqual(self.inv.count_item("key"), 4)

    #  consume_one
    def test_consume_decrements(self):
        self.inv.add_item("potion", 2)
        self.inv.consume_one("potion")
        self.assertEqual(self.inv.count_item("potion"), 1)

    def test_consume_absent_returns_false(self):
        self.assertFalse(self.inv.consume_one("bombe"))

    #  serialisation / equip 
    def test_equip_serialized(self):
        self.inv.equip_item("boomerang")
        self.assertEqual(self.inv.to_save_data()["equipped_item"], "boomerang")

    def test_roundtrip_save_load(self):
        self.inv.add_item("pomme", 4)
        self.inv.equip_item("pomme")
        inv2 = Inventory()
        inv2.from_save_data(self.inv.to_save_data())
        self.assertEqual(inv2.count_item("pomme"), 4)
        self.assertEqual(inv2.equiped_item_id, "pomme")

    def test_reset_clears(self):
        self.inv.add_item("pomme", 5)
        self.inv.reset()
        self.assertEqual(self.inv.count_item("pomme"), 0)

if __name__ == "__main__":
    unittest.main()
