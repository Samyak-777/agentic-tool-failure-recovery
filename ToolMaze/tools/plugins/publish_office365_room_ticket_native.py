"""
publish_office365_room_ticket_native Tool Plugin

Function: Publish an Office365-native room ticket summary
Category: Action
Domain: Office
"""

TOOL_NAME = "publish_office365_room_ticket_native"

from tools.plugins import push_alert as pa


def execute(arguments, context) -> dict:
    room_ticket = arguments.get("room_ticket") or {}
    if not isinstance(room_ticket, dict):
        return {"error": "room_ticket must be an object"}

    room_name = room_ticket.get("room_name") or "Meeting Room 1"
    date = room_ticket.get("booking_day") or "2026-01-16"
    start_time = room_ticket.get("slot_start") or "09:00"
    seats = room_ticket.get("seat_limit", 0)
    message = f"Room {room_name} available on {date} at {start_time} for {seats} seats"
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
        "strategy": "office365_room_notice_native",
        "notification_id": result.get("notification_id"),
        "target_user": user_id,
        "room_ref": room_ticket.get("room_ticket_id") or "office365_room_ticket",
        "content": result.get("content", message),
    }
