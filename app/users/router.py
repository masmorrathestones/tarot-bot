from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.users.schemas import (
    CreateUserRequest, UpdateUserRequest,
    UserProfileResponse, UserResponse,
)
from app.users.service import (
    UserAlreadyExistsError, UserNotFoundError, user_service,
)

router = APIRouter(prefix="/api/users", tags=["Users"])


def map_user(user) -> UserResponse:
    p = user.profile
    return UserResponse(
        id=user.id,
        name=user.name,
        whatsapp_number=user.whatsapp_number,
        profile=UserProfileResponse(
            sun_sign=p.sun_sign if p else None,
            moon_sign=p.moon_sign if p else None,
            rising_sign=p.rising_sign if p else None,
            mbti=p.mbti if p else None,
            birth_date=p.birth_date if p else None,
            birth_time=p.birth_time if p else None,
            zodiac_sign=p.zodiac_sign if p else None,
            personal_number=p.personal_number if p else None,
            personal_arcana_number=p.personal_arcana_number if p else None,
            personal_arcana_name=p.personal_arcana_name if p else None,
            year_arcana_number=p.year_arcana_number if p else None,
            year_arcana_name=p.year_arcana_name if p else None,
            year_arcana_reference_year=(
                p.year_arcana_reference_year if p else None
            ),
        ),
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.post("", response_model=UserResponse, status_code=201)
def create_user(
    request: CreateUserRequest,
    db: Session = Depends(get_db),
):
    try:
        return map_user(user_service.create(db, request))
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/by-whatsapp/{whatsapp_number:path}", response_model=UserResponse)
def get_user_by_whatsapp(
    whatsapp_number: str,
    db: Session = Depends(get_db),
):
    try:
        return map_user(
            user_service.get_by_whatsapp(db, whatsapp_number)
        )
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    try:
        return map_user(user_service.get(db, user_id))
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    request: UpdateUserRequest,
    db: Session = Depends(get_db),
):
    try:
        return map_user(user_service.update(db, user_id, request))
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
