"""
build_power_restore_request Tool Plugin

Function: Build a normalized power-restore request for a selected device
Category: Processor
Domain: IoT
"""

TOOL_NAME = "build_power_restore_request"


def execute(arguments, context) -> dict:
    del context

    device_ref = arguments.get("device_ref")
    if not isinstance(device_ref, dict):
        return {"error": "device_ref must be an object"}

    device_id = device_ref.get("device_id")
    if not device_id:
        return {"error": "device_ref.device_id is required"}

    state = (arguments.get("state") or "on").lower()
    if state not in ["on", "off"]:
        return {"error": "state must be 'on' or 'off'"}

    return {
        "device_id": device_id,
        "state": state,
    }
