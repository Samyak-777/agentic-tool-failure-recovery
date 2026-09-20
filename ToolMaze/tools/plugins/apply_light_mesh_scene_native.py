"""
apply_light_mesh_scene_native Tool Plugin

Function: Apply brightness using a mesh-native light snapshot
Category: Action
Domain: IoT
"""

TOOL_NAME = "apply_light_mesh_scene_native"

from tools.plugins import apply_light_brightness as alb


def execute(arguments, context) -> dict:
    mesh_snapshot = arguments.get("mesh_snapshot") or {}
    if not isinstance(mesh_snapshot, dict):
        return {"error": "mesh_snapshot must be an object"}

    light_id = mesh_snapshot.get("mesh_node") or "light_living"
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
        "strategy": "mesh_scene_native",
        "device_id": result.get("device_id", light_id),
        "brightness": result.get("brightness", brightness),
        "control_ref": mesh_snapshot.get("mesh_node") or "mesh_placeholder",
    }
