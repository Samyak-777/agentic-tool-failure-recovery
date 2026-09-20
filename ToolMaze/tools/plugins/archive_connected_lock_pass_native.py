"""
archive_connected_lock_pass_native Tool Plugin

Function: Archive a connected-lock native pass
Category: Action
Domain: IoT
"""

TOOL_NAME = "archive_connected_lock_pass_native"

from tools.plugins import create_document_and_alert_from_data as cdaafd


def execute(arguments, context) -> dict:
    lock_pass = arguments.get("lock_pass") or {}
    if not isinstance(lock_pass, dict):
        return {"error": "lock_pass must be an object"}

    result = cdaafd.execute(
        {
            "data": lock_pass,
            "title": arguments.get("title") or "Connected Lock Pass",
            "tags": ["lock", "connected", "native"],
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
        "strategy": "connected_lock_archive_native",
        "notification_id": result.get("notification_id"),
        "note_id": result.get("note_id"),
        "title": result.get("title"),
        "lock_ref": lock_pass.get("lock_pass_ref") or "connected_lock_pass",
    }
