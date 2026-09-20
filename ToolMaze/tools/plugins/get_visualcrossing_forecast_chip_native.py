"""
get_visualcrossing_forecast_chip_native Tool Plugin

Function: Retrieve a Visual Crossing-native forecast chip
Category: Source
Domain: Travel
"""

TOOL_NAME = "get_visualcrossing_forecast_chip_native"

from tools.plugins import get_weather_visualcrossing as gwv


def execute(arguments, context) -> dict:
    weather = gwv.execute(arguments, context)
    if "error" in weather:
        return weather

    city = arguments.get("city") or "Tokyo"
    temperature = weather.get("temperature_celsius", 20)
    return {
        "forecast_chip_ref": f"vc_{str(city).lower().replace(' ', '_')}",
        "locality": city,
        "metric_temp": temperature,
        "conditions_brief": weather.get("condition") or "Clear",
        "advice_level": "watch" if temperature < 10 or temperature > 30 else "normal",
    }
