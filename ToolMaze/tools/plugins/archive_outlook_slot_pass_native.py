"""
archive_outlook_slot_pass_native Tool Plugin

Function: Archive an Outlook-native slot pass
Category: Action
Domain: Office
"""

TOOL_NAME = "archive_outlook_slot_pass_native"

from tools.plugins import create_document_and_alert_from_data as cdaafd


def execute(arguments, context) -> dict:
    slot_pass = arguments.get("slot_pass") or {}
    if not isinstance(slot_pass, dict):
        return {"error": "slot_pass must be an object"}

    result = cdaafd.execute(
        {
            "data": slot_pass,
            "title": arguments.get("title") or "Outlook Slot Pass",
            "tags": ["availability", "outlook_calendar", "native"],
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
        "strategy": "outlook_slot_archive_native",
        "notification_id": result.get("notification_id"),
        "note_id": result.get("note_id"),
        "title": result.get("title"),
        "slot_ref": slot_pass.get("slot_pass_ref") or "outlook_slot_pass",
    }
