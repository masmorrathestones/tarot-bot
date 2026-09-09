from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

import httpx
import swisseph as swe
from timezonefinder import TimezoneFinder


ZODIAC_SIGNS = [
    "Áries", "Touro", "Gêmeos", "Câncer", "Leão", "Virgem",
    "Libra", "Escorpião", "Sagitário", "Capricórnio", "Aquário", "Peixes",
]

PLANETS = {
    "Sol": swe.SUN,
    "Lua": swe.MOON,
    "Mercúrio": swe.MERCURY,
    "Vênus": swe.VENUS,
    "Marte": swe.MARS,
    "Júpiter": swe.JUPITER,
    "Saturno": swe.SATURN,
    "Urano": swe.URANUS,
    "Netuno": swe.NEPTUNE,
    "Plutão": swe.PLUTO,
}


class BirthPlaceNotFoundError(ValueError):
    pass


class BirthTimezoneNotFoundError(ValueError):
    pass


@dataclass(frozen=True)
class BirthPlace:
    display_name: str
    latitude: float
    longitude: float
    timezone: str


def zodiac_position(longitude: float) -> dict:
    normalized = longitude % 360.0
    sign_index = int(normalized // 30)
    degree = normalized % 30
    return {
        "sign": ZODIAC_SIGNS[sign_index],
        "degree": round(degree, 2),
        "longitude": round(normalized, 4),
    }


def geocode_birth_place(query: str) -> BirthPlace:
    with httpx.Client(timeout=15.0, follow_redirects=True) as client:
        response = client.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": query,
                "format": "jsonv2",
                "limit": 1,
                "addressdetails": 1,
            },
            headers={
                "User-Agent": "tarot-bot/1.0 (natal-chart geocoder)",
                "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.7",
            },
        )
        response.raise_for_status()
        results = response.json()

    if not results:
        raise BirthPlaceNotFoundError(
            "Não consegui localizar esse lugar de nascimento."
        )

    result = results[0]
    latitude = float(result["lat"])
    longitude = float(result["lon"])
    timezone_name = TimezoneFinder().timezone_at(
        lat=latitude,
        lng=longitude,
    )
    if not timezone_name:
        raise BirthTimezoneNotFoundError(
            "Não consegui determinar o fuso horário desse local."
        )

    return BirthPlace(
        display_name=str(result.get("display_name") or query),
        latitude=latitude,
        longitude=longitude,
        timezone=timezone_name,
    )


def calculate_natal_chart(
    *,
    birth_date: date,
    birth_time: time,
    birth_place: BirthPlace,
) -> dict:
    local_datetime = datetime.combine(
        birth_date,
        birth_time,
        tzinfo=ZoneInfo(birth_place.timezone),
    )
    utc_datetime = local_datetime.astimezone(ZoneInfo("UTC"))

    decimal_hour = (
        utc_datetime.hour
        + utc_datetime.minute / 60.0
        + utc_datetime.second / 3600.0
    )
    julian_day = swe.julday(
        utc_datetime.year,
        utc_datetime.month,
        utc_datetime.day,
        decimal_hour,
        swe.GREG_CAL,
    )

    flags = swe.FLG_MOSEPH | swe.FLG_SPEED
    positions = {}
    for name, body in PLANETS.items():
        result, _ = swe.calc_ut(julian_day, body, flags)
        positions[name] = zodiac_position(result[0])

    _, ascmc = swe.houses(
        julian_day,
        birth_place.latitude,
        birth_place.longitude,
        b"P",
    )
    ascendant = zodiac_position(ascmc[0])

    return {
        "calculation": "tropical_geocentric_placidus",
        "birth_place": birth_place.display_name,
        "timezone": birth_place.timezone,
        "utc_datetime": utc_datetime.isoformat(),
        "positions": positions,
        "ascendant": ascendant,
    }


def format_natal_chart(chart: dict) -> str:
    positions = chart["positions"]
    lines = [
        "✨ Seu mapa astral básico ficou assim:",
        "",
    ]
    for body in (
        "Sol", "Lua", "Mercúrio", "Vênus", "Marte",
        "Júpiter", "Saturno", "Urano", "Netuno", "Plutão",
    ):
        position = positions[body]
        lines.append(
            f"{body}: {position['sign']} {position['degree']:.2f}°"
        )

    ascendant = chart["ascendant"]
    lines.extend(
        [
            f"Ascendente: {ascendant['sign']} {ascendant['degree']:.2f}°",
            "",
            "Esses dados ficam salvos no seu perfil e podem ser usados como "
            "contexto simbólico nas próximas leituras.",
        ]
    )
    return "\n".join(lines)
