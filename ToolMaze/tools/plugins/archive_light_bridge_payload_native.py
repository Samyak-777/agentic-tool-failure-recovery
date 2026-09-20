"""
archive_light_bridge_payload_native Tool Plugin

Function: Archive a bridge-native light payload
Category: Action
Domain: IoT
"""

TOOL_NAME = "archive_light_bridge_payload_native"

from tools.plugins import create_document_and_alert_from_data as cdaafd


def execute(arguments, context) -> dict:
    bridge_payload = arguments.get("bridge_payload") or {}
    if not isinstance(bridge_payload, dict):
        return {"error": "bridge_payload must be an object"}

    result = cdaafd.execute(
        {
            "data": bridge_payload,
            "title": arguments.get("title") or "Light Payload",
            "tags": ["iot", "light", "bridge", "native"],
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
        "strategy": "bridge_light_archive_native",
        "notification_id": result.get("notification_id"),
        "note_id": result.get("note_id"),
        "title": result.get("title"),
        "light_ref": bridge_payload.get("bridge_light_id") or "bridge_light_payload",
    }
