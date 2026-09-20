"""
get_light_mesh_snapshot_native Tool Plugin

Function: Retrieve a mesh-native smart-light snapshot
Category: Source
Domain: IoT
"""

TOOL_NAME = "get_light_mesh_snapshot_native"

from tools.plugins import get_light_status as gls

CONSTRAINTS = gls.CONSTRAINTS


def execute(arguments, context) -> dict:
    light_id = arguments.get("light_id")
    if not light_id:
        return {"error": "light_id is required"}

    light = gls.execute({"light_id": light_id}, context)
    if "error" in light:
        return light

    return {
        "mesh_node": light.get("device_id", light_id),
        "lamp_state": light.get("power_state"),
        "level_pct": light.get("brightness"),
        "hue_name": light.get("color"),
    }
