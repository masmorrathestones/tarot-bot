import os
from pathlib import Path
from urllib.parse import quote

import httpx


ARCANA_ASSET_DIR = Path(__file__).resolve().parents[1] / "assets" / "arcana"

# Rider-Waite-Smith major arcana images. The symbolic numbering used by the
# application keeps Justice as 8 and Strength as 11, so the mapping is by the
# application's arcana number rather than the number printed on the RWS card.
_ARCANA_FILES = {
    1: "RWS Tarot 01 Magician.jpg",
    2: "RWS Tarot 02 High Priestess.jpg",
    3: "RWS Tarot 03 Empress.jpg",
    4: "RWS Tarot 04 Emperor.jpg",
    5: "RWS Tarot 05 Hierophant.jpg",
    6: "RWS Tarot 06 Lovers.jpg",
    7: "RWS Tarot 07 Chariot.jpg",
    8: "RWS Tarot 11 Justice.jpg",
    9: "RWS Tarot 09 Hermit.jpg",
    10: "RWS Tarot 10 Wheel of Fortune.jpg",
    11: "RWS Tarot 08 Strength.jpg",
    12: "RWS Tarot 12 Hanged Man.jpg",
    13: "RWS Tarot 13 Death.jpg",
    14: "RWS Tarot 14 Temperance.jpg",
    15: "RWS Tarot 15 Devil.jpg",
    16: "RWS Tarot 16 Tower.jpg",
    17: "RWS Tarot 17 Star.jpg",
    18: "RWS Tarot 18 Moon.jpg",
    19: "RWS Tarot 19 Sun.jpg",
    20: "RWS Tarot 20 Judgement.jpg",
    21: "RWS Tarot 21 World.jpg",
    22: "RWS Tarot 00 Fool.jpg",
}


def source_arcana_url(arcana_number: int) -> str:
    filename = _ARCANA_FILES[arcana_number]
    return (
        "https://commons.wikimedia.org/wiki/Special:Redirect/file/"
        f"{quote(filename)}?width=700"
    )


def arcana_image_url(arcana_number: int) -> str:
    base_url = os.getenv(
        "PUBLIC_BASE_URL",
        "https://tarot-bot-c1fv.onrender.com",
    ).rstrip("/")
    return f"{base_url}/api/assets/arcana/{arcana_number}"


def ensure_arcana_asset(arcana_number: int) -> Path:
    if arcana_number not in _ARCANA_FILES:
        raise ValueError("Invalid major arcana number.")

    ARCANA_ASSET_DIR.mkdir(parents=True, exist_ok=True)
    target = ARCANA_ASSET_DIR / f"{arcana_number:02d}.jpg"
    if target.exists() and target.stat().st_size > 0:
        return target

    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        response = client.get(source_arcana_url(arcana_number))
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "image" not in content_type.lower():
            raise ValueError("Arcana source did not return an image.")
        target.write_bytes(response.content)

    return target
