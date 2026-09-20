"""
archive_local_time_capsule_native Tool Plugin

Function: Archive a local-time native capsule
Category: Action
Domain: General
"""

TOOL_NAME = "archive_local_time_capsule_native"

from tools.plugins import create_document_and_alert_from_data as cdaafd


def execute(arguments, context) -> dict:
    time_capsule = arguments.get("time_capsule") or {}
    if not isinstance(time_capsule, dict):
        return {"error": "time_capsule must be an object"}

    result = cdaafd.execute(
        {
            "data": time_capsule,
            "title": arguments.get("title") or "Time Capsule",
            "tags": ["time", "local", "native"],
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
        "strategy": "local_capsule_archive_native",
        "notification_id": result.get("notification_id"),
        "note_id": result.get("note_id"),
        "title": result.get("title"),
        "time_ref": time_capsule.get("capsule_ref") or "local_capsule",
    }
