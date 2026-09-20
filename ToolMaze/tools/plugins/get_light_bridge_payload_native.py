"""
get_light_bridge_payload_native Tool Plugin

Function: Retrieve a bridge-native smart-light payload
Category: Source
Domain: IoT
"""

TOOL_NAME = "get_light_bridge_payload_native"

from tools.plugins import get_iot_device_status as gids

CONSTRAINTS = {
    "device_id": ["light_living", "light_bedroom"],
}


def execute(arguments, context) -> dict:
    device_id = arguments.get("device_id")
    if not device_id:
        return {"error": "device_id is required"}

    light = gids.execute({"device_id": device_id}, context)
    if "error" in light:
        return light

    return {
        "bridge_light_id": light.get("device_id", device_id),
        "bridge_state": light.get("power_state"),
        "dimmer": light.get("brightness"),
        "tone": light.get("color"),
    }
