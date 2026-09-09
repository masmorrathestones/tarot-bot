import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.whatsapp.arcana_media import ensure_arcana_asset


router = APIRouter(prefix="/api/assets", tags=["Assets"])


@router.get("/arcana/{arcana_number}")
def get_arcana_image(arcana_number: int):
    if not 1 <= arcana_number <= 22:
        raise HTTPException(status_code=404, detail="Arcana not found.")

    try:
        path = ensure_arcana_asset(arcana_number)
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to load arcana image.",
        ) from exc

    return FileResponse(path, media_type="image/jpeg")
