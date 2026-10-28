"""Run every test: python run_tests.py. The app modules import each other by their bare names,
as in Beamer, so app/ goes on sys.path beside the repo root."""
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / "app")]
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

suite = unittest.TestSuite()
for folder in ("core/tests", "app/tests"):
    suite.addTests(unittest.defaultTestLoader.discover(str(ROOT / folder), top_level_dir=str(ROOT)))
result = unittest.TextTestRunner(verbosity=1).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
