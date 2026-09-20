"""
publish_light_mesh_snapshot_native Tool Plugin

Function: Publish a mesh-native light snapshot summary
Category: Action
Domain: IoT
"""

TOOL_NAME = "publish_light_mesh_snapshot_native"

from tools.plugins import push_alert as pa


def execute(arguments, context) -> dict:
    mesh_snapshot = arguments.get("mesh_snapshot") or {}
    if not isinstance(mesh_snapshot, dict):
        return {"error": "mesh_snapshot must be an object"}

    light_id = mesh_snapshot.get("mesh_node") or "light_living"
    state = mesh_snapshot.get("lamp_state") or "unknown"
    level = mesh_snapshot.get("level_pct", 0)
    hue = mesh_snapshot.get("hue_name") or "default"
    message = f"Light {light_id}: {state}, {level}% ({hue})"
    user_id = arguments.get("user_id") or "default_user"

    result = pa.execute(
        {
            "message": message,
            "user_id": user_id,
            "priority": arguments.get("priority") or "medium",
            "channel": arguments.get("channel") or "app",
        },
        context,
    )
    if "error" in result:
        return result

    return {
        "status": "published",
        "strategy": "mesh_light_notice_native",
        "notification_id": result.get("notification_id"),
        "target_user": user_id,
        "light_ref": mesh_snapshot.get("mesh_node") or "mesh_light_snapshot",
        "content": result.get("content", message),
    }
