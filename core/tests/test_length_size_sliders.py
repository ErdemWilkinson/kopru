import base64
import unittest
from types import SimpleNamespace

from core import effects


class LengthSizeSliderTests(unittest.TestCase):
    def test_continuous_values_map_to_nearest_legacy_presets(self):
        self.assertEqual([effects.length_preset(value) for value in (0.5, 1.0, 2.0)],
                         ["short", "normal", "long"])
        self.assertEqual([effects.size_preset(value) for value in (0.03, 0.045, 0.06)],
                         ["small", "medium", "large"])
        self.assertEqual(effects.length_preset(0.25), "short")
        self.assertEqual(effects.size_preset(0.08), "large")

    def test_fractional_size_scales_against_short_edge_and_keeps_minimum(self):
        self.assertEqual(effects.edge_depth(1920, 1080, size_fraction=0.03), 32.4)
        self.assertEqual(effects.edge_depth(640, 480, size_fraction=0.02), 24)
        self.assertEqual(effects.edge_depth(3840, 2160, size_fraction=0.08), 172.8)

    def test_each_style_play_time_uses_shared_effect_timing_and_pace(self):
        self.assertEqual(effects.play_through_seconds("beam", 2.0), 1.2)
        self.assertEqual(effects.play_through_seconds("aperture", 0.5), 0.31)

    def test_switch_arrival_readout_uses_arrival_timing_when_there_is_no_departure(self):
        self.assertEqual(effects.play_through_seconds("locator", 1.0), 0.72)

    def test_shared_slider_readouts_use_core_timing_and_depth(self):
        self.assertEqual(effects.design_slider_readouts("beam", 2.0, 0.06, 1920, 1080),
                         ("1.2 s", "65 pt"))

    def test_preset_only_values_migrate_to_both_forms(self):
        pace, fraction, length, size = effects.design_values(
            length="long", size="small")
        self.assertEqual((pace, fraction, length, size), (2.0, 0.03, "long", "small"))

    def test_valid_continuous_values_take_precedence_and_invalid_values_fall_back(self):
        self.assertEqual(effects.design_values(1.35, 0.052, "normal", "medium"),
                         (1.35, 0.052, "normal", "medium"))
        self.assertEqual(effects.design_values(1.35, 0.052), (1.35, 0.052, "normal", "medium"))

    def test_a_preset_that_disagrees_with_its_slider_value_was_set_later_and_wins(self):
        self.assertEqual(effects.design_values(1.35, 0.052, "short", "small"),
                         (0.5, 0.03, "short", "small"))
        self.assertEqual(effects.design_values(99, 0.9, "short", "large"),
                         (0.5, 0.06, "short", "large"))


if __name__ == "__main__":
    unittest.main()
