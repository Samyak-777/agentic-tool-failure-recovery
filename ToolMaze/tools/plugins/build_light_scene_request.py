"""
build_light_scene_request Tool Plugin

Function: Build a normalized light-scene request from current device status
Category: Processor
Domain: IoT
"""

TOOL_NAME = "build_light_scene_request"


def execute(arguments, context) -> dict:
    del context

    device_status = arguments.get("device_status")
    if not isinstance(device_status, dict):
        return {"error": "device_status must be an object"}

    device_id = device_status.get("device_id")
    if not device_id:
        return {"error": "device_status.device_id is required"}

    brightness = arguments.get("brightness")
    try:
        brightness = int(brightness)
    except (TypeError, ValueError):
        return {"error": "brightness must be an integer"}
    if not (0 <= brightness <= 100):
        return {"error": "brightness must be between 0 and 100"}

    state = (arguments.get("state") or "on").lower()
    if state not in ["on", "off"]:
        return {"error": "state must be 'on' or 'off'"}

    color = arguments.get("color") or "white"

    return {
        "device_id": device_id,
        "state": state,
        "brightness": brightness,
        "color": str(color),
        "current_power_state": device_status.get("power_state"),
    }
