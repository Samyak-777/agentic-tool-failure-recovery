"""
publish_outlook_slot_pass_native Tool Plugin

Function: Publish a slot notice using an Outlook-native slot pass
Category: Action
Domain: Office
"""

TOOL_NAME = "publish_outlook_slot_pass_native"

from tools.plugins import push_alert as pa


def execute(arguments, context) -> dict:
    slot_pass = arguments.get("slot_pass") or {}
    if not isinstance(slot_pass, dict):
        return {"error": "slot_pass must be an object"}

    message = (
        f"Outlook slot {slot_pass.get('slot_day', '2024-10-24')} "
        f"{slot_pass.get('window_begin', '09:00')}-{slot_pass.get('window_end', '10:00')}"
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
        "strategy": "outlook_slot_notice_native",
        "notification_id": result.get("notification_id"),
        "target_user": user_id,
        "slot_ref": slot_pass.get("slot_pass_ref") or "outlook_slot_pass",
        "content": result.get("content", message),
    }
