# -*- coding: utf-8 -*-
import sys, os, json, unittest, tempfile, shutil, unittest.mock as mock

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
for m in ("PyQt5", "PyQt5.QtCore", "PyQt5.QtGui", "PyQt5.QtWidgets", "PyQt5.QtMultimedia"):
    sys.modules.setdefault(m, mock.MagicMock())

from game.save_manager import SaveManager

TEMPLATE = {"flags": {}, "current_room": "room3", "current_health": 6, "player_x": 5, "player_y": 5}

class TestSaveManager(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self._orig = SaveManager.SAVE_DIR
        SaveManager.SAVE_DIR = self.tmp
        with open(os.path.join(self.tmp, "file0.json"), "w") as f:
            json.dump(TEMPLATE, f)
        self.sm = SaveManager(slot=None)

    def tearDown(self):
        SaveManager.SAVE_DIR = self._orig
        shutil.rmtree(self.tmp)

    #  get_flag / set_flag
    def test_flag_default_false(self):
        self.assertFalse(self.sm.get_flag("inexistant"))

    def test_flag_set_and_get(self):
        self.sm.set_flag("sword", True)
        self.assertTrue(self.sm.get_flag("sword"))

    def test_flag_overwrite(self):
        self.sm.set_flag("switch", True)
        self.sm.set_flag("switch", False)
        self.assertFalse(self.sm.get_flag("switch"))

    #  get/set current_health 
    def test_health_default(self):
        self.assertEqual(self.sm.get_current_health(), 6)

    def test_health_set(self):
        self.sm.set_current_health(2)
        self.assertEqual(self.sm.get_current_health(), 2)

    #  get/set current_room
    def test_room_default(self):
        self.assertEqual(self.sm.get_current_room(), "room3")

    def test_room_set(self):
        self.sm.set_current_room("room7")
        self.assertEqual(self.sm.get_current_room(), "room7")

    # write_save / persistance 
    def test_write_save_creates_file(self):
        with mock.patch.object(SaveManager, "SAVE_DIR", self.tmp):
            SaveManager.write_save(1, {"current_health": 3})
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "file1.json")))

    def test_write_save_content(self):
        with mock.patch.object(SaveManager, "SAVE_DIR", self.tmp):
            SaveManager.write_save(2, {"current_room": "room9"})
        with open(os.path.join(self.tmp, "file2.json")) as f:
            data = json.load(f)
        self.assertEqual(data["current_room"], "room9")

if __name__ == "__main__":
    unittest.main()
