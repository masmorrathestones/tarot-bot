from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.whatsapp.arcana_media import arcana_asset_path


router = APIRouter(prefix="/api/assets", tags=["Assets"])


@router.get("/arcana/{arcana_number}")
def get_arcana_image(arcana_number: int):
    if not 1 <= arcana_number <= 22:
        raise HTTPException(status_code=404, detail="Arcana not found.")

    try:
        path = arcana_asset_path(arcana_number)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(
            status_code=404,
            detail="Arcana image is not available in the project assets.",
        ) from exc

    return FileResponse(path, media_type="image/jpeg")
