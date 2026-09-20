"""
archive_office365_room_ticket_native Tool Plugin

Function: Archive an Office365-native room ticket
Category: Action
Domain: Office
"""

TOOL_NAME = "archive_office365_room_ticket_native"

from tools.plugins import create_document_and_alert_from_data as cdaafd


def execute(arguments, context) -> dict:
    room_ticket = arguments.get("room_ticket") or {}
    if not isinstance(room_ticket, dict):
        return {"error": "room_ticket must be an object"}

    result = cdaafd.execute(
        {
            "data": room_ticket,
            "title": arguments.get("title") or "Room Ticket",
            "tags": ["room", "office365", "native"],
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
        "strategy": "office365_room_archive_native",
        "notification_id": result.get("notification_id"),
        "note_id": result.get("note_id"),
        "title": result.get("title"),
        "resource_ref": room_ticket.get("room_ticket_id") or "o365_room_ticket",
    }
