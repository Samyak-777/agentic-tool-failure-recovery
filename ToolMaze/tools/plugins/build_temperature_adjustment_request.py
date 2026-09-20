"""
build_temperature_adjustment_request Tool Plugin

Function: Build a normalized thermostat adjustment request from current device status
Category: Processor
Domain: IoT
"""

TOOL_NAME = "build_temperature_adjustment_request"

VALID_MODES = ["cool", "heat", "fan", "off", "auto", "eco"]


def execute(arguments, context) -> dict:
    del context

    device_status = arguments.get("device_status")
    if not isinstance(device_status, dict):
        return {"error": "device_status must be an object"}

    device_id = device_status.get("device_id")
    if not device_id:
        return {"error": "device_status.device_id is required"}

    temperature = arguments.get("temperature")
    try:
        temperature = float(temperature)
    except (TypeError, ValueError):
        return {"error": "temperature must be a number"}

    mode = (arguments.get("mode") or "cool").lower()
    if mode not in VALID_MODES:
        return {"error": f"mode must be one of {VALID_MODES}"}

    return {
        "device_id": device_id,
        "temperature": temperature,
        "mode": mode,
        "current_temperature": device_status.get("temperature"),
    }
