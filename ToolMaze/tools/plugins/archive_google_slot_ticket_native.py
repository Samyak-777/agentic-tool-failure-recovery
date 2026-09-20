"""
archive_google_slot_ticket_native Tool Plugin

Function: Archive a Google Calendar-native slot ticket
Category: Action
Domain: Office
"""

TOOL_NAME = "archive_google_slot_ticket_native"

from tools.plugins import create_document_and_alert_from_data as cdaafd


def execute(arguments, context) -> dict:
    slot_ticket = arguments.get("slot_ticket") or {}
    if not isinstance(slot_ticket, dict):
        return {"error": "slot_ticket must be an object"}

    result = cdaafd.execute(
        {
            "data": slot_ticket,
            "title": arguments.get("title") or "Google Slot Ticket",
            "tags": ["availability", "google_calendar", "native"],
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
        "strategy": "google_slot_archive_native",
        "notification_id": result.get("notification_id"),
        "note_id": result.get("note_id"),
        "title": result.get("title"),
        "slot_ref": slot_ticket.get("slot_ticket_id") or "google_slot_ticket",
    }
