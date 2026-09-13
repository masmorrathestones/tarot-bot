import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.dreams.matcher import match_dream_symbols, normalize_words
from app.dreams.models import DreamSymbolEntity
from app.payments.config import PaymentSettings


class DreamInterpretationTests(unittest.TestCase):
    def test_dream_prices_are_three_dollars_and_eighteen_reais(self):
        settings = PaymentSettings("", "", "https://example.test")
        self.assertEqual(settings.amount_for_currency("usd", "dream_interpretation"), 300)
        self.assertEqual(settings.amount_for_currency("brl", "dream_interpretation"), 1800)

    def test_normalization_ignores_case_accents_and_punctuation(self):
        self.assertEqual(normalize_words("  CÃO-de-Guarda! "), "cao de guarda")

    def test_matcher_uses_word_boundaries_and_all_language_names(self):
        engine = create_engine("sqlite+pysqlite:///:memory:")
        DreamSymbolEntity.__table__.create(engine)
        with Session(engine) as db:
            db.add_all([
                DreamSymbolEntity(canonical_key="mar", name_pt="mar", name_en="sea", name_es="mar", meaning_pt="pt", meaning_en="en", meaning_es="es", interpretation_type="MYSTICAL", tradition="popular", source_book="book", source_reference="1"),
                DreamSymbolEntity(canonical_key="cao", name_pt="cão", name_en="dog", name_es="perro", meaning_pt="cão pt", meaning_en="dog en", meaning_es="perro es", interpretation_type="PSYCHOANALYTIC", tradition="jungian", source_book="book", source_reference="2"),
            ])
            db.commit()
            matches = match_dream_symbols(db, "O cachorro correu até o SEA; depois vi um cão.", language="pt")
        self.assertEqual({item["canonical_key"] for item in matches}, {"cao", "mar"})
        self.assertEqual(next(item for item in matches if item["canonical_key"] == "cao")["meaning"], "cão pt")

    def test_matcher_does_not_match_substrings(self):
        engine = create_engine("sqlite+pysqlite:///:memory:")
        DreamSymbolEntity.__table__.create(engine)
        with Session(engine) as db:
            db.add(DreamSymbolEntity(canonical_key="mar", name_pt="mar", name_en="sea", name_es="mar", meaning_pt="pt", meaning_en="en", meaning_es="es", interpretation_type="MYSTICAL", tradition="popular", source_book="book", source_reference="1"))
            db.commit()
            self.assertEqual(match_dream_symbols(db, "Ela amargou a decisão.", language="pt"), [])


if __name__ == "__main__":
    unittest.main()
