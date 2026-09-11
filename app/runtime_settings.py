from sqlalchemy.orm import Session

from app.persistence.models import RuntimeSettingEntity


TRUE_VALUES = {"1", "true", "yes", "on", "enabled"}


def get_runtime_setting(db: Session, key: str, default: str | None = None) -> str | None:
    row = db.get(RuntimeSettingEntity, key)
    if row is None:
        return default
    return row.value


def runtime_setting_enabled(db: Session, key: str, default: bool = False) -> bool:
    raw = get_runtime_setting(db, key)
    if raw is None:
        return default
    return raw.strip().lower() in TRUE_VALUES
