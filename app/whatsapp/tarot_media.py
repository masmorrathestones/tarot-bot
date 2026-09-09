import os
from io import BytesIO
from pathlib import Path

from PIL import Image

from app.tarot.enums import ArcanaType, Orientation
from app.tarot.models import DrawnCard, TarotCard
from app.tarot.service import tarot_draw_service


CARD_ASSET_DIR = Path(__file__).resolve().parents[1] / "assets" / "arcana"

_SPECIAL_CARD_EMOJIS = {
    "THE_TOWER": "⚡",
    "DEATH": "🖤",
    "THE_DEVIL": "⛓️",
    "THE_SUN": "☀️",
    "THE_MOON": "🌙",
    "THE_STAR": "⭐",
    "THE_LOVERS": "💞",
    "WHEEL_OF_FORTUNE": "🌀",
    "THREE_OF_SWORDS": "💔",
    "TEN_OF_SWORDS": "⚔️",
    "FIVE_OF_PENTACLES": "❄️",
    "TEN_OF_CUPS": "🌈",
}


def _public_base_url() -> str:
    return os.getenv(
        "PUBLIC_BASE_URL",
        "https://tarot-bot-c1fv.onrender.com",
    ).rstrip("/")


def _card_by_code(card_code: str) -> TarotCard:
    card = next(
        (
            item
            for item in tarot_draw_service.list_cards()
            if item.code == card_code.upper()
        ),
        None,
    )
    if card is None:
        raise ValueError(f"Unknown Tarot card code: {card_code}")
    return card


def card_asset_path(card_code: str) -> Path:
    card = _card_by_code(card_code)
    path = CARD_ASSET_DIR / f"{card.name}.jpg"
    if not path.is_file():
        raise FileNotFoundError(f"Tarot card image not found: {path}")
    return path


def card_back_asset_path(count: int) -> Path:
    if count not in {2, 3, 4}:
        raise ValueError("Card-back choice image count must be 2, 3, or 4.")
    path = CARD_ASSET_DIR / f"{count}backs.jpg"
    if not path.is_file():
        raise FileNotFoundError(f"Card-back choice image not found: {path}")
    return path


def card_image_url(card_code: str, orientation: Orientation) -> str:
    reversed_value = "true" if orientation == Orientation.REVERSED else "false"
    return (
        f"{_public_base_url()}/api/assets/cards/{card_code.upper()}"
        f"?reversed={reversed_value}"
    )


def card_back_image_url(count: int) -> str:
    return f"{_public_base_url()}/api/assets/card-backs/{count}"


def spread_image_url(reading_id: int) -> str:
    return f"{_public_base_url()}/api/assets/readings/{reading_id}/spread.jpg"


def card_caption(
    *,
    card: TarotCard,
    orientation: Orientation,
    card_number: int,
) -> str:
    emoji = _SPECIAL_CARD_EMOJIS.get(card.code)
    if emoji is None and card.arcana == ArcanaType.MAJOR:
        emoji = "✨"

    name = f"*{card.name}*"
    if emoji:
        name = f"{emoji} {name} {emoji}"

    orientation_line = (
        "Reversed" if orientation == Orientation.REVERSED else "Upright"
    )
    return f"{name}\n{orientation_line}\n\nCard {card_number}"


def render_card_jpeg(card_code: str, reversed_card: bool) -> bytes:
    path = card_asset_path(card_code)
    with Image.open(path) as source:
        image = source.convert("RGB")
        if reversed_card:
            image = image.rotate(180, expand=False)
        output = BytesIO()
        image.save(output, format="JPEG", quality=92, optimize=True)
        return output.getvalue()


def render_spread_jpeg(drawn_cards: list[DrawnCard]) -> bytes:
    if not drawn_cards:
        raise ValueError("Cannot render an empty Tarot spread.")

    target_height = 900
    gap = 28
    images: list[Image.Image] = []

    try:
        for item in drawn_cards:
            with Image.open(card_asset_path(item.card.code)) as source:
                image = source.convert("RGB")
                if item.orientation == Orientation.REVERSED:
                    image = image.rotate(180, expand=False)

                ratio = target_height / image.height
                target_width = max(1, int(image.width * ratio))
                image = image.resize(
                    (target_width, target_height),
                    Image.Resampling.LANCZOS,
                )
                images.append(image)

        canvas_width = sum(image.width for image in images) + gap * (len(images) - 1)
        canvas = Image.new("RGB", (canvas_width, target_height), (245, 242, 235))

        x = 0
        for image in images:
            canvas.paste(image, (x, 0))
            x += image.width + gap

        output = BytesIO()
        canvas.save(output, format="JPEG", quality=90, optimize=True)
        return output.getvalue()
    finally:
        for image in images:
            image.close()
