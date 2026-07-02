"""Today's weather via the Open-Meteo forecast API (no API key required)."""

import requests

WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Dense drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain",
    66: "Freezing rain", 67: "Heavy freezing rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Light showers", 81: "Showers", 82: "Violent showers",
    85: "Snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}


def fetch(config: dict) -> dict:
    loc = config["location"]
    unit = loc.get("temperature_unit", "fahrenheit")
    resp = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m",
            "daily": "temperature_2m_max,temperature_2m_min,weather_code,"
                     "precipitation_probability_max,sunrise,sunset",
            "temperature_unit": unit,
            "wind_speed_unit": "mph",
            "timezone": config["paper"].get("timezone", "auto"),
            "forecast_days": 3,
        },
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()

    current = data["current"]
    daily = data["daily"]
    deg = "°F" if unit == "fahrenheit" else "°C"

    days = []
    for i in range(len(daily["time"])):
        days.append({
            "date": daily["time"][i],
            "condition": WMO_CODES.get(daily["weather_code"][i], "Unknown"),
            "high": round(daily["temperature_2m_max"][i]),
            "low": round(daily["temperature_2m_min"][i]),
            "precip_chance": daily["precipitation_probability_max"][i],
        })

    return {
        "location": loc["name"],
        "unit": deg,
        "current_temp": round(current["temperature_2m"]),
        "feels_like": round(current["apparent_temperature"]),
        "condition": WMO_CODES.get(current["weather_code"], "Unknown"),
        "wind_mph": round(current["wind_speed_10m"]),
        "sunrise": daily["sunrise"][0].split("T")[1],
        "sunset": daily["sunset"][0].split("T")[1],
        "days": days,
    }
