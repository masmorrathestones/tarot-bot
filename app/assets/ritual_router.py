from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.tarot.persistence_service import ReadingNotFoundError, reading_persistence_service
from app.whatsapp.tarot_media import (
    card_back_asset_path,
    render_card_jpeg,
    render_spread_jpeg,
)


router = APIRouter(prefix="/api/assets", tags=["Assets"])


@router.get("/cards/{card_code}")
def get_tarot_card_image(
    card_code: str,
    reversed: bool = Query(default=False),
):
    try:
        content = render_card_jpeg(card_code, reversed)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail="Tarot card image is not available.") from exc
    return StreamingResponse(BytesIO(content), media_type="image/jpeg")


@router.get("/card-backs/{count}")
def get_card_back_choice_image(count: int):
    try:
        path = card_back_asset_path(count)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail="Card-back choice image is not available.") from exc
    return FileResponse(path, media_type="image/jpeg")


@router.get("/readings/{reading_id}/spread.jpg")
def get_reading_spread_image(
    reading_id: int,
    db: Session = Depends(get_db),
):
    try:
        reading = reading_persistence_service.get(db, reading_id)
    except ReadingNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Reading not found.") from exc

    try:
        drawn_cards = reading_persistence_service.reconstruct_drawn_cards(reading)
        language = str((reading.profile_snapshot or {}).get("language") or "en")
        content = render_spread_jpeg(
            drawn_cards,
            spread_code=reading.spread_code,
            language=language,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail="Reading spread image could not be rendered.") from exc

    return StreamingResponse(BytesIO(content), media_type="image/jpeg")
