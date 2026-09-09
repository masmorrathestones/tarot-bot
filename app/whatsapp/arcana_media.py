import os
from pathlib import Path


ARCANA_ASSET_DIR = Path(__file__).resolve().parents[1] / "assets" / "arcana"

# Local filenames expected in app/assets/arcana. The application numbering
# keeps Justice as 8, Strength as 11 and The Fool as 22.
_ARCANA_FILES = {
    1: "The Magician.jpg",
    2: "The High Priestess.jpg",
    3: "The Empress.jpg",
    4: "The Emperor.jpg",
    5: "The Hierophant.jpg",
    6: "The Lovers.jpg",
    7: "The Chariot.jpg",
    8: "Justice.jpg",
    9: "The Hermit.jpg",
    10: "Wheel of Fortune.jpg",
    11: "Strength.jpg",
    12: "The Hanged Man.jpg",
    13: "Death.jpg",
    14: "Temperance.jpg",
    15: "The Devil.jpg",
    16: "The Tower.jpg",
    17: "The Star.jpg",
    18: "The Moon.jpg",
    19: "The Sun.jpg",
    20: "Judgement.jpg",
    21: "The World.jpg",
    22: "The Fool.jpg",
}


def arcana_image_url(arcana_number: int) -> str:
    if arcana_number not in _ARCANA_FILES:
        raise ValueError("Invalid major arcana number.")

    base_url = os.getenv(
        "PUBLIC_BASE_URL",
        "https://tarot-bot-c1fv.onrender.com",
    ).rstrip("/")
    return f"{base_url}/api/assets/arcana/{arcana_number}"


def arcana_asset_path(arcana_number: int) -> Path:
    filename = _ARCANA_FILES.get(arcana_number)
    if filename is None:
        raise ValueError("Invalid major arcana number.")

    path = ARCANA_ASSET_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(
            f"Local arcana image not found: {path}. "
            "Add the Major Arcana images to app/assets/arcana."
        )

    return path
