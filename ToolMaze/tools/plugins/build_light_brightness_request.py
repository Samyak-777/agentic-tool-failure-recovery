"""
build_light_brightness_request Tool Plugin

Function: Build a normalized light-brightness request from current light status
Category: Processor
Domain: IoT
"""

TOOL_NAME = "build_light_brightness_request"


def execute(arguments, context) -> dict:
    del context

    light_status = arguments.get("light_status")
    if not isinstance(light_status, dict):
        return {"error": "light_status must be an object"}

    light_id = light_status.get("device_id")
    if not light_id:
        return {"error": "light_status.device_id is required"}

    brightness = arguments.get("brightness")
    try:
        brightness = int(brightness)
    except (TypeError, ValueError):
        return {"error": "brightness must be an integer"}
    if not (0 <= brightness <= 100):
        return {"error": "brightness must be between 0 and 100"}

    return {
        "light_id": light_id,
        "brightness": brightness,
        "current_power_state": light_status.get("power_state"),
    }
