from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.persistence.models import UserEntity, UserProfileEntity
from app.users.schemas import CreateUserRequest, UpdateUserRequest


class UserAlreadyExistsError(ValueError):
    pass


class UserNotFoundError(ValueError):
    pass


def normalize_whatsapp_number(value: str) -> str:
    value = value.strip()
    prefix = "+" if value.startswith("+") else ""
    digits = "".join(char for char in value if char.isdigit())
    return f"{prefix}{digits}"


class UserService:
    def create(self, db: Session, request: CreateUserRequest) -> UserEntity:
        user = UserEntity(
            name=request.name.strip(),
            whatsapp_number=normalize_whatsapp_number(request.whatsapp_number),
        )

        profile = request.profile
        user.profile = UserProfileEntity(
            sun_sign=profile.sun_sign if profile else None,
            moon_sign=profile.moon_sign if profile else None,
            rising_sign=profile.rising_sign if profile else None,
            mbti=profile.mbti.upper() if profile and profile.mbti else None,
        )

        db.add(user)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise UserAlreadyExistsError(
                "A user with this WhatsApp number already exists."
            ) from exc

        return self.get(db, user.id)

    def create_named_whatsapp_user(
        self,
        db: Session,
        *,
        whatsapp_number: str,
        name: str,
    ) -> UserEntity:
        clean_name = " ".join(name.strip().split())[:120]
        if not clean_name:
            raise ValueError("Name cannot be empty.")

        normalized = normalize_whatsapp_number(whatsapp_number)
        user = UserEntity(name=clean_name, whatsapp_number=normalized)
        user.profile = UserProfileEntity()
        db.add(user)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            return self.get_by_whatsapp(db, normalized)
        return self.get(db, user.id)

    def get(self, db: Session, user_id: int) -> UserEntity:
        user = db.scalar(
            select(UserEntity)
            .options(selectinload(UserEntity.profile))
            .where(UserEntity.id == user_id)
        )
        if user is None:
            raise UserNotFoundError("User not found.")
        return user

    def get_by_whatsapp(
        self, db: Session, whatsapp_number: str
    ) -> UserEntity:
        number = normalize_whatsapp_number(whatsapp_number)
        user = db.scalar(
            select(UserEntity)
            .options(selectinload(UserEntity.profile))
            .where(UserEntity.whatsapp_number == number)
        )
        if user is None:
            raise UserNotFoundError("User not found.")
        return user

    def get_or_create_by_whatsapp(
        self,
        db: Session,
        *,
        whatsapp_number: str,
        display_name: str | None = None,
    ) -> tuple[UserEntity, bool]:
        try:
            return self.get_by_whatsapp(db, whatsapp_number), False
        except UserNotFoundError:
            pass

        normalized = normalize_whatsapp_number(whatsapp_number)
        fallback_name = f"WhatsApp user {normalized[-4:]}" if normalized else "WhatsApp user"

        user = UserEntity(
            name=(display_name or fallback_name).strip()[:120],
            whatsapp_number=normalized,
        )
        user.profile = UserProfileEntity()
        db.add(user)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            return self.get_by_whatsapp(db, whatsapp_number), False

        return self.get(db, user.id), True

    def update(
        self, db: Session, user_id: int, request: UpdateUserRequest
    ) -> UserEntity:
        user = self.get(db, user_id)

        if request.name is not None:
            user.name = request.name.strip()
        if request.whatsapp_number is not None:
            user.whatsapp_number = normalize_whatsapp_number(
                request.whatsapp_number
            )

        if request.profile is not None:
            if user.profile is None:
                user.profile = UserProfileEntity()
            user.profile.sun_sign = request.profile.sun_sign
            user.profile.moon_sign = request.profile.moon_sign
            user.profile.rising_sign = request.profile.rising_sign
            user.profile.mbti = (
                request.profile.mbti.upper()
                if request.profile.mbti else None
            )

        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise UserAlreadyExistsError(
                "A user with this WhatsApp number already exists."
            ) from exc

        return self.get(db, user_id)


user_service = UserService()
