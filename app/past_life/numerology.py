import unicodedata


ARCANA = {
    1: "The Magician", 2: "The High Priestess", 3: "The Empress", 4: "The Emperor",
    5: "The Hierophant", 6: "The Lovers", 7: "The Chariot", 8: "Strength",
    9: "The Hermit", 10: "Wheel of Fortune", 11: "Justice", 12: "The Hanged Man",
    13: "Death", 14: "Temperance", 15: "The Devil", 16: "The Tower",
    17: "The Star", 18: "The Moon", 19: "The Sun", 20: "Judgement",
    21: "The World", 22: "The Fool",
}


def word_arcana_number(word: str) -> int:
    normalized = unicodedata.normalize("NFKD", word.upper())
    total = sum(ord(char) - 64 for char in normalized if "A" <= char <= "Z")
    if total <= 0:
        raise ValueError("Word must contain letters A-Z.")
    while total > 22:
        total = sum(int(digit) for digit in str(total))
    return total
