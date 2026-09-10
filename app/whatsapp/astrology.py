from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

import httpx
import swisseph as swe
from timezonefinder import TimezoneFinder


ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
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


def _timezone_for(latitude: float, longitude: float, provider_timezone: str | None = None) -> str:
    if provider_timezone:
        try:
            ZoneInfo(provider_timezone)
            return provider_timezone
        except Exception:
            pass

    timezone_name = TimezoneFinder().timezone_at(lat=latitude, lng=longitude)
    if not timezone_name:
        raise BirthTimezoneNotFoundError("Unable to determine the timezone for that location.")
    return timezone_name


def _geocode_with_nominatim(client: httpx.Client, query: str, language: str) -> BirthPlace | None:
    accept_language = {
        "pt": "pt-BR,pt;q=0.9",
        "es": "es,es-ES;q=0.9",
    }.get(language, "en,en-US;q=0.9")

    response = client.get(
        "https://nominatim.openstreetmap.org/search",
        params={
            "q": query,
            "format": "jsonv2",
            "limit": 1,
            "addressdetails": 1,
        },
        headers={
            "User-Agent": "Holomancy-TarotBot/1.0",
            "Accept-Language": accept_language,
        },
    )
    response.raise_for_status()
    results = response.json()
    if not results:
        return None

    result = results[0]
    latitude = float(result["lat"])
    longitude = float(result["lon"])
    return BirthPlace(
        display_name=str(result.get("display_name") or query),
        latitude=latitude,
        longitude=longitude,
        timezone=_timezone_for(latitude, longitude),
    )


def _geocode_with_open_meteo(client: httpx.Client, query: str, language: str) -> BirthPlace | None:
    provider_language = {"pt": "pt", "es": "es"}.get(language, "en")
    response = client.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={
            "name": query,
            "count": 1,
            "language": provider_language,
            "format": "json",
        },
        headers={"User-Agent": "Holomancy-TarotBot/1.0"},
    )
    response.raise_for_status()
    results = response.json().get("results") or []
    if not results:
        return None

    result = results[0]
    latitude = float(result["latitude"])
    longitude = float(result["longitude"])
    parts = [
        str(result.get("name") or "").strip(),
        str(result.get("admin1") or "").strip(),
        str(result.get("country") or "").strip(),
    ]
    display_name = ", ".join(part for index, part in enumerate(parts) if part and part not in parts[:index])
    return BirthPlace(
        display_name=display_name or query,
        latitude=latitude,
        longitude=longitude,
        timezone=_timezone_for(latitude, longitude, str(result.get("timezone") or "") or None),
    )


def geocode_place(query: str, language: str = "en") -> BirthPlace:
    """Resolve a city/place using two independent providers.

    Nominatim remains the primary provider. Open-Meteo is used as a fallback so
    a temporary block/rate-limit/provider failure does not trap the WhatsApp
    conversation in the location prompt.
    """
    clean_query = query.strip()
    if len(clean_query) < 2:
        raise BirthPlaceNotFoundError("Location query is too short.")

    provider_errors: list[Exception] = []
    with httpx.Client(timeout=12.0, follow_redirects=True) as client:
        for resolver in (_geocode_with_nominatim, _geocode_with_open_meteo):
            try:
                result = resolver(client, clean_query, language)
                if result is not None:
                    return result
            except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
                provider_errors.append(exc)

    if provider_errors and len(provider_errors) == 2:
        raise BirthPlaceNotFoundError("Location providers were unavailable or could not resolve the place.") from provider_errors[-1]
    raise BirthPlaceNotFoundError("Unable to locate that place.")


def geocode_birth_place(query: str, language: str = "en") -> BirthPlace:
    """Backward-compatible alias used by the natal-chart flow."""
    return geocode_place(query, language=language)


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


def format_natal_chart(chart: dict, language: str = "en") -> str:
    positions = chart["positions"]
    body_names = {
        "en": {"Sun":"Sun","Moon":"Moon","Mercury":"Mercury","Venus":"Venus","Mars":"Mars","Jupiter":"Jupiter","Saturn":"Saturn","Uranus":"Uranus","Neptune":"Neptune","Pluto":"Pluto","Ascendant":"Ascendant"},
        "pt": {"Sun":"Sol","Moon":"Lua","Mercury":"Mercúrio","Venus":"Vênus","Mars":"Marte","Jupiter":"Júpiter","Saturn":"Saturno","Uranus":"Urano","Neptune":"Netuno","Pluto":"Plutão","Ascendant":"Ascendente"},
        "es": {"Sun":"Sol","Moon":"Luna","Mercury":"Mercurio","Venus":"Venus","Mars":"Marte","Jupiter":"Júpiter","Saturn":"Saturno","Uranus":"Urano","Neptune":"Neptuno","Pluto":"Plutón","Ascendant":"Ascendente"},
    }.get(language, {})
    title = {
        "pt": "✨ Seu mapa natal básico é este:",
        "es": "✨ Tu carta natal básica es esta:",
    }.get(language, "✨ Your basic natal chart looks like this:")
    footer = {
        "pt": "Esses dados foram salvos no seu perfil e podem ser usados como contexto simbólico em leituras futuras.",
        "es": "Estos datos se guardaron en tu perfil y pueden usarse como contexto simbólico en futuras lecturas.",
    }.get(language, "These details are saved in your profile and can be used as symbolic context in future readings.")

    lines = [title, ""]
    for body in (
        "Sun", "Moon", "Mercury", "Venus", "Mars",
        "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
    ):
        position = positions[body]
        lines.append(f"{body_names.get(body, body)}: {position['sign']} {position['degree']:.2f}°")

    ascendant = chart["ascendant"]
    lines.extend([
        f"{body_names.get('Ascendant', 'Ascendant')}: {ascendant['sign']} {ascendant['degree']:.2f}°",
        "",
        footer,
    ])
    return "\n".join(lines)
