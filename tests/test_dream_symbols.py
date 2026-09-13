import unittest

from app.dreams.catalog import INITIAL_DREAM_SYMBOLS
from app.dreams.models import DreamSymbolEntity


class DreamSymbolCatalogTests(unittest.TestCase):
    def test_catalog_contains_both_interpretive_lenses(self):
        types = {item["interpretation_type"] for item in INITIAL_DREAM_SYMBOLS}
        self.assertEqual(types, {"MYSTICAL", "PSYCHOANALYTIC"})

    def test_every_entry_is_trilingual_and_sourced(self):
        required = {
            "canonical_key", "name_pt", "name_en", "name_es",
            "meaning_pt", "meaning_en", "meaning_es",
            "interpretation_type", "tradition", "source_book", "source_reference",
        }
        for item in INITIAL_DREAM_SYMBOLS:
            self.assertTrue(required.issubset(item))
            self.assertTrue(all(item[key].strip() for key in required))

    def test_same_symbol_can_have_distinct_lenses(self):
        water = [item for item in INITIAL_DREAM_SYMBOLS if item["canonical_key"] == "water"]
        self.assertEqual({item["interpretation_type"] for item in water}, {"MYSTICAL", "PSYCHOANALYTIC"})

    def test_model_uses_expected_table(self):
        self.assertEqual(DreamSymbolEntity.__tablename__, "dream_symbols")


if __name__ == "__main__":
    unittest.main()
