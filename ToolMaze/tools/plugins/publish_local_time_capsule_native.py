"""
publish_local_time_capsule_native Tool Plugin

Function: Publish a time notice using a local-time capsule
Category: Action
Domain: General
"""

TOOL_NAME = "publish_local_time_capsule_native"

from tools.plugins import push_alert as pa


def execute(arguments, context) -> dict:
    time_capsule = arguments.get("time_capsule") or {}
    if not isinstance(time_capsule, dict):
        return {"error": "time_capsule must be an object"}

    message = f"{time_capsule.get('timezone_key', 'local')} {time_capsule.get('local_clock', '00:00:00')}"
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
        "strategy": "local_capsule_notice_native",
        "notification_id": result.get("notification_id"),
        "target_user": user_id,
        "time_ref": time_capsule.get("capsule_ref") or "local_time_capsule",
        "content": result.get("content", message),
    }
