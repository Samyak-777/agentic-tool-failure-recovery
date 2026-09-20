"""
publish_google_slot_ticket_native Tool Plugin

Function: Publish a slot notice using a Google Calendar-native slot ticket
Category: Action
Domain: Office
"""

TOOL_NAME = "publish_google_slot_ticket_native"

from tools.plugins import push_alert as pa


def execute(arguments, context) -> dict:
    slot_ticket = arguments.get("slot_ticket") or {}
    if not isinstance(slot_ticket, dict):
        return {"error": "slot_ticket must be an object"}

    message = (
        f"Google slot {slot_ticket.get('slot_date', '2024-10-24')} "
        f"{slot_ticket.get('slot_start', '09:00')}-{slot_ticket.get('slot_end', '10:00')}"
    )
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
        "strategy": "google_slot_notice_native",
        "notification_id": result.get("notification_id"),
        "target_user": user_id,
        "slot_ref": slot_ticket.get("slot_ticket_id") or "google_slot_ticket",
        "content": result.get("content", message),
    }
