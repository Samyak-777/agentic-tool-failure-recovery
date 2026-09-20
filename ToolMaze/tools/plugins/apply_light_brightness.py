"""
apply_light_brightness Tool Plugin

Function: Apply a normalized light-brightness request and return aligned output fields
Category: Action
Domain: IoT
"""

TOOL_NAME = "apply_light_brightness"

from tools.plugins import set_light_brightness as slb


def execute(arguments, context) -> dict:
    light_id = arguments.get("light_id")
    brightness = arguments.get("brightness")

    if not light_id:
        return {"error": "light_id is required"}
    if brightness is None:
        return {"error": "brightness is required"}

    result = slb.execute(
        {
            "light_id": light_id,
            "brightness": brightness,
        },
        context,
    )
    if "error" in result:
        return result

    return {
        "device_id": light_id,
        "status": "executed",
        "brightness": result.get("actual_brightness", brightness),
        "message": result.get("message", "Brightness adjusted"),
    }
