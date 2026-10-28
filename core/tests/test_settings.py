import json
import shutil
import tempfile
import unittest
from pathlib import Path

from core import effects, settings


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.folder, True)
        self.path = self.folder / "settings.json"

    def write(self, data):
        self.path.write_text(json.dumps(data), encoding="utf-8")

    def test_no_file_gives_the_defaults(self):
        self.assertEqual(settings.load(self.path), settings.DEFAULTS)

    def test_what_is_saved_loads_back(self):
        values = dict(settings.DEFAULTS, side="left", glow_style="rupture", resistance_px=200, auto_extend=False)
        settings.save(self.path, values)
        self.assertEqual(settings.load(self.path), values)

    def test_a_bad_value_falls_back_to_its_default_and_the_rest_stay(self):
        self.write({"side": "middle", "glow_style": "rupture", "resistance_px": -5, "effect_pace": 9})
        loaded = settings.load(self.path)
        self.assertEqual(loaded["glow_style"], "rupture")
        for key in ("side", "resistance_px", "effect_pace"):
            self.assertEqual(loaded[key], settings.DEFAULTS[key], key)

    def test_unknown_keys_are_dropped(self):
        self.write({"host": "10.0.0.2", "side": "top"})
        loaded = settings.load(self.path)
        self.assertNotIn("host", loaded)
        self.assertEqual(loaded["side"], "top")

    def test_an_unreadable_file_gives_the_defaults(self):
        self.path.write_text("{not json", encoding="utf-8")
        self.assertEqual(settings.load(self.path), settings.DEFAULTS)
        self.path.write_text("[1, 2]", encoding="utf-8")
        self.assertEqual(settings.load(self.path), settings.DEFAULTS)

    def test_a_hidden_effect_saved_by_beamer_loads_as_its_stand_in(self):
        hidden = next(iter(effects.STAND_INS))
        self.write({"glow_style": hidden})
        self.assertEqual(settings.load(self.path)["glow_style"], effects.STAND_INS[hidden])

    def test_saving_a_bad_value_is_refused_and_the_file_is_left_alone(self):
        settings.save(self.path, settings.DEFAULTS)
        before = self.path.read_bytes()
        with self.assertRaises(ValueError):
            settings.save(self.path, dict(settings.DEFAULTS, side="middle"))
        self.assertEqual(self.path.read_bytes(), before)

    def test_a_bool_is_not_a_number_and_a_number_is_not_a_bool(self):
        self.assertFalse(settings.valid("resistance_px", True))
        self.assertFalse(settings.valid("auto_extend", 1))
        self.assertTrue(settings.valid("effect_pace", 1))
        self.assertTrue(settings.valid("resistance_px", 0))

    def test_every_default_is_valid(self):
        for key, value in settings.DEFAULTS.items():
            self.assertTrue(settings.valid(key, value), key)

    def test_every_crossing_style_and_colour_is_offered(self):
        for style in ("glow", "beam") + effects.EFFECT_IDS:
            self.assertTrue(settings.valid("glow_style", style), style)
        for colour in settings.PALETTE_IDS + effects.PACK_IDS:
            self.assertTrue(settings.valid("glow_colour", colour), colour)


if __name__ == "__main__":
    unittest.main()
