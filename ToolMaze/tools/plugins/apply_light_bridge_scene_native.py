"""
apply_light_bridge_scene_native Tool Plugin

Function: Apply brightness using a bridge-native light payload
Category: Action
Domain: IoT
"""

TOOL_NAME = "apply_light_bridge_scene_native"

from tools.plugins import apply_light_brightness as alb


def execute(arguments, context) -> dict:
    bridge_payload = arguments.get("bridge_payload") or {}
    if not isinstance(bridge_payload, dict):
        return {"error": "bridge_payload must be an object"}

    light_id = bridge_payload.get("bridge_light_id") or "light_living"
    brightness = arguments.get("brightness")
    if brightness is None:
        return {"error": "brightness is required"}

    result = alb.execute(
        {
            "light_id": light_id,
            "brightness": brightness,
        },
        context,
    )
    if "error" in result:
        return result

    return {
        "status": result.get("status", "executed"),
        "strategy": "bridge_scene_native",
        "device_id": result.get("device_id", light_id),
        "brightness": result.get("brightness", brightness),
        "control_ref": bridge_payload.get("bridge_light_id") or "bridge_placeholder",
    }
