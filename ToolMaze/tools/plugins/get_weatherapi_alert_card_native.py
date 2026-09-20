"""
get_weatherapi_alert_card_native Tool Plugin

Function: Retrieve a WeatherAPI-native alert card
Category: Source
Domain: Travel
"""

TOOL_NAME = "get_weatherapi_alert_card_native"

from tools.plugins import get_weather_weatherapi as gww


def execute(arguments, context) -> dict:
    weather = gww.execute(arguments, context)
    if "error" in weather:
        return weather

    city = arguments.get("city") or "Tokyo"
    temperature = weather.get("temperature_celsius", 20)
    return {
        "alert_card_id": f"wapi_{str(city).lower().replace(' ', '_')}",
        "city_label": city,
        "celsius_now": temperature,
        "sky_text": weather.get("condition") or "Clear",
        "advice_level": "watch" if temperature < 10 or temperature > 30 else "normal",
    }
