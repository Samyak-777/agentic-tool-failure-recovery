"""
publish_light_bridge_payload_native Tool Plugin

Function: Publish a bridge-native light payload summary
Category: Action
Domain: IoT
"""

TOOL_NAME = "publish_light_bridge_payload_native"

from tools.plugins import push_alert as pa


def execute(arguments, context) -> dict:
    bridge_payload = arguments.get("bridge_payload") or {}
    if not isinstance(bridge_payload, dict):
        return {"error": "bridge_payload must be an object"}

    light_id = bridge_payload.get("bridge_light_id") or "light_living"
    state = bridge_payload.get("bridge_state") or "unknown"
    level = bridge_payload.get("dimmer", 0)
    tone = bridge_payload.get("tone") or "default"
    message = f"Light {light_id}: {state}, {level}% ({tone})"
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
        "strategy": "bridge_light_notice_native",
        "notification_id": result.get("notification_id"),
        "target_user": user_id,
        "light_ref": bridge_payload.get("bridge_light_id") or "bridge_light_payload",
        "content": result.get("content", message),
    }
