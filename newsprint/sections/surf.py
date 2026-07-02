"""Surf report via the Open-Meteo Marine API (no API key required)."""

import requests

COMPASS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
           "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]


def _compass(degrees: float) -> str:
    return COMPASS[round(degrees / 22.5) % 16]


def _rating(height_ft: float, period_s: float) -> str:
    if height_ft < 1.5:
        return "Flat — sleep in"
    if height_ft < 3:
        return "Small but rideable" if period_s >= 10 else "Weak windswell"
    if height_ft < 5:
        return "Fun size" if period_s >= 11 else "Choppy but surfable"
    if height_ft < 8:
        return "Solid — bring the step-up"
    return "Pumping — experts only"


def fetch(config: dict) -> dict:
    cfg = config["sections"]["surf"]
    resp = requests.get(
        "https://marine-api.open-meteo.com/v1/marine",
        params={
            "latitude": cfg["latitude"],
            "longitude": cfg["longitude"],
            "current": "wave_height,wave_period,wave_direction,"
                       "swell_wave_height,swell_wave_period,swell_wave_direction",
            "daily": "wave_height_max,wave_period_max",
            "length_unit": "imperial",
            "timezone": config["paper"].get("timezone", "auto"),
            "forecast_days": 3,
        },
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()

    cur = data["current"]
    daily = data["daily"]
    height = cur["wave_height"]
    period = cur["wave_period"]

    days = []
    for i in range(len(daily["time"])):
        days.append({
            "date": daily["time"][i],
            "max_height_ft": round(daily["wave_height_max"][i], 1),
            "max_period_s": round(daily["wave_period_max"][i]),
        })

    return {
        "spot": cfg["spot_name"],
        "wave_height_ft": round(height, 1),
        "wave_period_s": round(period),
        "wave_direction": _compass(cur["wave_direction"]),
        "swell_height_ft": round(cur["swell_wave_height"], 1),
        "swell_period_s": round(cur["swell_wave_period"]),
        "swell_direction": _compass(cur["swell_wave_direction"]),
        "rating": _rating(height, period),
        "days": days,
    }
