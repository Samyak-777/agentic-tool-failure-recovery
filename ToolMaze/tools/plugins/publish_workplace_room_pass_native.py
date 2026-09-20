"""
publish_workplace_room_pass_native Tool Plugin

Function: Publish a Workplace-native room pass summary
Category: Action
Domain: Office
"""

TOOL_NAME = "publish_workplace_room_pass_native"

from tools.plugins import push_alert as pa


def execute(arguments, context) -> dict:
    room_pass = arguments.get("room_pass") or {}
    if not isinstance(room_pass, dict):
        return {"error": "room_pass must be an object"}

    room_name = room_pass.get("room_name") or room_pass.get("resource_label") or "Meeting Room 1"
    date = room_pass.get("reserve_date") or "2026-01-16"
    start_time = room_pass.get("slot_begin") or "09:00"
    seats = room_pass.get("max_people", 0)
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
        "strategy": "workplace_room_notice_native",
        "notification_id": result.get("notification_id"),
        "target_user": user_id,
        "room_ref": room_pass.get("room_pass_ref") or "workplace_room_pass",
        "content": result.get("content", message),
    }
