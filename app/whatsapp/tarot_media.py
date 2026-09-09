import os
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.tarot.enums import ArcanaType, Orientation
from app.tarot.models import DrawnCard, TarotCard
from app.tarot.service import tarot_draw_service
from app.whatsapp.i18n import normalize_language, t


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
    card = next((item for item in tarot_draw_service.list_cards() if item.code == card_code.upper()), None)
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
    return f"{_public_base_url()}/api/assets/cards/{card_code.upper()}?reversed={reversed_value}"


def card_back_image_url(count: int) -> str:
    return f"{_public_base_url()}/api/assets/card-backs/{count}"


def spread_image_url(reading_id: int) -> str:
    return f"{_public_base_url()}/api/assets/readings/{reading_id}/spread.jpg"


def card_caption(
    *,
    card: TarotCard,
    orientation: Orientation,
    card_number: int,
    language: str = "en",
) -> str:
    emoji = _SPECIAL_CARD_EMOJIS.get(card.code)
    if emoji is None and card.arcana == ArcanaType.MAJOR:
        emoji = "✨"

    name = f"*{card.name}*"
    if emoji:
        name = f"{emoji} {name} {emoji}"

    orientation_line = t(language, "reversed") if orientation == Orientation.REVERSED else t(language, "upright")
    return f"{name}\n{orientation_line}\n\n{t(language, 'card_number', number=card_number)}"


def render_card_jpeg(card_code: str, reversed_card: bool) -> bytes:
    path = card_asset_path(card_code)
    with Image.open(path) as source:
        image = source.convert("RGB")
        if reversed_card:
            image = image.rotate(180, expand=False)
        output = BytesIO()
        image.save(output, format="JPEG", quality=92, optimize=True)
        return output.getvalue()


def _prepared_spread_card(item: DrawnCard, target_height: int) -> Image.Image:
    with Image.open(card_asset_path(item.card.code)) as source:
        image = source.convert("RGB")
        if item.orientation == Orientation.REVERSED:
            image = image.rotate(180, expand=False)
        ratio = target_height / image.height
        target_width = max(1, int(image.width * ratio))
        return image.resize((target_width, target_height), Image.Resampling.LANCZOS)


def _save_spread_canvas(canvas: Image.Image) -> bytes:
    output = BytesIO()
    canvas.save(output, format="JPEG", quality=90, optimize=True)
    return output.getvalue()


def _render_default_spread_jpeg(drawn_cards: list[DrawnCard]) -> bytes:
    target_height = 900
    gap = 28
    images: list[Image.Image] = []
    try:
        images = [_prepared_spread_card(item, target_height) for item in drawn_cards]
        canvas_width = sum(image.width for image in images) + gap * (len(images) - 1)
        canvas = Image.new("RGB", (canvas_width, target_height), (245, 242, 235))
        x = 0
        for image in images:
            canvas.paste(image, (x, 0))
            x += image.width + gap
        return _save_spread_canvas(canvas)
    finally:
        for image in images:
            image.close()


def _draw_centered_label(draw: ImageDraw.ImageDraw, *, text: str, center_x: int, y: int, font: ImageFont.ImageFont) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    width = bbox[2] - bbox[0]
    draw.text((center_x - width // 2, y), text, fill=(55, 52, 47), font=font)


def _render_decision_spread_jpeg(drawn_cards: list[DrawnCard], language: str = "en") -> bytes:
    language = normalize_language(language)
    cards_by_position = {item.position.index: item for item in drawn_cards}
    required_positions = set(range(1, 8))
    missing = sorted(required_positions - set(cards_by_position))
    if missing:
        raise ValueError(f"DECISION_SPREAD requires positions 1 through 7; missing: {missing}")

    labels = {
        "en": ("DECISION / CORE ISSUE - CARD 7", "IF YOU DO IT - 5 > 1 > 3", "IF YOU DON'T - 6 > 2 > 4"),
        "pt": ("DECISÃO / QUESTÃO CENTRAL - CARTA 7", "SE VOCÊ FIZER - 5 > 1 > 3", "SE VOCÊ NÃO FIZER - 6 > 2 > 4"),
        "es": ("DECISIÓN / CUESTIÓN CENTRAL - CARTA 7", "SI LO HACES - 5 > 1 > 3", "SI NO LO HACES - 6 > 2 > 4"),
    }[language]

    target_height = 520
    card_gap = 28
    row_gap = 48
    label_height = 30
    margin = 36
    background = (245, 242, 235)
    images: dict[int, Image.Image] = {}

    try:
        images = {index: _prepared_spread_card(cards_by_position[index], target_height) for index in required_positions}
        action_order = (5, 1, 3)
        inaction_order = (6, 2, 4)

        def row_width(order: tuple[int, ...]) -> int:
            return sum(images[index].width for index in order) + card_gap * (len(order) - 1)

        action_width = row_width(action_order)
        inaction_width = row_width(inaction_order)
        significator_width = images[7].width
        canvas_width = max(action_width, inaction_width, significator_width) + margin * 2

        significator_label_y = margin
        significator_y = significator_label_y + label_height
        action_label_y = significator_y + target_height + row_gap
        action_y = action_label_y + label_height
        inaction_label_y = action_y + target_height + row_gap
        inaction_y = inaction_label_y + label_height
        canvas_height = inaction_y + target_height + margin

        canvas = Image.new("RGB", (canvas_width, canvas_height), background)
        draw = ImageDraw.Draw(canvas)
        font = ImageFont.load_default()
        center_x = canvas_width // 2

        _draw_centered_label(draw, text=labels[0], center_x=center_x, y=significator_label_y, font=font)
        canvas.paste(images[7], (center_x - images[7].width // 2, significator_y))

        _draw_centered_label(draw, text=labels[1], center_x=center_x, y=action_label_y, font=font)
        x = (canvas_width - action_width) // 2
        for index in action_order:
            canvas.paste(images[index], (x, action_y))
            x += images[index].width + card_gap

        _draw_centered_label(draw, text=labels[2], center_x=center_x, y=inaction_label_y, font=font)
        x = (canvas_width - inaction_width) // 2
        for index in inaction_order:
            canvas.paste(images[index], (x, inaction_y))
            x += images[index].width + card_gap

        return _save_spread_canvas(canvas)
    finally:
        for image in images.values():
            image.close()


def render_spread_jpeg(
    drawn_cards: list[DrawnCard],
    *,
    spread_code: str | None = None,
    language: str = "en",
) -> bytes:
    if not drawn_cards:
        raise ValueError("Cannot render an empty Tarot spread.")
    if spread_code == "DECISION_SPREAD":
        return _render_decision_spread_jpeg(drawn_cards, language=language)
    return _render_default_spread_jpeg(drawn_cards)
