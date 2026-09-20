"""
archive_light_mesh_snapshot_native Tool Plugin

Function: Archive a mesh-native light snapshot
Category: Action
Domain: IoT
"""

TOOL_NAME = "archive_light_mesh_snapshot_native"

from tools.plugins import create_document_and_alert_from_data as cdaafd


def execute(arguments, context) -> dict:
    mesh_snapshot = arguments.get("mesh_snapshot") or {}
    if not isinstance(mesh_snapshot, dict):
        return {"error": "mesh_snapshot must be an object"}

    result = cdaafd.execute(
        {
            "data": mesh_snapshot,
            "title": arguments.get("title") or "Light Snapshot",
            "tags": ["iot", "light", "mesh", "native"],
            "user_id": arguments.get("user_id") or "default_user",
            "priority": arguments.get("priority") or "medium",
            "channel": arguments.get("channel") or "app",
        },
        context,
    )
    if "error" in result:
        return result

    return {
        "status": "archived",
        "strategy": "mesh_light_archive_native",
        "notification_id": result.get("notification_id"),
        "note_id": result.get("note_id"),
        "title": result.get("title"),
        "light_ref": mesh_snapshot.get("mesh_node") or "mesh_light_snapshot",
    }
