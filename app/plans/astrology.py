from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import swisseph as swe

from app.whatsapp.astrology import PLANETS, zodiac_position


MAJOR_ASPECTS = {
    "conjunction": 0.0,
    "sextile": 60.0,
    "square": 90.0,
    "trine": 120.0,
    "opposition": 180.0,
}


def _angle_distance(a: float, b: float) -> float:
    diff = abs((a - b) % 360.0)
    return min(diff, 360.0 - diff)


def calculate_weekly_transits(*, start_local: datetime, natal_chart: dict) -> dict:
    """Calculate deterministic transit metadata for seven local calendar days.

    The AI receives these calculated positions/aspects and performs only the
    interpretive step.
    """
    natal_positions = natal_chart.get("positions") or {}
    result_days = []
    flags = swe.FLG_MOSEPH | swe.FLG_SPEED

    for offset in range(7):
        local_dt = (start_local + timedelta(days=offset)).replace(hour=12, minute=0, second=0, microsecond=0)
        utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
        decimal_hour = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
        jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, decimal_hour, swe.GREG_CAL)

        transits = {}
        aspects = []
        for transit_name, body in PLANETS.items():
            values, _ = swe.calc_ut(jd, body, flags)
            longitude = float(values[0] % 360.0)
            transits[transit_name] = zodiac_position(longitude)

            for natal_name, natal in natal_positions.items():
                if not isinstance(natal, dict) or natal.get("longitude") is None:
                    continue
                distance = _angle_distance(longitude, float(natal["longitude"]))
                for aspect_name, exact_angle in MAJOR_ASPECTS.items():
                    orb = abs(distance - exact_angle)
                    if orb <= 3.0:
                        aspects.append({
                            "transit": transit_name,
                            "natal": natal_name,
                            "aspect": aspect_name,
                            "orb": round(orb, 2),
                        })
                        break

        result_days.append({
            "date": local_dt.date().isoformat(),
            "weekday": local_dt.strftime("%A"),
            "transits": transits,
            "major_aspects": sorted(aspects, key=lambda item: item["orb"])[:16],
        })

    return {
        "timezone": str(start_local.tzinfo),
        "start_date": result_days[0]["date"],
        "days": result_days,
    }
