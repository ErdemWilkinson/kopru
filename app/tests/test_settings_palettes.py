import unittest

import tokens
from core import settings


class PaletteIdsTests(unittest.TestCase):
    def test_core_names_the_same_palettes_as_the_tokens(self):
        # core stays free of Qt and app modules, so it keeps its own copy of the ids.
        self.assertEqual(settings.PALETTE_IDS, tuple(tokens.PALETTES))


if __name__ == "__main__":
    unittest.main()
