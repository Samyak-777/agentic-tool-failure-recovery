"""
push_alert_to_contact Tool Plugin

Function: Send a push alert using resolved contact information
Category: Action
Domain: Office
"""

TOOL_NAME = "push_alert_to_contact"

from tools.plugins import push_alert as pa


def execute(arguments, context) -> dict:
    user_id = arguments.get("user_id")
    message = arguments.get("message")

    if not user_id:
        return {"error": "user_id is required"}
    if not message:
        return {"error": "message is required"}

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

    result["recipient_name"] = arguments.get("recipient_name") or ""
    result["status"] = "sent"
    return result
