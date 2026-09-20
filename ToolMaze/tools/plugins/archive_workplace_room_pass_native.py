"""
archive_workplace_room_pass_native Tool Plugin

Function: Archive a Workplace-native room pass
Category: Action
Domain: Office
"""

TOOL_NAME = "archive_workplace_room_pass_native"

from tools.plugins import create_document_and_alert_from_data as cdaafd


def execute(arguments, context) -> dict:
    room_pass = arguments.get("room_pass") or {}
    if not isinstance(room_pass, dict):
        return {"error": "room_pass must be an object"}

    result = cdaafd.execute(
        {
            "data": room_pass,
            "title": arguments.get("title") or "Room Pass",
            "tags": ["room", "workplace", "native"],
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
        "strategy": "workplace_room_archive_native",
        "notification_id": result.get("notification_id"),
        "note_id": result.get("note_id"),
        "title": result.get("title"),
        "resource_ref": room_pass.get("room_pass_ref") or "workplace_room_pass",
    }
