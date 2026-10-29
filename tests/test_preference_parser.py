import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from api import webhook


class PreferenceParserTests(unittest.TestCase):
    def test_pipe_syntax_still_works(self):
        payload = webhook._parse_preference_payload("/favorito", "favorito comida|hamburguesa famous star|siempre la pide")
        self.assertEqual(payload, ("comida", "hamburguesa famous star", "siempre la pide"))

    def test_general_item_without_category(self):
        payload = webhook._parse_preference_payload("/gusta", "gusta pide siempre famous star en carls jr")
        self.assertEqual(payload, ("general", "pide siempre famous star en carls jr", ""))

    def test_short_category_and_item(self):
        payload = webhook._parse_preference_payload("/nogusta", "nogusta catsup")
        self.assertEqual(payload, ("general", "catsup", ""))


if __name__ == "__main__":
    unittest.main()
