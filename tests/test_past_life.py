import unittest

from app.past_life.numerology import ARCANA, word_arcana_number
from app.payments.config import PaymentSettings


class PastLifeWordArcanaTests(unittest.TestCase):
    def test_single_letter_uses_alphabet_position(self):
        self.assertEqual(word_arcana_number("A"), 1)
        self.assertEqual(word_arcana_number("V"), 22)

    def test_accents_and_case_are_normalized(self):
        self.assertEqual(word_arcana_number("ação"), word_arcana_number("ACAO"))

    def test_sum_is_reduced_until_at_most_twenty_two(self):
        self.assertEqual(word_arcana_number("ZZZ"), 15)  # 78 -> 7 + 8

    def test_non_letter_input_is_rejected(self):
        with self.assertRaises(ValueError):
            word_arcana_number("123 !")

    def test_every_possible_result_has_an_arcana(self):
        self.assertEqual(set(ARCANA), set(range(1, 23)))


class PastLifePricingTests(unittest.TestCase):
    def test_past_life_prices_are_two_dollars_and_twelve_reais(self):
        settings = PaymentSettings("", "", "https://example.test")
        self.assertEqual(settings.amount_for_currency("usd", "past_life_reading"), 200)
        self.assertEqual(settings.amount_for_currency("brl", "past_life_reading"), 1200)
        self.assertEqual(settings.amount_for_currency("usd", "tarot_reading"), 100)


if __name__ == "__main__":
    unittest.main()
