"""
publish_utc_moment_card_native Tool Plugin

Function: Publish a time notice using a UTC-style moment card
Category: Action
Domain: General
"""

TOOL_NAME = "publish_utc_moment_card_native"

from tools.plugins import push_alert as pa


def execute(arguments, context) -> dict:
    moment_card = arguments.get("moment_card") or {}
    if not isinstance(moment_card, dict):
        return {"error": "moment_card must be an object"}

    message = f"{moment_card.get('tz_label', 'UTC')} {moment_card.get('clock_face', '00:00:00')}"
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
        "strategy": "utc_moment_notice_native",
        "notification_id": result.get("notification_id"),
        "target_user": user_id,
        "time_ref": moment_card.get("moment_card_id") or "utc_moment_card",
        "content": result.get("content", message),
    }
