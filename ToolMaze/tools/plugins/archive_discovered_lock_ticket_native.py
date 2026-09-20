"""
archive_discovered_lock_ticket_native Tool Plugin

Function: Archive a discovered-lock native ticket
Category: Action
Domain: IoT
"""

TOOL_NAME = "archive_discovered_lock_ticket_native"

from tools.plugins import create_document_and_alert_from_data as cdaafd


def execute(arguments, context) -> dict:
    lock_ticket = arguments.get("lock_ticket") or {}
    if not isinstance(lock_ticket, dict):
        return {"error": "lock_ticket must be an object"}

    result = cdaafd.execute(
        {
            "data": lock_ticket,
            "title": arguments.get("title") or "Discovered Lock Ticket",
            "tags": ["lock", "discovered", "native"],
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
        "strategy": "discovered_lock_archive_native",
        "notification_id": result.get("notification_id"),
        "note_id": result.get("note_id"),
        "title": result.get("title"),
        "lock_ref": lock_ticket.get("lock_ticket_id") or "discovered_lock_ticket",
    }
